#!/usr/bin/env python3
"""
Extract Firebird DDL Schema for WINCASA Database
This script extracts the complete schema including tables, columns, and relationships
to fix the critical issue where LLM generates wrong table/field names.
"""

import os
import sys
import json
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wincasa.data.db_singleton import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_tables_schema():
    """Extract all tables and their columns from Firebird system tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query to get all user tables and their columns
    query = """
    SELECT 
        rf.RDB$RELATION_NAME as TABLE_NAME,
        rf.RDB$FIELD_NAME as COLUMN_NAME,
        f.RDB$FIELD_TYPE as FIELD_TYPE,
        f.RDB$FIELD_LENGTH as FIELD_LENGTH,
        f.RDB$FIELD_SCALE as FIELD_SCALE,
        f.RDB$FIELD_SUB_TYPE as FIELD_SUB_TYPE,
        rf.RDB$NULL_FLAG as NOT_NULL,
        rf.RDB$DESCRIPTION as FIELD_DESCRIPTION
    FROM RDB$RELATION_FIELDS rf
    LEFT JOIN RDB$FIELDS f ON rf.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
    WHERE rf.RDB$RELATION_NAME NOT STARTING WITH 'RDB$'
    AND rf.RDB$RELATION_NAME NOT STARTING WITH 'MON$'
    ORDER BY rf.RDB$RELATION_NAME, rf.RDB$FIELD_POSITION
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Group by table
    tables = {}
    for row in results:
        table_name = row[0].strip() if row[0] else None
        if not table_name:
            continue
            
        if table_name not in tables:
            tables[table_name] = {
                'name': table_name,
                'columns': []
            }
        
        column_info = {
            'name': row[1].strip() if row[1] else '',
            'type': get_field_type_name(row[2], row[5], row[4]),
            'length': row[3],
            'scale': row[4],
            'nullable': not bool(row[6]),
            'description': row[7].strip() if row[7] else None
        }
        
        tables[table_name]['columns'].append(column_info)
    
    cursor.close()
    return tables

def get_field_type_name(field_type, sub_type, scale):
    """Convert Firebird numeric field types to readable names"""
    type_map = {
        7: 'SMALLINT',
        8: 'INTEGER',
        9: 'QUAD',
        10: 'FLOAT',
        11: 'D_FLOAT',
        12: 'DATE',
        13: 'TIME',
        14: 'CHAR',
        16: 'BIGINT',
        27: 'DOUBLE',
        35: 'TIMESTAMP',
        37: 'VARCHAR',
        40: 'CSTRING',
        261: 'BLOB'
    }
    
    base_type = type_map.get(field_type, f'UNKNOWN({field_type})')
    
    # Handle numeric types with scale
    if field_type in [7, 8, 16, 27] and scale and scale < 0:
        return f'NUMERIC({abs(scale)})'
    
    # Handle BLOB subtypes
    if field_type == 261:
        if sub_type == 1:
            return 'BLOB SUB_TYPE TEXT'
        else:
            return 'BLOB SUB_TYPE BINARY'
    
    return base_type

def extract_primary_keys():
    """Extract primary key information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        rc.RDB$RELATION_NAME as TABLE_NAME,
        seg.RDB$FIELD_NAME as COLUMN_NAME
    FROM RDB$RELATION_CONSTRAINTS rc
    JOIN RDB$INDEX_SEGMENTS seg ON rc.RDB$INDEX_NAME = seg.RDB$INDEX_NAME
    WHERE rc.RDB$CONSTRAINT_TYPE = 'PRIMARY KEY'
    ORDER BY rc.RDB$RELATION_NAME, seg.RDB$FIELD_POSITION
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Group by table
    primary_keys = {}
    for row in results:
        table_name = row[0].strip() if row[0] else None
        column_name = row[1].strip() if row[1] else None
        
        if table_name and column_name:
            if table_name not in primary_keys:
                primary_keys[table_name] = []
            primary_keys[table_name].append(column_name)
    
    cursor.close()
    return primary_keys

def extract_foreign_keys():
    """Extract foreign key relationships"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        rc.RDB$RELATION_NAME as TABLE_NAME,
        seg.RDB$FIELD_NAME as COLUMN_NAME,
        rc2.RDB$RELATION_NAME as REFERENCED_TABLE,
        seg2.RDB$FIELD_NAME as REFERENCED_COLUMN,
        rc.RDB$CONSTRAINT_NAME as CONSTRAINT_NAME
    FROM RDB$RELATION_CONSTRAINTS rc
    JOIN RDB$INDEX_SEGMENTS seg ON rc.RDB$INDEX_NAME = seg.RDB$INDEX_NAME
    JOIN RDB$REF_CONSTRAINTS ref ON rc.RDB$CONSTRAINT_NAME = ref.RDB$CONSTRAINT_NAME
    JOIN RDB$RELATION_CONSTRAINTS rc2 ON ref.RDB$CONST_NAME_UQ = rc2.RDB$CONSTRAINT_NAME
    JOIN RDB$INDEX_SEGMENTS seg2 ON rc2.RDB$INDEX_NAME = seg2.RDB$INDEX_NAME
    WHERE rc.RDB$CONSTRAINT_TYPE = 'FOREIGN KEY'
    AND seg.RDB$FIELD_POSITION = seg2.RDB$FIELD_POSITION
    ORDER BY rc.RDB$RELATION_NAME, seg.RDB$FIELD_POSITION
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    foreign_keys = []
    for row in results:
        fk_info = {
            'table': row[0].strip() if row[0] else '',
            'column': row[1].strip() if row[1] else '',
            'referenced_table': row[2].strip() if row[2] else '',
            'referenced_column': row[3].strip() if row[3] else '',
            'constraint_name': row[4].strip() if row[4] else ''
        }
        foreign_keys.append(fk_info)
    
    cursor.close()
    return foreign_keys

def create_ddl_from_schema(tables, primary_keys, foreign_keys):
    """Generate DDL CREATE statements from schema information"""
    ddl_statements = []
    
    for table_name, table_info in sorted(tables.items()):
        ddl = f"CREATE TABLE {table_name} (\n"
        
        # Add columns
        column_defs = []
        for col in table_info['columns']:
            col_def = f"    {col['name']} {col['type']}"
            
            # Add length for VARCHAR/CHAR
            if col['type'] in ['VARCHAR', 'CHAR'] and col['length']:
                col_def += f"({col['length']})"
            
            # Add NOT NULL constraint
            if not col['nullable']:
                col_def += " NOT NULL"
            
            column_defs.append(col_def)
        
        # Add primary key constraint
        if table_name in primary_keys:
            pk_cols = ', '.join(primary_keys[table_name])
            column_defs.append(f"    CONSTRAINT PK_{table_name} PRIMARY KEY ({pk_cols})")
        
        ddl += ',\n'.join(column_defs)
        ddl += "\n);"
        
        ddl_statements.append(ddl)
    
    # Add foreign key constraints
    for fk in foreign_keys:
        fk_ddl = f"""
ALTER TABLE {fk['table']} 
ADD CONSTRAINT {fk['constraint_name']} 
FOREIGN KEY ({fk['column']}) 
REFERENCES {fk['referenced_table']}({fk['referenced_column']});"""
        ddl_statements.append(fk_ddl)
    
    return '\n\n'.join(ddl_statements)

def save_schema_documentation(tables, primary_keys, foreign_keys):
    """Save schema documentation in multiple formats"""
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'schema')
    os.makedirs(output_dir, exist_ok=True)
    
    # Save JSON format
    schema_json = {
        'extraction_date': datetime.now().isoformat(),
        'tables': tables,
        'primary_keys': primary_keys,
        'foreign_keys': foreign_keys
    }
    
    with open(os.path.join(output_dir, 'firebird_schema.json'), 'w') as f:
        json.dump(schema_json, f, indent=2)
    
    # Save DDL format
    ddl_content = create_ddl_from_schema(tables, primary_keys, foreign_keys)
    with open(os.path.join(output_dir, 'firebird_schema.sql'), 'w') as f:
        f.write(ddl_content)
    
    # Save human-readable documentation
    doc_content = f"""# WINCASA Firebird Database Schema
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
Total Tables: {len(tables)}
Total Relationships: {len(foreign_keys)}

## Critical Tables for Property Management

### EIGADR (Eigentümer/Owners)
Primary table for property owners.
Key fields:
- ONR: Owner number (PRIMARY KEY)
- ONAME: Owner name
- OSTRASSE: Street address
- OPLZORT: Postal code and city

### BEWOHNER (Mieter/Tenants)
Primary table for tenants.
Key fields:
- MIETERNR: Tenant number (PRIMARY KEY)
- MNRNEU: New tenant number
- BNAME: Tenant name
- BSTRASSE: Street address
- BPLZORT: Postal code and city
- Z1: KALTMIETE (Cold rent) - CRITICAL FIELD!

### OBJEKTE (Properties/Buildings)
Primary table for properties.
Key fields:
- OBJNR: Property number (PRIMARY KEY)
- OBJNAME: Property name
- OBJPLZORT: Property location

### WOHNUNGEN (Apartments)
Primary table for apartment units.
Key fields:
- WOBJNR: Property number (FOREIGN KEY to OBJEKTE)
- WHGNR: Apartment number
- WBEZ: Apartment designation

## Common Query Patterns

1. Get all tenants:
   SELECT * FROM BEWOHNER WHERE EIGNR > -1

2. Get vacant apartments (Leerstand):
   SELECT * FROM BEWOHNER WHERE EIGNR = -1

3. Get owner portfolio:
   SELECT * FROM EIGADR WHERE ONR >= 890

4. Get Kaltmiete (cold rent):
   SELECT BNAME, Z1 as KALTMIETE FROM BEWOHNER

## Field Name Mappings (German → SQL)

- Eigentümer → EIGADR table
- Mieter → BEWOHNER table
- Objekte → OBJEKTE table
- Wohnungen → WOHNUNGEN table
- Kaltmiete → BEWOHNER.Z1
- Strasse → OSTRASSE (owners) or BSTRASSE (tenants)
- Name → ONAME (owners) or BNAME (tenants)
- Stadt/Ort → OPLZORT (owners) or BPLZORT (tenants)

## Complete Table List
"""
    
    for table_name in sorted(tables.keys()):
        doc_content += f"\n### {table_name}\n"
        table_info = tables[table_name]
        for col in table_info['columns'][:10]:  # Show first 10 columns
            doc_content += f"- {col['name']}: {col['type']}"
            if not col['nullable']:
                doc_content += " NOT NULL"
            doc_content += "\n"
        if len(table_info['columns']) > 10:
            doc_content += f"... and {len(table_info['columns']) - 10} more columns\n"
    
    with open(os.path.join(output_dir, 'firebird_schema.md'), 'w') as f:
        f.write(doc_content)
    
    logger.info(f"Schema documentation saved to {output_dir}")
    return output_dir

def main():
    """Main function to extract and document Firebird schema"""
    logger.info("Starting Firebird schema extraction...")
    
    try:
        # Extract schema information
        tables = extract_tables_schema()
        logger.info(f"Extracted {len(tables)} tables")
        
        primary_keys = extract_primary_keys()
        logger.info(f"Extracted primary keys for {len(primary_keys)} tables")
        
        foreign_keys = extract_foreign_keys()
        logger.info(f"Extracted {len(foreign_keys)} foreign key relationships")
        
        # Save documentation
        output_dir = save_schema_documentation(tables, primary_keys, foreign_keys)
        
        # Print summary of critical tables
        print("\n" + "="*60)
        print("CRITICAL SCHEMA INFORMATION FOR LLM SYSTEM PROMPTS")
        print("="*60)
        print("\nKey Tables (CORRECT NAMES):")
        print("- EIGADR (NOT 'OWNERS') - Property owners table")
        print("- BEWOHNER (NOT 'TENANTS') - Tenants table")
        print("- OBJEKTE - Properties table")
        print("- WOHNUNGEN - Apartments table")
        print("\nKey Fields (CORRECT NAMES):")
        print("- BEWOHNER.Z1 (NOT 'KALTMIETE' field) - Cold rent amount")
        print("- BSTRASSE/OSTRASSE (NOT 'STRASSE') - Street address")
        print("- BNAME/ONAME (NOT 'BEWNAME') - Name fields")
        print("- BPLZORT/OPLZORT (NOT 'STADT') - City/location fields")
        print("\n" + "="*60)
        
        print(f"\nSchema documentation saved to: {output_dir}")
        print("\nNext steps:")
        print("1. Update VERSION_*.md files with this schema")
        print("2. Fix knowledge base mappings")
        print("3. Test all query modes")
        
    except Exception as e:
        logger.error(f"Failed to extract schema: {e}")
        raise

if __name__ == "__main__":
    main()