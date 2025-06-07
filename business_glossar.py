#!/usr/bin/env python3
"""
Business Glossar Module - WINCASA Domain Knowledge
Provides business term mapping and entity extraction for WINCASA queries.
"""

from typing import Dict, List, Set, Any
import re
from dataclasses import dataclass

@dataclass
class BusinessTerm:
    """Represents a business term with its technical mapping."""
    term: str
    synonyms: List[str]
    tables: List[str]
    category: str
    sql_patterns: List[str]

# WINCASA Business Glossar - Essential HV domain knowledge
WINCASA_GLOSSAR = {
    "residents": BusinessTerm(
        term="bewohner",
        synonyms=["mieter", "residents", "tenants", "person", "personen"],
        tables=["BEWOHNER", "OBJEKTE", "WOHNUNG"],
        category="people",
        sql_patterns=["SELECT * FROM BEWOHNER", "BEWOHNER.ONR = OBJEKTE.ONR"]
    ),
    "owners": BusinessTerm(
        term="eigentümer",
        synonyms=["vermieter", "besitzer", "owners", "landlord"],
        tables=["EIGENTUEMER", "VEREIG", "OBJEKTE"],
        category="people", 
        sql_patterns=["SELECT * FROM EIGENTUEMER", "EIGENTUEMER.ENR = VEREIG.ENR"]
    ),
    "properties": BusinessTerm(
        term="objekte",
        synonyms=["immobilien", "gebäude", "properties", "buildings", "häuser"],
        tables=["OBJEKTE", "WOHNUNG"],
        category="property",
        sql_patterns=["SELECT * FROM OBJEKTE", "OBJEKTE.ONR = WOHNUNG.ONR"]
    ),
    "apartments": BusinessTerm(
        term="wohnungen",
        synonyms=["einheiten", "apartments", "units", "whg"],
        tables=["WOHNUNG", "OBJEKTE", "BEWOHNER"],
        category="property",
        sql_patterns=["SELECT * FROM WOHNUNG", "WOHNUNG.ONR = OBJEKTE.ONR"]
    ),
    "addresses": BusinessTerm(
        term="adressen",
        synonyms=["straße", "adresse", "addresses", "street", "strasse"],
        tables=["BEWOHNER", "OBJEKTE"],
        category="location",
        sql_patterns=["BEWOHNER.BSTR LIKE", "OBJEKTE.OSTR LIKE"]
    ),
    "financial": BusinessTerm(
        term="finanzen",
        synonyms=["geld", "kosten", "miete", "nebenkosten", "financial", "costs"],
        tables=["KONTEN", "BUCHUNG", "SOLLSTELLUNG"],
        category="financial",
        sql_patterns=["SELECT * FROM KONTEN", "KONTEN.ONR = BUCHUNG.ONR"]
    )
}

class BusinessGlossar:
    """Business glossar for WINCASA domain knowledge."""
    
    def __init__(self):
        self.glossar = WINCASA_GLOSSAR
    
    def extract_entities(self, query: str) -> List[str]:
        """Extract business entities from query."""
        entities = []
        query_lower = query.lower()
        
        for term_key, term_data in self.glossar.items():
            # Check main term
            if term_data.term in query_lower:
                entities.append(term_data.term)
            
            # Check synonyms
            for synonym in term_data.synonyms:
                if synonym in query_lower:
                    entities.append(term_data.term)
                    break
        
        return list(set(entities))
    
    def get_relevant_tables(self, entities: List[str]) -> List[str]:
        """Get relevant tables for detected entities."""
        tables = set()
        
        for entity in entities:
            for term_key, term_data in self.glossar.items():
                if term_data.term == entity:
                    tables.update(term_data.tables)
        
        return list(tables)

def extract_business_entities(query: str, glossar: Dict = None) -> Dict[str, Any]:
    """
    Extract business entities from a query using the WINCASA glossar.
    
    Args:
        query: Natural language query
        glossar: Business glossar dictionary (uses WINCASA_GLOSSAR if None)
        
    Returns:
        Dictionary with extracted terms, categories, tables, and SQL patterns
    """
    if glossar is None:
        glossar = WINCASA_GLOSSAR
    
    query_lower = query.lower()
    extracted_terms = []
    category_mappings = {}
    tables_involved = set()
    sql_patterns = []
    direct_matches = 0
    fuzzy_matches = 0
    join_hints = []
    
    # Extract entities using the business glossar
    for term_key, term_data in glossar.items():
        # Check main term
        if term_data.term in query_lower:
            extracted_terms.append(term_data.term)
            category_mappings[term_data.category] = category_mappings.get(term_data.category, [])
            category_mappings[term_data.category].append(term_data.term)
            tables_involved.update(term_data.tables)
            sql_patterns.extend(term_data.sql_patterns)
            direct_matches += 1
            continue
        
        # Check synonyms
        for synonym in term_data.synonyms:
            if synonym in query_lower:
                extracted_terms.append(term_data.term)
                category_mappings[term_data.category] = category_mappings.get(term_data.category, [])
                category_mappings[term_data.category].append(term_data.term)
                tables_involved.update(term_data.tables)
                sql_patterns.extend(term_data.sql_patterns)
                fuzzy_matches += 1
                break
    
    # Generate JOIN hints for multi-table queries
    tables_list = list(tables_involved)
    if len(tables_list) > 1:
        # Common WINCASA joins
        if "BEWOHNER" in tables_list and "OBJEKTE" in tables_list:
            join_hints.append("BEWOHNER.ONR = OBJEKTE.ONR")
        if "EIGENTUEMER" in tables_list and "VEREIG" in tables_list:
            join_hints.append("EIGENTUEMER.ENR = VEREIG.ENR")
        if "WOHNUNG" in tables_list and "OBJEKTE" in tables_list:
            join_hints.append("WOHNUNG.ONR = OBJEKTE.ONR")
    
    return {
        "extracted_terms": list(set(extracted_terms)),
        "category_mappings": category_mappings,
        "tables_involved": list(tables_involved),
        "sql_patterns": list(set(sql_patterns)),
        "join_hints": join_hints,
        "direct_matches": direct_matches,
        "fuzzy_matches": fuzzy_matches
    }

# Export for backward compatibility
__all__ = [
    'WINCASA_GLOSSAR',
    'BusinessGlossar', 
    'extract_business_entities',
    'BusinessTerm'
]