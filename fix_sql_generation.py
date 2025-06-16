#!/usr/bin/env python3
"""
Fix SQL generation by enforcing exact table names in prompts
"""

import json
from pathlib import Path

def create_sql_enforcement_prompt():
    """Create a strict SQL prompt that enforces exact table names"""
    
    prompt = """# WINCASA SQL Generator - STRICT MODE

## CRITICAL: You MUST use EXACT table names from this list:

### PRIMARY TABLES (USE THESE EXACT NAMES):
- BEWOHNER (for tenants/Mieter) - NEVER use "Mieter", "TENANTS", etc.
- EIGADR (for owners/Eigentümer) - NEVER use "Eigentümer", "OWNERS", etc.
- OBJEKTE (for properties/Objekte) - NEVER use "Properties", "IMMOBILIEN", etc.
- WOHNUNG (for units/apartments) - NEVER use "UNITS", "APARTMENTS", etc.

### FIELD MAPPINGS (EXACT NAMES REQUIRED):

#### BEWOHNER (Tenant table):
- BNAME (tenant surname) - NOT "BEWNAME" or "NAME"
- BVNAME (tenant first name) - NOT "VORNAME"
- BSTR (tenant street) - NOT "STRASSE" or "STREET"
- BPLZORT (tenant city) - NOT "ORT" or "STADT"
- Z1 (cold rent/Kaltmiete) - NOT "KALTMIETE"
- Z2 (garage rent)
- Z3 (utilities/Nebenkosten)
- Z4 (heating/Heizkosten)
- VENDE (contract end date, NULL = active)
- ONR (property number for joining)

#### EIGADR (Owner table):
- ENAME (owner surname)
- EVNAME (owner first name)
- ESTR (owner street)
- EPLZORT (owner city)
- EIGNR (owner ID)

#### OBJEKTE (Property table):
- OBEZ (property designation)
- OSTRASSE (property street)
- OPLZORT (property city)
- ONR (property number)
- EIGNR (owner ID for joining)

## SQL GENERATION RULES:

1. ALWAYS use the EXACT table names listed above
2. NEVER translate table names to German or English
3. NEVER use special characters (ä, ö, ü) in table or field names
4. For active tenants: WHERE VENDE IS NULL
5. Standard joins:
   - BEWOHNER.ONR = OBJEKTE.ONR
   - OBJEKTE.EIGNR = EIGADR.EIGNR

## EXAMPLES OF CORRECT SQL:

### Find all owners named Schmidt:
```sql
SELECT ENAME, EVNAME, ESTR, EPLZORT
FROM EIGADR
WHERE UPPER(ENAME) LIKE '%SCHMIDT%'
```

### Find all tenants in Marienstraße:
```sql
SELECT b.BNAME, b.BVNAME, o.OSTRASSE, o.OPLZORT
FROM BEWOHNER b
JOIN OBJEKTE o ON b.ONR = o.ONR
WHERE UPPER(o.OSTRASSE) LIKE '%MARIENSTR%'
AND b.VENDE IS NULL
```

### Find owner of a specific property:
```sql
SELECT e.ENAME, e.EVNAME, o.OBEZ, o.OSTRASSE
FROM OBJEKTE o
JOIN EIGADR e ON o.EIGNR = e.EIGNR
WHERE UPPER(o.OSTRASSE) LIKE '%MARIENSTR%'
```

## COMMON MISTAKES TO AVOID:
❌ FROM Eigentümer  → ✅ FROM EIGADR
❌ FROM Mieter      → ✅ FROM BEWOHNER
❌ WHERE AKTIV = 1  → ✅ WHERE VENDE IS NULL
❌ SELECT KALTMIETE → ✅ SELECT Z1
❌ WHERE STRASSE    → ✅ WHERE BSTR/ESTR/OSTRASSE

REMEMBER: Use ONLY the exact table and field names provided above!
"""
    
    return prompt

def update_sql_prompts():
    """Update all SQL prompt files with strict enforcement"""
    
    prompt_content = create_sql_enforcement_prompt()
    
    # Update VERSION_B_SQL_SYSTEM.md
    sql_system_path = Path("src/wincasa/utils/VERSION_B_SQL_SYSTEM.md")
    with open(sql_system_path, 'w', encoding='utf-8') as f:
        f.write(prompt_content)
    print(f"Updated: {sql_system_path}")
    
    # Update VERSION_B_SQL_VANILLA.md with similar content
    sql_vanilla_path = Path("src/wincasa/utils/VERSION_B_SQL_VANILLA.md")
    vanilla_prompt = prompt_content.replace("STRICT MODE", "VANILLA MODE")
    with open(sql_vanilla_path, 'w', encoding='utf-8') as f:
        f.write(vanilla_prompt)
    print(f"Updated: {sql_vanilla_path}")
    
    # Create a SQL hints file for the knowledge base
    sql_hints = {
        "table_enforcement": {
            "NEVER_USE": ["Eigentümer", "Mieter", "OWNERS", "TENANTS", "Properties"],
            "ALWAYS_USE": {
                "tenants": "BEWOHNER",
                "owners": "EIGADR", 
                "properties": "OBJEKTE",
                "units": "WOHNUNG"
            }
        },
        "field_enforcement": {
            "NEVER_USE": ["BEWNAME", "KALTMIETE", "STRASSE", "AKTIV"],
            "ALWAYS_USE": {
                "tenant_name": "BNAME",
                "cold_rent": "Z1",
                "street": "BSTR/ESTR/OSTRASSE",
                "active": "VENDE IS NULL"
            }
        },
        "critical_rules": [
            "Table names are CASE SENSITIVE in Firebird",
            "Never use German special characters in SQL",
            "Always use UPPER() for LIKE comparisons",
            "BEWOHNER has no EIGNR field - join through OBJEKTE"
        ]
    }
    
    kb_path = Path("data/knowledge_base/sql_enforcement.json")
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(sql_hints, f, indent=2, ensure_ascii=False)
    print(f"Created: {kb_path}")

if __name__ == "__main__":
    update_sql_prompts()
    print("\nSQL prompts updated with strict table name enforcement!")