#!/usr/bin/env python3
"""
Extract Schema Information from SQL Query Files
Analyzes the 35 SQL queries to understand the real table structure
"""

import os
import re
import json
from collections import defaultdict

def extract_tables_and_fields():
    """Extract table and field information from SQL queries"""
    
    sql_dir = "data/sql"
    tables = defaultdict(set)
    table_aliases = {}
    table_descriptions = {}
    
    # Process each SQL file
    for filename in sorted(os.listdir(sql_dir)):
        if filename.endswith('.sql'):
            filepath = os.path.join(sql_dir, filename)
            print(f"Analyzing {filename}...")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extract FROM clauses to identify tables
                from_pattern = r'FROM\s+(\w+)\s+(\w+)?'
                from_matches = re.finditer(from_pattern, content, re.IGNORECASE)
                
                for match in from_matches:
                    table_name = match.group(1)
                    alias = match.group(2) if match.group(2) else table_name
                    table_aliases[alias] = table_name
                
                # Extract JOIN clauses
                join_pattern = r'JOIN\s+(\w+)\s+(\w+)?'
                join_matches = re.finditer(join_pattern, content, re.IGNORECASE)
                
                for match in join_matches:
                    table_name = match.group(1)
                    alias = match.group(2) if match.group(2) else table_name
                    table_aliases[alias] = table_name
                
                # Extract field references (alias.field)
                field_pattern = r'(\w+)\.(\w+)'
                field_matches = re.finditer(field_pattern, content)
                
                for match in field_matches:
                    alias = match.group(1)
                    field = match.group(2)
                    
                    # Map alias to table name
                    if alias in table_aliases:
                        table_name = table_aliases[alias]
                        tables[table_name].add(field)
                
                # Extract comments about tables
                comment_pattern = r'--\s*(.+)'
                comments = re.findall(comment_pattern, content)
                for comment in comments:
                    if 'HAUPTTABELLEN:' in comment:
                        # Extract table descriptions
                        idx = comments.index(comment)
                        for i in range(idx + 1, min(idx + 10, len(comments))):
                            if comments[i].strip().startswith('-'):
                                desc_match = re.match(r'-\s*(\w+):\s*(.+)', comments[i])
                                if desc_match:
                                    table_descriptions[desc_match.group(1)] = desc_match.group(2)
    
    return tables, table_descriptions

def create_ddl_from_analysis():
    """Create DDL statements based on extracted information"""
    
    tables, descriptions = extract_tables_and_fields()
    
    # Core tables based on frequency and importance
    core_tables = {
        'BEWOHNER': 'Mieterstammdaten - Zentrale Tabelle für alle Mieterinformationen',
        'BEWADR': 'Mieter-Adressdaten - Zusätzliche Adressinformationen für Mieter',
        'EIGADR': 'Eigentümerstammdaten - Zentrale Tabelle für alle Eigentümerinformationen',
        'OBJEKTE': 'Objektstammdaten - Gebäude und Immobilien',
        'WOHNUNG': 'Wohnungsstammdaten - Einzelne Wohneinheiten',
        'KONTEN': 'Kontostammdaten - Buchführungskonten für Mieter/Eigentümer',
        'BUCHUNG': 'Buchungsdaten - Alle finanziellen Transaktionen',
        'VERSAMMLUNG': 'Eigentümerversammlungen',
        'BESCHLUSS': 'Beschlüsse aus Eigentümerversammlungen',
        'VEREIG': 'Versammlungs-Eigentümer-Zuordnung',
        'TEILPLAN': 'Teilungserklärung und Eigentumsanteile',
        'RUECKPOS': 'Rücklagenpositionen',
        'VORAUSZ': 'Vorauszahlungen und Nebenkosten',
        'KONTO_B': 'Bank-Konten',
        'GRUND': 'Grundstücksinformationen'
    }
    
    ddl_statements = []
    
    # Generate DDL for core tables
    for table, desc in core_tables.items():
        if table in tables:
            ddl = f"-- {desc}\nCREATE TABLE {table} (\n"
            
            # Add fields we found
            fields = sorted(tables[table])
            field_defs = []
            
            for field in fields:
                # Infer data type based on field name patterns
                data_type = infer_data_type(field)
                field_def = f"    {field} {data_type}"
                
                # Add NOT NULL for key fields
                if field in ['KNR', 'ONR', 'ENR', 'BNR', 'BEWNR']:
                    field_def += " NOT NULL"
                
                field_defs.append(field_def)
            
            ddl += ",\n".join(field_defs)
            ddl += "\n);\n"
            ddl_statements.append(ddl)
    
    return ddl_statements

def infer_data_type(field_name):
    """Infer data type based on field name patterns"""
    
    # Common patterns
    if field_name.endswith('NR') or field_name in ['ONR', 'ENR', 'KNR', 'BNR']:
        return "INTEGER"
    elif field_name.endswith('DATUM') or 'BEGINN' in field_name or 'ENDE' in field_name:
        return "DATE"
    elif field_name.endswith('BETRAG') or field_name.startswith('Z') and field_name[1:].isdigit():
        return "NUMERIC(15,2)"
    elif field_name in ['BNAME', 'BVNAME', 'BSTR', 'BPLZORT', 'BEMAIL']:
        return "VARCHAR(100)"
    elif field_name.endswith('BEZ') or field_name.endswith('TEXT'):
        return "VARCHAR(200)"
    elif field_name.endswith('FLAG') or field_name in ['ABWESEND', 'AKTIV']:
        return "SMALLINT"
    elif 'IBAN' in field_name:
        return "VARCHAR(34)"
    elif 'BIC' in field_name or 'BLZ' in field_name:
        return "VARCHAR(11)"
    else:
        return "VARCHAR(50)"

def main():
    """Main function"""
    print("Extracting schema from SQL queries...")
    
    tables, descriptions = extract_tables_and_fields()
    
    print(f"\nFound {len(tables)} tables")
    print("\nCore tables and fields:")
    
    # Show core tables
    core_tables = ['BEWOHNER', 'BEWADR', 'EIGADR', 'OBJEKTE', 'WOHNUNG', 'KONTEN']
    
    schema_info = {}
    
    for table in core_tables:
        if table in tables:
            fields = sorted(tables[table])
            print(f"\n{table}: {len(fields)} fields")
            print(f"  Fields: {', '.join(fields[:10])}...")
            
            schema_info[table] = {
                'fields': list(fields),
                'field_count': len(fields)
            }
    
    # Generate DDL
    ddl_statements = create_ddl_from_analysis()
    
    # Save DDL
    with open('data/knowledge/wincasa_schema_from_queries.sql', 'w', encoding='utf-8') as f:
        f.write("-- WINCASA Database Schema (extracted from SQL queries)\n")
        f.write("-- This represents the ACTUAL tables and fields used in production\n\n")
        
        for ddl in ddl_statements:
            f.write(ddl)
            f.write("\n")
    
    # Save schema info as JSON
    with open('data/knowledge/wincasa_schema_info.json', 'w', encoding='utf-8') as f:
        json.dump(schema_info, f, indent=2, ensure_ascii=False)
    
    print(f"\nSchema saved to: data/knowledge/wincasa_schema_from_queries.sql")
    print(f"Schema info saved to: data/knowledge/wincasa_schema_info.json")

if __name__ == "__main__":
    main()