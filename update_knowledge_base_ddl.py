#!/usr/bin/env python3
"""
Update knowledge base with correct DDL field mappings.
Based on actual Firebird database schema.
"""

import json
from pathlib import Path

def create_correct_field_mappings():
    """Create field mappings based on DDL schema"""
    
    # Core field mappings from DDL
    field_mappings = {
        # BEWOHNER (Mieter) fields
        "MIETER_NAME": {
            "canonical": "BEWOHNER.BNAME",
            "source_file": "DDL verified",
            "is_computed": False,
            "description": "Nachname des Mieters"
        },
        "MIETER_VORNAME": {
            "canonical": "BEWOHNER.BVNAME",
            "source_file": "DDL verified",
            "is_computed": False,
            "description": "Vorname des Mieters"
        },
        "MIETER_STRASSE": {
            "canonical": "BEWOHNER.BSTR",
            "source_file": "DDL verified",
            "is_computed": False,
            "description": "Straße des Mieters"
        },
        "MIETER_ORT": {
            "canonical": "BEWOHNER.BPLZORT",
            "source_file": "DDL verified",
            "is_computed": False,
            "description": "PLZ und Ort des Mieters"
        },
        "KALTMIETE": {
            "canonical": "BEWOHNER.Z1",
            "source_file": "DDL verified",
            "is_computed": False,
            "description": "Kaltmiete (ohne Nebenkosten)"
        },
        "GARAGENMIETE": {
            "canonical": "BEWOHNER.Z2",
            "source_file": "DDL verified",
            "is_computed": False
        },
        "BETRIEBSKOSTEN": {
            "canonical": "BEWOHNER.Z3",
            "source_file": "DDL verified",
            "is_computed": False
        },
        "HEIZKOSTEN": {
            "canonical": "BEWOHNER.Z4",
            "source_file": "DDL verified",
            "is_computed": False
        },
        "WARMMIETE": {
            "canonical": "EXPRESSION: (COALESCE(BEWOHNER.Z1, 0) + COALESCE(BEWOHNER.Z2, 0) + COALESCE(BEWOHNER.Z3, 0) + COALESCE(BEWOHNER.Z4, 0))",
            "source_file": "02_mieter.sql",
            "is_computed": True,
            "description": "Gesamtmiete inkl. Nebenkosten"
        },
        "VERTRAGSENDE": {
            "canonical": "BEWOHNER.VENDE",
            "source_file": "DDL verified",
            "is_computed": False,
            "description": "NULL = aktiver Mieter"
        },
        
        # EIGADR (Eigentümer) fields
        "EIGENTUEMER_NAME": {
            "canonical": "EIGADR.ENAME",
            "source_file": "DDL verified",
            "is_computed": False,
            "description": "Nachname des Eigentümers"
        },
        "EIGENTUEMER_VORNAME": {
            "canonical": "EIGADR.EVNAME",
            "source_file": "DDL verified",
            "is_computed": False,
            "description": "Vorname des Eigentümers"
        },
        "EIGENTUEMER_STRASSE": {
            "canonical": "EIGADR.ESTR",
            "source_file": "DDL verified",
            "is_computed": False,
            "description": "Straße des Eigentümers"
        },
        "EIGENTUEMER_ORT": {
            "canonical": "EIGADR.EPLZORT",
            "source_file": "DDL verified",
            "is_computed": False,
            "description": "PLZ und Ort des Eigentümers"
        },
        "EIGENTUEMER_ID": {
            "canonical": "EIGADR.EIGNR",
            "source_file": "DDL verified",
            "is_computed": False,
            "description": "Eindeutige Eigentümer-ID"
        },
        
        # OBJEKTE fields
        "OBJEKT_BEZEICHNUNG": {
            "canonical": "OBJEKTE.OBEZ",
            "source_file": "DDL verified",
            "is_computed": False
        },
        "OBJEKT_STRASSE": {
            "canonical": "OBJEKTE.OSTRASSE",
            "source_file": "DDL verified",
            "is_computed": False
        },
        "OBJEKT_ORT": {
            "canonical": "OBJEKTE.OPLZORT",
            "source_file": "DDL verified",
            "is_computed": False
        },
        "OBJEKT_NR": {
            "canonical": "OBJEKTE.ONR",
            "source_file": "DDL verified",
            "is_computed": False
        },
        
        # WOHNUNG fields
        "EINHEIT_BEZEICHNUNG": {
            "canonical": "WOHNUNG.EBEZ",
            "source_file": "DDL verified",
            "is_computed": False,
            "description": "z.B. '1. OG rechts'"
        },
        "EINHEIT_NR": {
            "canonical": "WOHNUNG.ENR",
            "source_file": "DDL verified",
            "is_computed": False
        }
    }
    
    # Add existing mappings that are still valid
    existing_file = Path("data/knowledge_base/alias_map.json")
    if existing_file.exists():
        with open(existing_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        
        # Keep computed expressions that are valid
        for key, value in existing.items():
            if key not in field_mappings and value.get('is_computed', False):
                # Verify it doesn't use fantasy fields
                canonical = value.get('canonical', '')
                if ('BEWNAME' not in canonical and 
                    'OWNERS' not in canonical and
                    'TENANTS' not in canonical):
                    field_mappings[key] = value
    
    return field_mappings

def update_business_vocabulary():
    """Update German business vocabulary with correct table names"""
    
    vocabulary = {
        # Entities
        "mieter": ["BEWOHNER", "tenant", "renter"],
        "eigentümer": ["EIGADR", "owner", "proprietor"],
        "eigentuemer": ["EIGADR", "owner", "proprietor"],
        "objekt": ["OBJEKTE", "property", "building"],
        "liegenschaft": ["OBJEKTE", "property", "real estate"],
        "wohnung": ["WOHNUNG", "apartment", "unit"],
        "einheit": ["WOHNUNG", "unit", "apartment"],
        
        # Fields
        "kaltmiete": ["BEWOHNER.Z1", "net rent", "cold rent"],
        "warmmiete": ["BEWOHNER.Z1+Z2+Z3+Z4", "gross rent", "warm rent"],
        "nebenkosten": ["BEWOHNER.Z3", "utilities", "service charges"],
        "heizkosten": ["BEWOHNER.Z4", "heating costs"],
        "name": ["BNAME or ENAME", "surname", "last name"],
        "vorname": ["BVNAME or EVNAME", "first name"],
        "strasse": ["BSTR or ESTR or OSTRASSE", "street"],
        "straße": ["BSTR or ESTR or OSTRASSE", "street"],
        
        # Status
        "aktiv": ["VENDE IS NULL", "active", "current"],
        "leerstand": ["no BEWOHNER record", "vacancy", "empty"],
        "vermietet": ["has BEWOHNER record", "rented", "occupied"]
    }
    
    return vocabulary

def main():
    """Update knowledge base files"""
    
    kb_dir = Path("data/knowledge_base")
    
    # Update field mappings
    print("Updating field mappings...")
    field_mappings = create_correct_field_mappings()
    
    with open(kb_dir / "alias_map.json", 'w', encoding='utf-8') as f:
        json.dump(field_mappings, f, indent=2, ensure_ascii=False)
    
    print(f"Updated {len(field_mappings)} field mappings")
    
    # Update business vocabulary
    print("\nUpdating business vocabulary...")
    vocabulary = update_business_vocabulary()
    
    with open(kb_dir / "business_vocabulary.json", 'w', encoding='utf-8') as f:
        json.dump(vocabulary, f, indent=2, ensure_ascii=False)
    
    print(f"Updated {len(vocabulary)} business terms")
    
    # Create SQL hints file
    sql_hints = {
        "common_mistakes": {
            "BEWNAME": "Use BNAME instead",
            "OWNERS": "Use EIGADR table instead",
            "TENANTS": "Use BEWOHNER table instead",
            "STRASSE": "Use BSTR, ESTR, or OSTRASSE",
            "STADT": "Use BPLZORT or EPLZORT or OPLZORT",
            "KALTMIETE": "Use Z1 field instead",
            "AKTIV": "Use VENDE IS NULL instead"
        },
        "table_mappings": {
            "tenants": "BEWOHNER",
            "owners": "EIGADR",
            "properties": "OBJEKTE",
            "units": "WOHNUNG",
            "accounts": "KONTEN"
        },
        "critical_joins": {
            "mieter_to_objekt": "BEWOHNER.ONR = OBJEKTE.ONR",
            "objekt_to_owner": "OBJEKTE.EIGNR = EIGADR.EIGNR",
            "mieter_address": "BEWOHNER.BEWNR = BEWADR.BEWNR"
        }
    }
    
    with open(kb_dir / "sql_hints.json", 'w', encoding='utf-8') as f:
        json.dump(sql_hints, f, indent=2, ensure_ascii=False)
    
    print("\nCreated SQL hints file")
    print("\nKnowledge base update complete!")

if __name__ == "__main__":
    main()