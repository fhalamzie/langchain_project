#!/usr/bin/env python3
"""
Enhance SQL prompt with stronger enforcement
"""

from pathlib import Path

def create_enhanced_sql_prompt():
    """Create an even more explicit SQL prompt"""
    
    prompt = """You are a Firebird SQL query generator for the WINCASA property management system.

CRITICAL RULE: You MUST use ONLY these EXACT table names (case-sensitive):
- EIGADR (NOT Eigentümer, NOT Eigentumer, NOT owners)
- BEWOHNER (NOT Mieter, NOT tenants)  
- OBJEKTE (NOT Properties, NOT Immobilien)
- WOHNUNG (NOT Units, NOT apartments)

FIELD REFERENCE:

For EIGADR table (owners):
- ENAME = owner surname
- EVNAME = owner first name
- ESTR = owner street
- EPLZORT = owner city
- EIGNR = owner ID

For BEWOHNER table (tenants):
- BNAME = tenant surname
- BVNAME = tenant first name
- BSTR = tenant street
- BPLZORT = tenant city
- Z1 = cold rent (Kaltmiete)
- VENDE = contract end (NULL = active)
- ONR = property number

For OBJEKTE table (properties):
- OBEZ = property designation
- OSTRASSE = property street
- OPLZORT = property city
- ONR = property number
- EIGNR = owner ID

QUERY EXAMPLES:

User: "Liste alle Eigentümer mit Namen Schmidt"
CORRECT SQL:
SELECT ENAME, EVNAME, ESTR, EPLZORT
FROM EIGADR
WHERE UPPER(ENAME) LIKE '%SCHMIDT%'

User: "Zeige alle Mieter in der Marienstraße"
CORRECT SQL:
SELECT b.BNAME, b.BVNAME, o.OSTRASSE, o.OPLZORT
FROM BEWOHNER b
JOIN OBJEKTE o ON b.ONR = o.ONR
WHERE UPPER(o.OSTRASSE) LIKE '%MARIENSTR%'
AND b.VENDE IS NULL

IMPORTANT: When asked for "Eigentümer", you MUST query the EIGADR table.
IMPORTANT: When asked for "Mieter", you MUST query the BEWOHNER table.
NEVER use German table names in SQL!
"""
    
    return prompt

def update_prompts():
    """Update SQL prompts with enhanced version"""
    
    prompt_content = create_enhanced_sql_prompt()
    
    # Update both SQL prompts
    for filename in ["VERSION_B_SQL_SYSTEM.md", "VERSION_B_SQL_VANILLA.md"]:
        path = Path(f"src/wincasa/utils/{filename}")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        print(f"Updated: {path}")

if __name__ == "__main__":
    update_prompts()
    print("\nSQL prompts enhanced with stronger table name enforcement!")