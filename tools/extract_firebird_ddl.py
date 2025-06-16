#!/usr/bin/env python3
"""
Extract Firebird DDL Schema from WINCASA Database
Generates complete schema documentation for System Prompts
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from wincasa.data.json_exporter import get_connection
import json

def extract_table_ddl(conn, table_name):
    """Extract DDL for a single table including columns"""
    cursor = conn.cursor()
    
    # Get column information
    query = """
    SELECT 
        rf.RDB$FIELD_NAME as FIELD_NAME,
        f.RDB$FIELD_TYPE as FIELD_TYPE,
        f.RDB$FIELD_LENGTH as FIELD_LENGTH,
        f.RDB$FIELD_LENGTH as CHAR_LENGTH,
        f.RDB$FIELD_PRECISION as FIELD_PRECISION,
        f.RDB$FIELD_SCALE as FIELD_SCALE,
        rf.RDB$NULL_FLAG as NOT_NULL,
        rf.RDB$DEFAULT_SOURCE as DEFAULT_VALUE,
        rf.RDB$DESCRIPTION as DESCRIPTION
    FROM RDB$RELATION_FIELDS rf
    JOIN RDB$FIELDS f ON rf.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
    WHERE rf.RDB$RELATION_NAME = ?
    ORDER BY rf.RDB$FIELD_POSITION
    """
    
    cursor.execute(query, (table_name,))
    columns = cursor.fetchall()
    cursor.close()
    
    # Map Firebird types to SQL standard
    type_map = {
        7: 'SMALLINT',
        8: 'INTEGER', 
        9: 'QUAD',
        10: 'FLOAT',
        12: 'DATE',
        13: 'TIME',
        14: 'CHAR',
        16: 'BIGINT',
        27: 'DOUBLE PRECISION',
        35: 'TIMESTAMP',
        37: 'VARCHAR',
        40: 'CSTRING',
        261: 'BLOB'
    }
    
    ddl_lines = [f"CREATE TABLE {table_name.strip()} ("]
    
    for i, col in enumerate(columns):
        field_name = col[0].strip()
        field_type = col[1]
        field_length = col[2]
        char_length = col[3]
        precision = col[4]
        scale = col[5]
        not_null = col[6]
        default_val = col[7]
        description = col[8]
        
        # Build data type
        data_type = type_map.get(field_type, f'UNKNOWN({field_type})')
        
        if field_type in [14, 37]:  # CHAR, VARCHAR
            length = char_length if char_length else field_length
            data_type = f"{data_type}({length})"
        elif field_type == 16 and precision:  # NUMERIC/DECIMAL
            if scale and scale < 0:
                data_type = f"NUMERIC({precision},{abs(scale)})"
            else:
                data_type = f"NUMERIC({precision})"
        
        # Build column definition
        col_def = f"    {field_name} {data_type}"
        
        if not_null:
            col_def += " NOT NULL"
            
        if default_val:
            col_def += f" {default_val.strip()}"
            
        # Add comma except for last column
        if i < len(columns) - 1:
            col_def += ","
            
        # Add description as comment
        if description:
            col_def += f"  -- {description.strip()}"
            
        ddl_lines.append(col_def)
    
    ddl_lines.append(");")
    
    return "\n".join(ddl_lines)

def extract_all_tables_ddl():
    """Extract DDL for all user tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all user tables (exclude system tables)
    query = """
    SELECT DISTINCT RDB$RELATION_NAME 
    FROM RDB$RELATIONS 
    WHERE RDB$SYSTEM_FLAG = 0
    AND RDB$RELATION_TYPE = 0
    ORDER BY RDB$RELATION_NAME
    """
    
    cursor.execute(query)
    tables = cursor.fetchall()
    cursor.close()
    
    print(f"Found {len(tables)} tables in WINCASA database")
    
    all_ddl = []
    table_info = {}
    
    for table in tables:
        table_name = table[0].strip()
        print(f"Extracting DDL for table: {table_name}")
        
        try:
            ddl = extract_table_ddl(conn, table[0])
            all_ddl.append(f"-- Table: {table_name}")
            all_ddl.append(ddl)
            all_ddl.append("")  # Empty line between tables
            
            # Also collect simplified info for JSON
            cursor2 = conn.cursor()
            cursor2.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor2.fetchone()[0]
            cursor2.close()
            
            table_info[table_name] = {
                "row_count": row_count,
                "ddl": ddl
            }
            
        except Exception as e:
            print(f"Error extracting DDL for {table_name}: {e}")
    
    conn.close()
    
    # Save complete DDL
    ddl_content = "\n".join(all_ddl)
    with open('data/knowledge/wincasa_firebird_schema.sql', 'w', encoding='utf-8') as f:
        f.write("-- WINCASA Firebird Database Schema\n")
        f.write("-- Extracted from actual database\n")
        f.write("-- This is the REAL schema that must be used for SQL generation\n\n")
        f.write(ddl_content)
    
    # Save table info as JSON
    with open('data/knowledge/wincasa_tables_info.json', 'w', encoding='utf-8') as f:
        json.dump(table_info, f, indent=2, ensure_ascii=False)
    
    print(f"\nDDL saved to: data/knowledge/wincasa_firebird_schema.sql")
    print(f"Table info saved to: data/knowledge/wincasa_tables_info.json")
    
    # Print summary of important tables
    print("\n=== Important Tables for Property Management ===")
    important_tables = ['BEWOHNER', 'BEWADR', 'EIGADR', 'OBJEKTE', 'WOHNUNG', 'KONTEN']
    
    for table in important_tables:
        if table in table_info:
            print(f"\n{table}: {table_info[table]['row_count']} rows")
            # Show first few columns
            lines = table_info[table]['ddl'].split('\n')[1:6]  # Skip CREATE TABLE line
            for line in lines:
                if line.strip() and not line.startswith(');'):
                    print(f"  {line.strip()}")

if __name__ == "__main__":
    extract_all_tables_ddl()