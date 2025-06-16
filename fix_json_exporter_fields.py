#!/usr/bin/env python3
"""
Fix JSON exporter to use correct DDL field names
"""

import re
from pathlib import Path

def get_correct_field_mappings():
    """Get correct field mappings from DDL"""
    return {
        # BEWOHNER (Tenant) mappings
        'MIETER_NAME': 'BNAME',
        'MIETER_VORNAME': 'BVNAME', 
        'MIETER_STRASSE': 'BSTR',
        'MIETER_ORT': 'BPLZORT',
        'KALTMIETE': 'Z1',
        'NEBENKOSTEN': 'Z3',
        'HEIZKOSTEN': 'Z4',
        'GARAGENMIETE': 'Z2',
        'VERTRAGSENDE': 'VENDE',
        'BEWOHNER_NAME': 'BNAME',
        'BEWOHNER_VORNAME': 'BVNAME',
        
        # EIGADR (Owner) mappings
        'EIGENTUEMER_NAME': 'ENAME',
        'EIGENTUEMER_VORNAME': 'EVNAME',
        'EIGENTUEMER_STRASSE': 'ESTR',
        'EIGENTUEMER_ORT': 'EPLZORT',
        'EIGENTUEMER_ID': 'EIGNR',
        
        # OBJEKTE (Property) mappings
        'OBJEKT_STRASSE': 'OSTRASSE',
        'OBJEKT_ORT': 'OPLZORT',
        'OBJEKT_BEZEICHNUNG': 'OBEZ',
        'OBJEKT_NR': 'ONR',
        
        # WOHNUNG (Unit) mappings  
        'EINHEIT_BEZEICHNUNG': 'EBEZ',
        'EINHEIT_NR': 'ENR'
    }

def fix_sql_files():
    """Fix SQL files to use correct field names"""
    
    sql_dir = Path("data/sql")
    if not sql_dir.exists():
        print(f"Directory {sql_dir} not found")
        return
        
    mappings = get_correct_field_mappings()
    
    # Process all SQL files
    for sql_file in sql_dir.glob("*.sql"):
        print(f"\nProcessing {sql_file.name}...")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Replace incorrect field names with correct ones
        for wrong_name, correct_name in mappings.items():
            # Match patterns like SELECT MIETER_NAME or AS MIETER_NAME
            patterns = [
                # SELECT MIETER_NAME
                (rf'\b{wrong_name}\b(?!\s*AS)', correct_name),
                # AS MIETER_NAME
                (rf'AS\s+{wrong_name}\b', f'AS {correct_name}'),
                # COALESCE(MIETER_NAME
                (rf'COALESCE\s*\(\s*{wrong_name}\b', f'COALESCE({correct_name}'),
                # WHERE MIETER_NAME
                (rf'WHERE\s+{wrong_name}\b', f'WHERE {correct_name}'),
                # ORDER BY MIETER_NAME
                (rf'ORDER\s+BY\s+{wrong_name}\b', f'ORDER BY {correct_name}')
            ]
            
            for pattern, replacement in patterns:
                new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                if new_content != content:
                    changes_made.append(f"  {pattern} -> {replacement}")
                    content = new_content
        
        # Also fix common table name errors
        table_fixes = [
            ('FROM eigentuemer', 'FROM EIGADR'),
            ('JOIN eigentuemer', 'JOIN EIGADR'),
            ('FROM mieter', 'FROM BEWOHNER'),
            ('JOIN mieter', 'JOIN BEWOHNER'),
            ('FROM tenants', 'FROM BEWOHNER'),
            ('FROM owners', 'FROM EIGADR')
        ]
        
        for wrong, correct in table_fixes:
            new_content = re.sub(wrong, correct, content, flags=re.IGNORECASE)
            if new_content != content:
                changes_made.append(f"  {wrong} -> {correct}")
                content = new_content
        
        # Save if changes were made
        if content != original_content:
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Updated {sql_file.name} with {len(changes_made)} changes:")
            for change in changes_made[:5]:  # Show first 5 changes
                print(change)
            if len(changes_made) > 5:
                print(f"  ... and {len(changes_made) - 5} more changes")
        else:
            print(f"  No changes needed in {sql_file.name}")

def check_json_export_dir():
    """Check JSON export directory for files using wrong field names"""
    
    export_dir = Path("data/exports")
    if not export_dir.exists():
        print(f"\nExport directory {export_dir} not found")
        return
        
    print(f"\nChecking JSON exports in {export_dir}...")
    
    wrong_fields = ['MIETER_NAME', 'EIGENTUEMER_NAME', 'KALTMIETE', 'BEWNAME']
    
    for json_file in export_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            found_issues = []
            for field in wrong_fields:
                if field in content:
                    found_issues.append(field)
            
            if found_issues:
                print(f"  {json_file.name} contains wrong fields: {', '.join(found_issues)}")
        except Exception as e:
            print(f"  Error reading {json_file.name}: {e}")

if __name__ == "__main__":
    print("Fixing JSON exporter field names...\n")
    
    # Fix SQL files
    fix_sql_files()
    
    # Check existing JSON exports
    check_json_export_dir()
    
    print("\nDone! SQL queries have been updated to use correct DDL field names.")