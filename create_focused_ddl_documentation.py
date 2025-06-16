#!/usr/bin/env python3
"""
Create focused DDL documentation for core WINCASA tables.
Only includes tables actually used in SQL queries.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

def extract_tables_from_sql(sql_file):
    """Extract table names from SQL file"""
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find table names after FROM and JOIN
    tables = set()
    
    # Pattern for FROM and JOIN clauses
    patterns = [
        r'FROM\s+(\w+)',
        r'JOIN\s+(\w+)',
        r'LEFT\s+JOIN\s+(\w+)',
        r'RIGHT\s+JOIN\s+(\w+)',
        r'INNER\s+JOIN\s+(\w+)',
        r'LEFT\s+OUTER\s+JOIN\s+(\w+)',
        r'RIGHT\s+OUTER\s+JOIN\s+(\w+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        tables.update(match.upper() for match in matches)
    
    return tables

def get_ddl_for_table(table_name, ddl_dir):
    """Get DDL content for a specific table"""
    ddl_file = ddl_dir / f"{table_name}_table.sql"
    if ddl_file.exists():
        with open(ddl_file, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def create_focused_ddl_doc():
    """Create focused DDL documentation"""
    # Paths
    sql_dir = Path("data/sql")
    ddl_dir = Path("data/ddl_creation schema")
    output_file = Path("data/knowledge_base/focused_ddl_schema.md")
    
    # Extract all used tables
    all_tables = set()
    table_usage = defaultdict(list)
    
    for sql_file in sorted(sql_dir.glob("*.sql")):
        print(f"Analyzing {sql_file.name}...")
        tables = extract_tables_from_sql(sql_file)
        all_tables.update(tables)
        for table in tables:
            table_usage[table].append(sql_file.name)
    
    # Core tables (most frequently used)
    core_tables = ['BEWOHNER', 'EIGADR', 'OBJEKTE', 'WOHNUNG', 'KONTEN', 
                   'EIGENTUEMER', 'BEWADR', 'BUCHUNG']
    
    # Create documentation
    doc_lines = [
        "# WINCASA Focused DDL Schema Documentation",
        "",
        "This document contains the DDL definitions for core tables used in WINCASA queries.",
        "Generated from actual Firebird database schema.",
        "",
        "## Critical Field Mappings",
        "",
        "### WICHTIG - Häufige Fehler:",
        "- **KEIN EIGNR in BEWOHNER!** (Eigentümer-ID ist nur in EIGADR/EIGENTUEMER)",
        "- Mieter-Name: `BEWOHNER.BNAME` (nicht BEWNAME)",
        "- Kaltmiete: `BEWOHNER.Z1` (nicht KALTMIETE oder MIETE)",
        "- Eigentümer: Tabelle `EIGADR` (nicht OWNERS)",
        "- Straße Mieter: `BEWOHNER.BSTR` (nicht STRASSE)",
        "- Stadt/Ort: `BEWOHNER.BPLZORT` (nicht STADT)",
        "",
        "## Core Tables (Used in 90% of queries)",
        ""
    ]
    
    # Add DDL for core tables
    for table in core_tables:
        if table in all_tables:
            ddl_content = get_ddl_for_table(table, ddl_dir)
            if ddl_content:
                doc_lines.extend([
                    f"### {table}",
                    f"Used in: {', '.join(sorted(table_usage[table])[:3])}...",
                    "```sql",
                    ddl_content.strip(),
                    "```",
                    ""
                ])
    
    # Add summary of other tables
    doc_lines.extend([
        "## Supporting Tables",
        ""
    ])
    
    other_tables = sorted(all_tables - set(core_tables))
    for table in other_tables[:10]:  # Limit to 10 most important
        doc_lines.append(f"- **{table}**: Used in {', '.join(sorted(table_usage[table])[:2])}")
    
    # Key relationships
    doc_lines.extend([
        "",
        "## Key Relationships",
        "",
        "1. **Mieter zu Wohnung**: BEWOHNER.ONR + ENR -> WOHNUNG.ONR + ENR",
        "2. **Eigentümer zu Objekt**: EIGADR.EIGNR -> EIGENTUEMER.EIGNR -> OBJEKTE.EIGNR",
        "3. **Mieter-Adresse**: BEWADR.BEWNR = BEWOHNER.BEWNR",
        "4. **Konten**: BEWOHNER.ONR + KNR + ENR = KONTEN.ONR + KNR + ENR",
        "",
        "## Field Usage Examples",
        "",
        "```sql",
        "-- Mieter finden",
        "SELECT BNAME, BVNAME, BSTR, BPLZORT FROM BEWOHNER WHERE BNAME LIKE '%Müller%';",
        "",
        "-- Eigentümer finden", 
        "SELECT ENAME, EVNAME, ESTR, EPLZORT FROM EIGADR WHERE ENAME LIKE '%Schmidt%';",
        "",
        "-- Kaltmiete berechnen",
        "SELECT Z1 AS KALTMIETE FROM BEWOHNER WHERE ONR = 123;",
        "```"
    ])
    
    # Write documentation
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(doc_lines))
    
    print(f"\nCreated focused DDL documentation: {output_file}")
    print(f"Total tables found: {len(all_tables)}")
    print(f"Core tables documented: {len([t for t in core_tables if t in all_tables])}")
    
    # Also create a compact JSON version
    json_output = Path("data/knowledge_base/focused_ddl_schema.json")
    ddl_data = {
        "core_tables": core_tables,
        "all_tables": sorted(list(all_tables)),
        "table_usage": dict(table_usage),
        "critical_mappings": {
            "KALTMIETE": "BEWOHNER.Z1",
            "MIETER_NAME": "BEWOHNER.BNAME",
            "MIETER_VORNAME": "BEWOHNER.BVNAME",
            "MIETER_STRASSE": "BEWOHNER.BSTR",
            "MIETER_ORT": "BEWOHNER.BPLZORT",
            "EIGENTÜMER_NAME": "EIGADR.ENAME",
            "EIGENTÜMER_VORNAME": "EIGADR.EVNAME",
            "EIGENTÜMER_STRASSE": "EIGADR.ESTR",
            "EIGENTÜMER_ORT": "EIGADR.EPLZORT"
        }
    }
    
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(ddl_data, f, indent=2, ensure_ascii=False)
    
    print(f"Created JSON schema: {json_output}")

if __name__ == "__main__":
    create_focused_ddl_doc()