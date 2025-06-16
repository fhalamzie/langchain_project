#!/usr/bin/env python3
"""
Simple Firebird DDL Schema Extractor for WINCASA Database
Extracts schema in one connection to avoid connection issues
"""

import os
import sys
import json
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wincasa.data.db_singleton import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_complete_schema():
    """Extract all schema information in a single connection"""
    
    # Get all tables and columns
    tables_query = """
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
    
    results = execute_query(tables_query)
    
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

def save_critical_schema_info(tables):
    """Save the critical schema information for LLM system prompts"""
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'schema')
    os.makedirs(output_dir, exist_ok=True)
    
    # Focus on critical tables for property management
    critical_tables = ['EIGADR', 'BEWOHNER', 'OBJEKTE', 'WOHNUNGEN', 'KONTEN', 'BUCHUNGEN']
    
    # Create a simplified schema for LLM
    llm_schema = {
        'extraction_date': datetime.now().isoformat(),
        'critical_info': {
            'EIGADR': {
                'description': 'Property owners table (NOT OWNERS)',
                'key_fields': {
                    'ONR': 'Owner number (PRIMARY KEY)',
                    'ONAME': 'Owner name',
                    'OSTRASSE': 'Street address (NOT STRASSE)',
                    'OPLZORT': 'Postal code and city (NOT STADT)'
                }
            },
            'BEWOHNER': {
                'description': 'Tenants table (NOT TENANTS)',
                'key_fields': {
                    'MIETERNR': 'Tenant number (PRIMARY KEY)',
                    'BNAME': 'Tenant name (NOT BEWNAME)',
                    'BSTRASSE': 'Street address (NOT STRASSE)',
                    'BPLZORT': 'Postal code and city (NOT STADT)',
                    'Z1': 'KALTMIETE - Cold rent amount (CRITICAL!)',
                    'EIGNR': 'Owner reference (-1 = vacant)'
                }
            },
            'OBJEKTE': {
                'description': 'Properties/Buildings table',
                'key_fields': {
                    'OBJNR': 'Property number (PRIMARY KEY)',
                    'OBJNAME': 'Property name',
                    'OBJPLZORT': 'Property location'
                }
            },
            'WOHNUNGEN': {
                'description': 'Apartments/Units table',
                'key_fields': {
                    'WOBJNR': 'Property number (FOREIGN KEY to OBJEKTE)',
                    'WHGNR': 'Apartment number',
                    'WBEZ': 'Apartment designation'
                }
            }
        },
        'common_mistakes': {
            'WRONG': ['OWNERS', 'TENANTS', 'STRASSE', 'BEWNAME', 'STADT', 'KALTMIETE as field name'],
            'CORRECT': ['EIGADR', 'BEWOHNER', 'OSTRASSE/BSTRASSE', 'BNAME', 'OPLZORT/BPLZORT', 'Z1 as KALTMIETE']
        }
    }
    
    # Save LLM-focused schema
    with open(os.path.join(output_dir, 'llm_critical_schema.json'), 'w') as f:
        json.dump(llm_schema, f, indent=2)
    
    # Save complete tables info
    with open(os.path.join(output_dir, 'complete_tables.json'), 'w') as f:
        json.dump(tables, f, indent=2)
    
    # Create SQL examples for system prompts
    sql_examples = """-- CORRECT SQL Examples for WINCASA Database

-- Get all tenants (NOT FROM 'TENANTS' table!)
SELECT MIETERNR, BNAME, BSTRASSE, BPLZORT, Z1 as KALTMIETE 
FROM BEWOHNER 
WHERE EIGNR > -1;

-- Get all owners (NOT FROM 'OWNERS' table!)
SELECT ONR, ONAME, OSTRASSE, OPLZORT 
FROM EIGADR 
WHERE ONR >= 890;

-- Get vacant apartments
SELECT * FROM BEWOHNER WHERE EIGNR = -1;

-- Get properties
SELECT OBJNR, OBJNAME, OBJPLZORT FROM OBJEKTE;

-- Get apartments with property info
SELECT w.WHGNR, w.WBEZ, o.OBJNAME 
FROM WOHNUNGEN w
JOIN OBJEKTE o ON w.WOBJNR = o.OBJNR;

-- Calculate total Kaltmiete (cold rent)
SELECT SUM(Z1) as TOTAL_KALTMIETE FROM BEWOHNER WHERE EIGNR > -1;
"""
    
    with open(os.path.join(output_dir, 'correct_sql_examples.sql'), 'w') as f:
        f.write(sql_examples)
    
    logger.info(f"Critical schema information saved to {output_dir}")
    
    # Print summary
    print("\n" + "="*80)
    print("CRITICAL WINCASA SCHEMA EXTRACTED SUCCESSFULLY")
    print("="*80)
    print("\nTables found:", len(tables))
    print("\nCRITICAL CORRECTIONS NEEDED:")
    print("1. EIGADR table (NOT 'OWNERS')")
    print("2. BEWOHNER table (NOT 'TENANTS')")
    print("3. BEWOHNER.Z1 = KALTMIETE (NOT a field named 'KALTMIETE')")
    print("4. BSTRASSE/OSTRASSE (NOT 'STRASSE')")
    print("5. BNAME/ONAME (NOT 'BEWNAME')")
    print("6. BPLZORT/OPLZORT (NOT 'STADT')")
    print("\nFiles created in data/schema/:")
    print("- llm_critical_schema.json")
    print("- complete_tables.json")
    print("- correct_sql_examples.sql")
    print("="*80)
    
    return output_dir

def main():
    """Main function"""
    logger.info("Starting simplified Firebird schema extraction...")
    
    try:
        tables = extract_complete_schema()
        logger.info(f"Extracted {len(tables)} tables")
        
        output_dir = save_critical_schema_info(tables)
        
        print(f"\nNext step: Update VERSION_*.md files in src/wincasa/utils/")
        
    except Exception as e:
        logger.error(f"Failed to extract schema: {e}")
        raise

if __name__ == "__main__":
    main()