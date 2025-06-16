#!/usr/bin/env python3
"""
Update Knowledge Base with Correct WINCASA Schema
Fixes critical issues where LLM generates wrong table/field names
"""

import os
import sys
import json
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_schema_info():
    """Load the extracted schema information"""
    schema_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'schema')
    
    # Load critical schema
    with open(os.path.join(schema_dir, 'llm_critical_schema.json'), 'r') as f:
        critical_schema = json.load(f)
    
    # Load complete tables
    with open(os.path.join(schema_dir, 'complete_tables.json'), 'r') as f:
        complete_tables = json.load(f)
    
    return critical_schema, complete_tables

def create_schema_mappings(critical_schema, complete_tables):
    """Create comprehensive field mappings from schema"""
    mappings = {
        "_metadata": {
            "generated": datetime.now().isoformat(),
            "purpose": "Critical WINCASA schema mappings for LLM SQL generation"
        },
        "critical_corrections": {
            "NEVER_USE": [
                "OWNERS table (use EIGADR)",
                "TENANTS table (use BEWOHNER)",
                "STRASSE field (use OSTRASSE/BSTRASSE/ESTR)",
                "BEWNAME field (use BNAME)",
                "STADT field (use OPLZORT/BPLZORT/EPLZORT)",
                "KALTMIETE as field name (use Z1)",
                "EIGNR in BEWOHNER (doesn't exist!)",
                "ONR in EIGADR (doesn't exist!)",
                "OBJNR (use ONR)",
                "OBJNAME (use OBEZ)",
                "WOHNUNGEN table (use WOHNUNG singular)"
            ],
            "ALWAYS_USE": critical_schema['common_mistakes']['CORRECT']
        },
        "table_mappings": {
            "mieter": "BEWOHNER",
            "tenant": "BEWOHNER",
            "tenants": "BEWOHNER",
            "eigentümer": "EIGADR",
            "eigentuemer": "EIGADR",
            "owner": "EIGADR",
            "owners": "EIGADR",
            "objekt": "OBJEKTE",
            "objekte": "OBJEKTE",
            "property": "OBJEKTE",
            "properties": "OBJEKTE",
            "gebäude": "OBJEKTE",
            "gebaeude": "OBJEKTE",
            "wohnung": "WOHNUNG",
            "wohnungen": "WOHNUNG",
            "apartment": "WOHNUNG",
            "apartments": "WOHNUNG",
            "einheit": "WOHNUNG",
            "einheiten": "WOHNUNG"
        },
        "field_mappings": {
            # BEWOHNER mappings
            "kaltmiete": "BEWOHNER.Z1",
            "nettokaltmiete": "BEWOHNER.Z1",
            "cold_rent": "BEWOHNER.Z1",
            "mieter_name": "BEWOHNER.BNAME",
            "tenant_name": "BEWOHNER.BNAME",
            "mieter_strasse": "BEWOHNER.BSTR",
            "mieter_adresse": "BEWOHNER.BSTR",
            "mieter_plz": "BEWOHNER.BPLZORT",
            "mieter_ort": "BEWOHNER.BPLZORT",
            "mieter_stadt": "BEWOHNER.BPLZORT",
            
            # EIGADR mappings
            "eigentümer_name": "EIGADR.ENAME",
            "eigentuemer_name": "EIGADR.ENAME",
            "owner_name": "EIGADR.ENAME",
            "eigentümer_strasse": "EIGADR.ESTR",
            "eigentuemer_strasse": "EIGADR.ESTR",
            "eigentümer_plz": "EIGADR.EPLZORT",
            "eigentuemer_plz": "EIGADR.EPLZORT",
            "eigentümer_ort": "EIGADR.EPLZORT",
            "eigentuemer_ort": "EIGADR.EPLZORT",
            
            # OBJEKTE mappings
            "objektnummer": "OBJEKTE.ONR",
            "property_number": "OBJEKTE.ONR",
            "objektbezeichnung": "OBJEKTE.OBEZ",
            "property_name": "OBJEKTE.OBEZ",
            "objekt_strasse": "OBJEKTE.OSTRASSE",
            "property_street": "OBJEKTE.OSTRASSE",
            "objekt_plz": "OBJEKTE.OPLZORT",
            "objekt_ort": "OBJEKTE.OPLZORT",
            
            # WOHNUNG mappings
            "wohnungsnummer": "WOHNUNG.ENR",
            "apartment_number": "WOHNUNG.ENR",
            "wohnungsbezeichnung": "WOHNUNG.EBEZ",
            "apartment_name": "WOHNUNG.EBEZ"
        },
        "critical_relationships": {
            "tenant_property": {
                "description": "Join BEWOHNER with OBJEKTE",
                "sql": "BEWOHNER B JOIN OBJEKTE O ON B.ONR = O.ONR"
            },
            "tenant_apartment": {
                "description": "Join BEWOHNER with WOHNUNG",
                "sql": "BEWOHNER B JOIN WOHNUNG W ON B.ONR = W.ONR AND B.ENR = W.ENR"
            },
            "apartment_property": {
                "description": "Join WOHNUNG with OBJEKTE",
                "sql": "WOHNUNG W JOIN OBJEKTE O ON W.ONR = O.ONR"
            },
            "vacancy_detection": {
                "description": "Find vacant apartments - NO EIGNR field in BEWOHNER!",
                "sql": "SELECT * FROM WOHNUNG W LEFT JOIN BEWOHNER B ON W.ONR = B.ONR AND W.ENR = B.ENR WHERE B.KNR IS NULL"
            }
        },
        "common_queries": {
            "all_tenants": "SELECT MIETERNR, BNAME, BSTR, BPLZORT, Z1 as KALTMIETE FROM BEWOHNER",
            "all_owners": "SELECT EIGNR, ENAME, ESTR, EPLZORT FROM EIGADR",
            "vacant_apartments": "SELECT W.* FROM WOHNUNG W LEFT JOIN BEWOHNER B ON W.ONR = B.ONR AND W.ENR = B.ENR WHERE B.KNR IS NULL",
            "total_cold_rent": "SELECT SUM(Z1) as TOTAL_KALTMIETE FROM BEWOHNER",
            "properties_with_units": "SELECT O.ONR, O.OBEZ, COUNT(W.ENR) as UNIT_COUNT FROM OBJEKTE O LEFT JOIN WOHNUNG W ON O.ONR = W.ONR GROUP BY O.ONR, O.OBEZ"
        }
    }
    
    return mappings

def update_knowledge_base(mappings):
    """Update knowledge base files with correct schema"""
    kb_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'knowledge_base')
    
    # Save schema mappings
    schema_file = os.path.join(kb_dir, 'schema_mappings.json')
    with open(schema_file, 'w') as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)
    logger.info(f"Created schema mappings: {schema_file}")
    
    # Update business vocabulary with critical terms
    vocab_file = os.path.join(kb_dir, 'business_vocabulary.json')
    if os.path.exists(vocab_file):
        with open(vocab_file, 'r') as f:
            vocab = json.load(f)
        
        # Add critical schema corrections
        vocab['_schema_critical'] = {
            "bewohner_not_tenants": {
                "correct": "BEWOHNER",
                "wrong": ["TENANTS", "TENANT"],
                "sql_hint": "FROM BEWOHNER"
            },
            "eigadr_not_owners": {
                "correct": "EIGADR", 
                "wrong": ["OWNERS", "OWNER"],
                "sql_hint": "FROM EIGADR"
            },
            "z1_is_kaltmiete": {
                "correct": "Z1",
                "wrong": ["KALTMIETE field"],
                "sql_hint": "SELECT Z1 as KALTMIETE FROM BEWOHNER"
            },
            "no_eignr_in_bewohner": {
                "correct": "BEWOHNER has no EIGNR field",
                "wrong": ["WHERE EIGNR = -1", "WHERE EIGNR > -1"],
                "sql_hint": "Use LEFT JOIN to detect vacancy, not EIGNR"
            }
        }
        
        with open(vocab_file, 'w') as f:
            json.dump(vocab, f, indent=2, ensure_ascii=False)
        logger.info(f"Updated business vocabulary with schema corrections")
    
    # Create SQL template corrections
    template_corrections = {
        "metadata": {
            "created": datetime.now().isoformat(),
            "purpose": "SQL template corrections for common mistakes"
        },
        "corrections": [
            {
                "wrong_pattern": "FROM OWNERS",
                "correct_pattern": "FROM EIGADR",
                "description": "OWNERS table doesn't exist"
            },
            {
                "wrong_pattern": "FROM TENANTS", 
                "correct_pattern": "FROM BEWOHNER",
                "description": "TENANTS table doesn't exist"
            },
            {
                "wrong_pattern": "WHERE EIGNR = -1",
                "correct_pattern": "LEFT JOIN BEWOHNER B ON W.ONR = B.ONR AND W.ENR = B.ENR WHERE B.KNR IS NULL",
                "description": "BEWOHNER has no EIGNR field, use LEFT JOIN for vacancy"
            },
            {
                "wrong_pattern": "SELECT.*KALTMIETE.*FROM",
                "correct_pattern": "SELECT Z1 as KALTMIETE FROM",
                "description": "KALTMIETE is not a field name, use Z1"
            }
        ]
    }
    
    corrections_file = os.path.join(kb_dir, 'sql_template_corrections.json')
    with open(corrections_file, 'w') as f:
        json.dump(template_corrections, f, indent=2)
    logger.info(f"Created SQL template corrections: {corrections_file}")
    
    return True

def main():
    """Main function"""
    logger.info("Starting knowledge base schema update...")
    
    try:
        # Load schema
        critical_schema, complete_tables = load_schema_info()
        logger.info("Loaded schema information")
        
        # Create mappings
        mappings = create_schema_mappings(critical_schema, complete_tables)
        logger.info("Created schema mappings")
        
        # Update knowledge base
        update_knowledge_base(mappings)
        
        print("\n" + "="*60)
        print("KNOWLEDGE BASE SCHEMA UPDATE COMPLETE")
        print("="*60)
        print("\nFiles created/updated:")
        print("- data/knowledge_base/schema_mappings.json")
        print("- data/knowledge_base/business_vocabulary.json")
        print("- data/knowledge_base/sql_template_corrections.json")
        print("\nKey corrections added:")
        print("- BEWOHNER not TENANTS")
        print("- EIGADR not OWNERS")
        print("- Z1 not KALTMIETE field")
        print("- No EIGNR in BEWOHNER table")
        print("- Vacancy detection via LEFT JOIN")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Failed to update knowledge base: {e}")
        raise

if __name__ == "__main__":
    main()