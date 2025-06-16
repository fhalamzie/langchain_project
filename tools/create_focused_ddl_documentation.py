#!/usr/bin/env python3
"""
Create focused DDL documentation for WINCASA core tables.
Only includes the 9 tables actually used in production queries.
"""

import json
from pathlib import Path

# Core tables identified from SQL query analysis
CORE_TABLES = [
    "EIGADR",      # Owner addresses
    "OBJEKTE",     # Properties  
    "WOHNUNG",     # Apartments
    "BEWOHNER",    # Tenants (NO EIGNR field!)
    "KONTEN",      # Accounts
    "EIGENTUEMER", # Ownership relations
    "BUCHUNG",     # Transactions
    "BEWADR",      # Tenant addresses
    "HK_WOHN"      # Heating/area data
]

# Critical field mappings that MUST be correct
CRITICAL_MAPPINGS = {
    "KALTMIETE": "BEWOHNER.Z1",  # NOT KBETRAG!
    "OWNER_NAME": "EIGADR.ENAME", # NOT OWNERS.NAME
    "OWNER_STREET": "EIGADR.ESTR", # NOT STRASSE
    "TENANT_NAME": "BEWOHNER.BNAME", # NOT BEWNAME
    "TENANT_CITY": "BEWOHNER.BPLZORT", # NOT STADT
    "PROPERTY_STREET": "OBJEKTE.OSTRASSE", # NOT STRASSE
    "PROPERTY_CITY": "OBJEKTE.OPLZORT", # NOT ORT
}

# Business rules that must be documented
BUSINESS_RULES = {
    "ACTIVE_TENANTS": "VENDE IS NULL",
    "EXCLUDE_TEST": "ONR < 890", 
    "TENANT_ACCOUNTS": "KKLASSE = 60",
    "EXCLUDE_WEG": "EIGNR <> -1",
    "INCOME_ONLY": "BETRAG > 0",
}

def extract_ddl_for_table(table_name):
    """Read DDL from schema file"""
    ddl_path = Path(f"data/ddl_creation schema/{table_name}_table.sql")
    if ddl_path.exists():
        return ddl_path.read_text()
    return None

def parse_columns_from_ddl(ddl_content):
    """Extract column definitions from DDL"""
    columns = []
    in_create_table = False
    
    for line in ddl_content.split('\n'):
        line = line.strip()
        
        if line.startswith('CREATE TABLE'):
            in_create_table = True
            continue
            
        if in_create_table and line.startswith(')'):
            break
            
        if in_create_table and line and not line.startswith('PRIMARY KEY') and not line.startswith('FOREIGN KEY'):
            # Parse column definition
            parts = line.split()
            if len(parts) >= 2:
                col_name = parts[0].rstrip(',')
                col_type = parts[1]
                nullable = 'NULL' in line
                default = None
                if 'DEFAULT' in line:
                    default_idx = line.find('DEFAULT')
                    default = line[default_idx:].split()[1].strip("'")
                
                columns.append({
                    'name': col_name,
                    'type': col_type,
                    'nullable': nullable,
                    'default': default
                })
    
    return columns

def create_focused_documentation():
    """Generate focused DDL documentation"""
    
    documentation = {
        "version": "1.0",
        "description": "Focused WINCASA DDL for core tables only",
        "tables": {},
        "critical_mappings": CRITICAL_MAPPINGS,
        "business_rules": BUSINESS_RULES,
        "relationships": {
            "owner_property": "EIGADR.EIGNR -> EIGENTUEMER.EIGNR -> OBJEKTE",
            "tenant_apartment": "BEWOHNER.ONR+ENR -> WOHNUNG.ONR+ENR", 
            "tenant_account": "BEWOHNER.KNR -> KONTEN.KNR",
            "transaction_account": "BUCHUNG.KHABEN/KSOLL -> KONTEN.KNR"
        }
    }
    
    print("Extracting DDL for core tables...")
    
    for table in CORE_TABLES:
        print(f"Processing {table}...")
        ddl_content = extract_ddl_for_table(table)
        
        if ddl_content:
            columns = parse_columns_from_ddl(ddl_content)
            
            # Identify key columns based on usage
            key_columns = []
            if table == "EIGADR":
                key_columns = ["EIGNR", "ENAME", "EVNAME", "ESTR", "EPLZORT", "ETEL1", "EEMAIL"]
            elif table == "BEWOHNER":
                key_columns = ["ONR", "KNR", "ENR", "BEWNR", "BNAME", "BVNAME", "BSTR", "BPLZORT", "Z1", "VENDE"]
            elif table == "OBJEKTE":
                key_columns = ["ONR", "OBEZ", "OSTRASSE", "OPLZORT", "EIGNR"]
            elif table == "WOHNUNG":
                key_columns = ["ONR", "ENR", "EBEZ", "ART"]
            elif table == "KONTEN":
                key_columns = ["KNR", "KKLASSE", "ONR", "BEWNR", "OPBETRAG"]
            
            documentation["tables"][table] = {
                "columns": columns,
                "key_columns": key_columns,
                "total_columns": len(columns),
                "description": get_table_description(table)
            }
        else:
            print(f"WARNING: DDL not found for {table}")
    
    # Save documentation
    output_path = Path("data/knowledge_base/focused_ddl_documentation.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(documentation, f, indent=2, ensure_ascii=False)
    
    print(f"\nFocused DDL documentation created: {output_path}")
    
    # Create compact version for prompts
    create_compact_prompt_version(documentation)
    
    return documentation

def get_table_description(table):
    """Get business description for table"""
    descriptions = {
        "EIGADR": "Eigentümer-Stammdaten mit Kontaktdaten und Banking",
        "OBJEKTE": "Liegenschafts-Stammdaten mit Verwaltungsinformationen",
        "WOHNUNG": "Wohnungseinheiten innerhalb der Objekte",
        "BEWOHNER": "Mieter-Stammdaten mit Vertragsdaten (KEIN EIGNR!)",
        "KONTEN": "Buchhaltungskonten für Mieter und Eigentümer",
        "EIGENTUEMER": "Eigentumsrelationen zwischen Personen und Objekten",
        "BUCHUNG": "Finanztransaktionen und Zahlungseingänge",
        "BEWADR": "Zusätzliche Mieter-Adressen",
        "HK_WOHN": "Heizkosten und Flächendaten"
    }
    return descriptions.get(table, "")

def create_compact_prompt_version(documentation):
    """Create ultra-compact version for LLM prompts"""
    
    compact = []
    compact.append("WINCASA CORE TABLES (nur diese 9 Tabellen verwenden!):\n")
    
    for table, info in documentation["tables"].items():
        compact.append(f"\n{table}: {info['description']}")
        compact.append(f"  Schlüsselfelder: {', '.join(info['key_columns'])}")
        
        # Add critical notes
        if table == "BEWOHNER":
            compact.append("  WICHTIG: KEIN EIGNR FELD! Verwende ONR+ENR für Wohnungszuordnung")
            compact.append("  KALTMIETE = Z1 (nicht KALTMIETE oder KBETRAG!)")
    
    compact.append("\nKRITISCHE FELDNAMEN (niemals fantasieren!):")
    for concept, field in CRITICAL_MAPPINGS.items():
        compact.append(f"  {concept}: {field}")
    
    compact.append("\nBUSINESS RULES:")
    for rule, sql in BUSINESS_RULES.items():
        compact.append(f"  {rule}: {sql}")
    
    compact_text = '\n'.join(compact)
    
    # Save compact version
    output_path = Path("data/knowledge_base/compact_ddl_prompt.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(compact_text)
    
    print(f"Compact prompt version created: {output_path}")
    print(f"Size: {len(compact_text)} characters")

if __name__ == "__main__":
    create_focused_documentation()