"""
Global Context Definition for WINCASA Database System

This module provides a structured global context that contains essential database
information to be included with every LLM query. This implements the hybrid
context strategy from implementation_plan.md.
"""

GLOBAL_CONTEXT = {
    "system_description": """
WINCASA is a property management database system for real estate administration.
The database contains information about apartments, residents, owners, financial accounts, and property management operations.
Total: 151 tables, 517 apartments, 698 residents.
""",
    
    "core_entities": {
        "people": {
            "BEWOHNER": "Residents/tenants living in properties",
            "EIGENTUEMER": "Property owners",
            "BEWADR": "Resident address details", 
            "EIGADR": "Owner address details"
        },
        "properties": {
            "OBJEKTE": "Main property/building objects (ONR = Object Number)",
            "WOHNUNG": "Individual apartments/units within properties",
            "LIEGEN": "Land/lot information"
        },
        "financial": {
            "KONTEN": "Financial accounts (55 connections - central hub table)",
            "BUCHUNG": "Financial transactions and bookings",
            "SOLLSTELLUNG": "Outstanding balances/receivables",
            "BANKEN": "Bank account information"
        },
        "management": {
            "VERWALTER": "Property managers",
            "SEVERTRAG": "Service contracts",
            "NACHWEIS": "Documents and evidence records"
        }
    },
    
    "key_relationships": {
        # Core navigation paths for common queries
        "resident_to_property": "BEWOHNER.ONR → OBJEKTE.ONR (BWO = Object Number)",
        "owner_to_property": "EIGENTUEMER.ONR → OBJEKTE.ONR via VEREIG table",
        "property_to_accounts": "OBJEKTE.ONR → KONTEN.ONR → KONTEN.KNR",
        "accounts_to_transactions": "KONTEN.KNR → BUCHUNG.KSOLL/KHABEN",
        "residents_to_addresses": "BEWOHNER.BEWNR → BEWADR.BEWNR",
        "owners_to_addresses": "EIGENTUEMER.EIGNR → EIGADR.EIGNR"
    },
    
    "critical_patterns": {
        "address_search": {
            "description": "Finding people by address",
            "tables": ["BEWOHNER", "BEWADR", "OBJEKTE"],
            "key_fields": ["BSTR (street)", "BPLZORT (postal code + city)", "HNRZU (house number)"]
        },
        "financial_lookup": {
            "description": "Financial queries and account management", 
            "path": "OBJEKTE → KONTEN → BUCHUNG → SOLLSTELLUNG",
            "key_fields": ["ONR (object)", "KNR (account)", "BETRAG (amount)", "DATUM (date)"]
        },
        "owner_property_relations": {
            "description": "Owner-property relationships",
            "path": "EIGENTUEMER → VEREIG → OBJEKTE",
            "key_fields": ["EIGNR", "ONR", "ANTEIL (ownership share)"]
        },
        "resident_queries": {
            "description": "Resident information and apartment assignments",
            "tables": ["BEWOHNER", "BEWADR", "OBJEKTE", "WOHNUNG"], 
            "key_fields": ["BEWNR", "ONR", "WOHNR", "NAME", "VORNAME"]
        }
    },
    
    "database_specifics": {
        "primary_keys": {
            "OBJEKTE": "ONR (Object Number) - Central identifier for properties",
            "BEWOHNER": "BEWNR (Resident Number)",
            "EIGENTUEMER": "EIGNR (Owner Number)", 
            "KONTEN": "Composite: ONR + KNR (Object + Account Number)",
            "BUCHUNG": "BNR (Booking Number)"
        },
        "important_fields": {
            "address_components": ["BSTR", "BPLZORT", "HNRZU", "HNRVON", "HNRBIS"],
            "name_fields": ["NAME", "VORNAME", "TITEL"],
            "financial_fields": ["BETRAG", "DATUM", "VERWENDUNG", "BELEGNR"],
            "status_fields": ["STATUS", "TYP", "ART"]
        },
        "common_constraints": [
            "Most tables connect via ONR (Object Number)",
            "KONTEN is the central hub with 55 connections",
            "Address information split between main tables and ADR tables",
            "Financial data flows: OBJEKTE → KONTEN → BUCHUNG"
        ]
    },
    
    "query_guidance": {
        "address_queries": "Use BEWOHNER + BEWADR for resident addresses, EIGENTUEMER + EIGADR for owner addresses",
        "counting_properties": "Count OBJEKTE for buildings, WOHNUNG for individual units", 
        "financial_data": "Start with KONTEN, join to BUCHUNG for transactions",
        "ownership_info": "Use VEREIG to connect EIGENTUEMER to OBJEKTE",
        "date_filtering": "Most date fields are DATUM, some tables have GUELTIGAB/GUELTIGBIS"
    }
}

def get_global_context_prompt():
    """
    Generate the global context as a formatted prompt section.
    This should be included in every LLM query to provide baseline understanding.
    """
    context_lines = []
    
    context_lines.append("=== WINCASA DATABASE GLOBAL CONTEXT ===")
    context_lines.append(GLOBAL_CONTEXT["system_description"].strip())
    context_lines.append("")
    
    context_lines.append("CORE ENTITIES:")
    for category, entities in GLOBAL_CONTEXT["core_entities"].items():
        context_lines.append(f"• {category.upper()}:")
        for table, desc in entities.items():
            context_lines.append(f"  - {table}: {desc}")
    context_lines.append("")
    
    context_lines.append("KEY RELATIONSHIPS:")
    for relationship, description in GLOBAL_CONTEXT["key_relationships"].items():
        context_lines.append(f"• {description}")
    context_lines.append("")
    
    context_lines.append("QUERY PATTERNS:")
    for pattern, info in GLOBAL_CONTEXT["critical_patterns"].items():
        context_lines.append(f"• {info['description']}")
        if 'path' in info:
            context_lines.append(f"  Path: {info['path']}")
        if 'tables' in info:
            context_lines.append(f"  Tables: {', '.join(info['tables'])}")
        if 'key_fields' in info:
            context_lines.append(f"  Key fields: {', '.join(info['key_fields'])}")
    context_lines.append("")
    
    context_lines.append("IMPORTANT DATABASE SPECIFICS:")
    context_lines.append("• Primary Keys:")
    for table, key_info in GLOBAL_CONTEXT["database_specifics"]["primary_keys"].items():
        context_lines.append(f"  - {table}: {key_info}")
    context_lines.append("• Common Constraints:")
    for constraint in GLOBAL_CONTEXT["database_specifics"]["common_constraints"]:
        context_lines.append(f"  - {constraint}")
    context_lines.append("")
    
    context_lines.append("QUERY GUIDANCE:")
    for query_type, guidance in GLOBAL_CONTEXT["query_guidance"].items():
        context_lines.append(f"• {query_type}: {guidance}")
    
    context_lines.append("=== END GLOBAL CONTEXT ===")
    context_lines.append("")
    
    return "\n".join(context_lines)

def get_compact_global_context():
    """
    Get a more compact version of the global context for token-conscious scenarios.
    """
    compact = f"""=== WINCASA DB CONTEXT ===
Property management system: 151 tables, 517 apartments, 698 residents

CORE TABLES & RELATIONSHIPS:
• BEWOHNER (residents) → BEWADR (addresses) 
• EIGENTUEMER (owners) → EIGADR (addresses)
• OBJEKTE (properties, ONR=key) → WOHNUNG (units)
• KONTEN (accounts, 55 connections) → BUCHUNG (transactions)
• VEREIG connects owners to properties

KEY PATTERNS:
• Address search: BEWOHNER.BEWNR → BEWADR, fields BSTR/BPLZORT/HNRZU
• Financial: OBJEKTE.ONR → KONTEN → BUCHUNG, key fields BETRAG/DATUM
• Ownership: EIGENTUEMER.EIGNR → VEREIG → OBJEKTE.ONR

NAVIGATION: Most tables link via ONR (Object Number). KONTEN is central hub.
=== END CONTEXT ===
"""
    return compact

if __name__ == "__main__":
    print("Full Global Context:")
    print(get_global_context_prompt())
    print("\n" + "="*80 + "\n")
    print("Compact Global Context:")
    print(get_compact_global_context())