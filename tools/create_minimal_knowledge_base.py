#!/usr/bin/env python3
"""
Create minimal knowledge base focused on the 9 core tables.
Only includes mappings and rules that are actually used.
"""

import json
from pathlib import Path

def create_minimal_knowledge_base():
    """Create focused knowledge base for core tables only"""
    
    knowledge_base = {
        "version": "2.0",
        "description": "Minimal WINCASA Knowledge Base - Core Tables Only",
        
        # German to SQL field mappings
        "field_mappings": {
            # Eigentümer (Owner) mappings
            "eigentümer": "EIGADR",
            "eigentümername": "EIGADR.ENAME",
            "eigentümervorname": "EIGADR.EVNAME", 
            "eigentümerstrasse": "EIGADR.ESTR",
            "eigentümerort": "EIGADR.EPLZORT",
            "eigentümeremail": "EIGADR.EEMAIL",
            "eigentümertelefon": "EIGADR.ETEL1",
            
            # Mieter (Tenant) mappings
            "mieter": "BEWOHNER",
            "mietername": "BEWOHNER.BNAME",
            "mietervorname": "BEWOHNER.BVNAME",
            "mieterstrasse": "BEWOHNER.BSTR",
            "mieterort": "BEWOHNER.BPLZORT",
            "mieteremail": "BEWOHNER.BEMAIL",
            "mietertelefon": "BEWOHNER.BTEL",
            "kaltmiete": "BEWOHNER.Z1",  # CRITICAL!
            "nebenkosten": "BEWOHNER.Z3",
            "warmmiete": "BEWOHNER.MIETE1",
            "vertragsbeginn": "BEWOHNER.VBEGINN",
            "vertragsende": "BEWOHNER.VENDE",
            "kaution": "BEWOHNER.KAUT_VEREINBART",
            
            # Objekt (Property) mappings
            "objekt": "OBJEKTE",
            "objektbezeichnung": "OBJEKTE.OBEZ",
            "objektstrasse": "OBJEKTE.OSTRASSE",
            "objektort": "OBJEKTE.OPLZORT",
            "liegenschaft": "OBJEKTE",
            "gebäude": "OBJEKTE",
            
            # Wohnung (Apartment) mappings
            "wohnung": "WOHNUNG",
            "einheit": "WOHNUNG",
            "wohnungsbezeichnung": "WOHNUNG.EBEZ",
            "wohnungsart": "WOHNUNG.ART",
            
            # Konto mappings
            "konto": "KONTEN",
            "kontostand": "KONTEN.OPBETRAG",
            "offeneposten": "KONTEN.OPBETRAG",
            
            # Buchung (Transaction) mappings
            "buchung": "BUCHUNG",
            "zahlung": "BUCHUNG",
            "transaktion": "BUCHUNG",
            "betrag": "BUCHUNG.BETRAG",
            "datum": "BUCHUNG.DATUM",
            
            # Common terms
            "leerstand": "WOHNUNG ohne BEWOHNER (LEFT JOIN)",
            "aktiv": "VENDE IS NULL",
            "beendet": "VENDE IS NOT NULL"
        },
        
        # Table relationships
        "relationships": {
            "eigentümer_objekt": {
                "from": "EIGADR.EIGNR",
                "to": "OBJEKTE.EIGNR",
                "type": "1:n"
            },
            "objekt_wohnung": {
                "from": "OBJEKTE.ONR", 
                "to": "WOHNUNG.ONR",
                "type": "1:n"
            },
            "wohnung_mieter": {
                "from": ["WOHNUNG.ONR", "WOHNUNG.ENR"],
                "to": ["BEWOHNER.ONR", "BEWOHNER.ENR"],
                "type": "1:1",
                "note": "Aktiver Mieter wenn VENDE IS NULL"
            },
            "mieter_konto": {
                "from": "BEWOHNER.KNR",
                "to": "KONTEN.KNR", 
                "type": "1:1"
            },
            "konto_buchung": {
                "from": "KONTEN.KNR",
                "to": ["BUCHUNG.KHABEN", "BUCHUNG.KSOLL"],
                "type": "1:n"
            }
        },
        
        # Common query patterns
        "query_patterns": {
            "alle_mieter": {
                "sql": "SELECT * FROM BEWOHNER WHERE VENDE IS NULL",
                "description": "Alle aktiven Mieter"
            },
            "alle_eigentümer": {
                "sql": "SELECT * FROM EIGADR",
                "description": "Alle Eigentümer"
            },
            "leerstand": {
                "sql": """SELECT W.ONR, W.ENR, W.EBEZ, O.OBEZ 
                         FROM WOHNUNG W 
                         JOIN OBJEKTE O ON W.ONR = O.ONR 
                         LEFT JOIN BEWOHNER B ON W.ONR = B.ONR AND W.ENR = B.ENR 
                         WHERE B.KNR IS NULL""",
                "description": "Leerstehende Wohnungen"
            },
            "kaltmiete_summe": {
                "sql": "SELECT SUM(Z1) FROM BEWOHNER WHERE VENDE IS NULL",
                "description": "Summe aller Kaltmieten"
            },
            "mieter_in_objekt": {
                "sql": """SELECT B.BNAME, B.BVNAME, W.EBEZ 
                         FROM BEWOHNER B 
                         JOIN WOHNUNG W ON B.ONR = W.ONR AND B.ENR = W.ENR 
                         WHERE B.ONR = ? AND B.VENDE IS NULL""",
                "description": "Alle Mieter in einem Objekt"
            }
        },
        
        # Business rules
        "business_rules": {
            "aktive_mieter": "VENDE IS NULL OR VENDE > CURRENT_DATE",
            "echte_objekte": "ONR < 890",
            "mieterkonten": "KKLASSE = 60",
            "ohne_weg": "EIGNR <> -1",
            "einnahmen": "BETRAG > 0",
            "pünktliche_zahlung": "EXTRACT(DAY FROM DATUM) <= 5",
            "verspätete_zahlung": "EXTRACT(DAY FROM DATUM) BETWEEN 6 AND 15",
            "sehr_späte_zahlung": "EXTRACT(DAY FROM DATUM) > 15"
        },
        
        # Critical warnings
        "warnings": [
            "BEWOHNER hat KEIN EIGNR Feld! Nutze JOINs über OBJEKTE",
            "Kaltmiete ist Z1, nicht KALTMIETE",
            "Leerstand nur über LEFT JOIN ermitteln",
            "Verwende VENDE IS NULL für aktive Mieter",
            "ONR < 890 für echte Objekte"
        ]
    }
    
    # Save knowledge base
    output_path = Path("data/knowledge_base/minimal_knowledge_base.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
    
    print(f"Minimal knowledge base created: {output_path}")
    print(f"Size: {output_path.stat().st_size / 1024:.1f} KB")
    
    # Create integration script for knowledge base loader
    create_kb_integration_script()

def create_kb_integration_script():
    """Create script to integrate minimal KB into system"""
    
    script = '''#!/usr/bin/env python3
"""
Update knowledge base loader to use minimal KB.
"""

import json
from pathlib import Path

def update_knowledge_base_loader():
    """Update the knowledge base loader configuration"""
    
    kb_loader_path = Path("src/wincasa/knowledge/knowledge_base_loader.py")
    
    # Read current loader
    content = kb_loader_path.read_text()
    
    # Update path to minimal KB
    old_path = 'alias_map.json'
    new_path = 'minimal_knowledge_base.json'
    
    if old_path in content:
        content = content.replace(old_path, new_path)
        kb_loader_path.write_text(content)
        print(f"Updated {kb_loader_path} to use minimal KB")
    else:
        print("Knowledge base loader already updated or has different structure")

if __name__ == "__main__":
    update_knowledge_base_loader()
'''
    
    script_path = Path("tools/integrate_minimal_kb.py")
    script_path.write_text(script)
    script_path.chmod(0o755)
    print(f"Integration script created: {script_path}")

if __name__ == "__main__":
    create_minimal_knowledge_base()