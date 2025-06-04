"""
Business Glossar Implementation for WINCASA Property Management System

This module provides rule-based mappings between business terms and SQL conditions,
implementing the business glossar component from the 5-Step JOIN-Enhanced Architecture.

The business glossar serves as a domain-specific dictionary that translates natural
language business terms into specific SQL patterns and table relationships.
"""

import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from langchain_core.documents import Document


class TermCategory(Enum):
    """Categories for business terms to organize glossar entries."""
    PEOPLE = "people"
    PROPERTY = "property"
    FINANCIAL = "financial"
    STATUS = "status"
    LOCATION = "location"
    TIME = "time"


@dataclass
class BusinessTerm:
    """Represents a business term with its SQL mapping and metadata."""
    term: str
    category: TermCategory
    sql_pattern: str
    tables_involved: List[str]
    description: str
    aliases: List[str] = None
    examples: List[str] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.examples is None:
            self.examples = []


class BusinessGlossar:
    """
    Central business glossar for WINCASA property management system.
    
    Maps natural language business terms to SQL patterns and provides
    context-aware term resolution with fuzzy matching capabilities.
    """
    
    def __init__(self):
        self.terms: Dict[str, BusinessTerm] = {}
        self.aliases_map: Dict[str, str] = {}  # alias -> canonical term
        self._initialize_wincasa_terms()
    
    def _initialize_wincasa_terms(self):
        """Initialize the business glossar with WINCASA-specific terms."""
        
        # PEOPLE TERMS
        people_terms = [
            BusinessTerm(
                term="Mieter",
                category=TermCategory.PEOPLE,
                sql_pattern="BEWOHNER WHERE VBEGINN IS NOT NULL AND (VENDE IS NULL OR VENDE > CURRENT_DATE)",
                tables_involved=["BEWOHNER"],
                description="Active tenants with valid rental contracts",
                aliases=["Bewohner", "Mieterin", "Bewohnerin", "Pächter"],
                examples=["Wer sind die aktuellen Mieter?", "Zeige mir alle Bewohner"]
            ),
            BusinessTerm(
                term="Eigentümer",
                category=TermCategory.PEOPLE,
                sql_pattern="EIGENTUEMER E JOIN VEREIG V ON E.EIGNR = V.EIGNR",
                tables_involved=["EIGENTUEMER", "VEREIG"],
                description="Property owners with their ownership shares",
                aliases=["Besitzer", "Eigentümerin", "Inhaber"],
                examples=["Welche Eigentümer gibt es?", "Zeige mir die Besitzer"]
            ),
            BusinessTerm(
                term="Verwalter",
                category=TermCategory.PEOPLE,
                sql_pattern="VERWALTER WHERE AKTIV = 'J'",
                tables_involved=["VERWALTER"],
                description="Active property managers",
                aliases=["Hausverwaltung", "Manager", "Verwaltern"],
                examples=["Wer ist der zuständige Verwalter?"]
            ),
        ]
        
        # PROPERTY TERMS
        property_terms = [
            BusinessTerm(
                term="Wohnung",
                category=TermCategory.PROPERTY,
                sql_pattern="WOHNUNG W JOIN OBJEKTE O ON W.ONR = O.ONR",
                tables_involved=["WOHNUNG", "OBJEKTE"],
                description="Individual residential units within properties",
                aliases=["Apartment", "Einheit", "Wohneinheit", "Unit"],
                examples=["Wie viele Wohnungen gibt es?", "Zeige alle Einheiten"]
            ),
            BusinessTerm(
                term="Objekt",
                category=TermCategory.PROPERTY,
                sql_pattern="OBJEKTE",
                tables_involved=["OBJEKTE"],
                description="Properties and buildings managed in the system",
                aliases=["Gebäude", "Immobilie", "Haus", "Liegenschaft"],
                examples=["Welche Objekte werden verwaltet?", "Zeige mir alle Gebäude"]
            ),
            BusinessTerm(
                term="Leerstand",
                category=TermCategory.PROPERTY,
                sql_pattern="WOHNUNG W LEFT JOIN BEWOHNER B ON W.ONR = B.ONR WHERE B.ONR IS NULL OR B.VENDE < CURRENT_DATE",
                tables_involved=["WOHNUNG", "BEWOHNER"],
                description="Vacant units without active tenants",
                aliases=["leer", "unvermietete", "freie Wohnung"],
                examples=["Welche Wohnungen stehen leer?", "Zeige freie Einheiten"]
            ),
        ]
        
        # FINANCIAL TERMS
        financial_terms = [
            BusinessTerm(
                term="Kredit",
                category=TermCategory.FINANCIAL,
                sql_pattern="SOLLSTELLUNG WHERE ARTBEZ LIKE '%KREDIT%' AND BETRAG > 0",
                tables_involved=["SOLLSTELLUNG"],
                description="Credit entries and loan obligations",
                aliases=["Darlehen", "Schulden", "Verbindlichkeiten"],
                examples=["Welche Kredite bestehen?", "Zeige offene Darlehen"]
            ),
            BusinessTerm(
                term="Miete",
                category=TermCategory.FINANCIAL,
                sql_pattern="KONTEN K JOIN BEWOHNER B ON K.ONR = B.ONR AND K.KNR = B.KNR WHERE K.KBEZ LIKE '%MIETE%'",
                tables_involved=["KONTEN", "BEWOHNER"],
                description="Rental payments and rent-related accounts",
                aliases=["Mietkosten", "Mieteinnahmen", "Mietgebühr"],
                examples=["Wie hoch ist die Miete?", "Zeige Mieteinnahmen"]
            ),
            BusinessTerm(
                term="Kaution",
                category=TermCategory.FINANCIAL,
                sql_pattern="BEWOHNER WHERE KAUT_VEREINBART > 0 OR KAUT_BEZ_KONTO IS NOT NULL",
                tables_involved=["BEWOHNER"],
                description="Security deposits from tenants",
                aliases=["Sicherheit", "Pfand", "Deposit"],
                examples=["Welche Kautionen wurden hinterlegt?", "Zeige Sicherheitsleistungen"]
            ),
            BusinessTerm(
                term="Nebenkosten",
                category=TermCategory.FINANCIAL,
                sql_pattern="NKMASTER N JOIN NKDETAIL D ON N.ONR = D.ONR",
                tables_involved=["NKMASTER", "NKDETAIL"],
                description="Utility costs and ancillary expenses",
                aliases=["NK", "Betriebskosten", "Utilities", "Zusatzkosten"],
                examples=["Wie hoch sind die Nebenkosten?", "Zeige Betriebskosten"]
            ),
            BusinessTerm(
                term="offene Posten",
                category=TermCategory.FINANCIAL,
                sql_pattern="KONTEN WHERE OPBETRAG > 0",
                tables_involved=["KONTEN"],
                description="Outstanding balances and unpaid amounts",
                aliases=["Schulden", "Außenstände", "unbezahlt"],
                examples=["Welche offenen Posten gibt es?", "Zeige Außenstände"]
            ),
        ]
        
        # STATUS TERMS
        status_terms = [
            BusinessTerm(
                term="aktiv",
                category=TermCategory.STATUS,
                sql_pattern="STATUS = 'AKTIV' OR AKTIV = 'J'",
                tables_involved=[],  # Context-dependent
                description="Active status for various entities",
                aliases=["gültig", "current", "wirksam"],
                examples=["Zeige aktive Verträge", "Welche Mieter sind aktiv?"]
            ),
            BusinessTerm(
                term="gekündigt",
                category=TermCategory.STATUS,
                sql_pattern="VENDE IS NOT NULL AND VENDE <= CURRENT_DATE",
                tables_involved=["BEWOHNER"],
                description="Terminated contracts or ended relationships",
                aliases=["beendet", "ausgelaufen", "terminated"],
                examples=["Welche Verträge wurden gekündigt?", "Zeige beendete Mietverhältnisse"]
            ),
        ]
        
        # LOCATION TERMS
        location_terms = [
            BusinessTerm(
                term="Adresse",
                category=TermCategory.LOCATION,
                sql_pattern="BSTR + ', ' + BPLZORT + CASE WHEN HNRZU IS NOT NULL THEN ' ' + HNRZU ELSE '' END",
                tables_involved=["BEWADR", "EIGADR"],
                description="Complete address formatting for people and properties",
                aliases=["Anschrift", "Wohnort", "Address"],
                examples=["Wie lautet die Adresse?", "Zeige Anschriften"]
            ),
            BusinessTerm(
                term="Straße",
                category=TermCategory.LOCATION,
                sql_pattern="BSTR",
                tables_involved=["BEWADR", "EIGADR", "OBJEKTE"],
                description="Street name and house number",
                aliases=["Street", "Straßenname"],
                examples=["In welcher Straße wohnt der Mieter?"]
            ),
            BusinessTerm(
                term="Stadt",
                category=TermCategory.LOCATION,
                sql_pattern="SUBSTRING(BPLZORT FROM POSITION(' ' IN BPLZORT) + 1)",
                tables_involved=["BEWADR", "EIGADR"],
                description="City name extracted from postal code field",
                aliases=["Ort", "City", "Gemeinde"],
                examples=["In welcher Stadt liegt das Objekt?"]
            ),
        ]
        
        # Register all terms
        all_terms = people_terms + property_terms + financial_terms + status_terms + location_terms
        
        for term in all_terms:
            self.add_term(term)
    
    def add_term(self, term: BusinessTerm):
        """Add a business term to the glossar."""
        # Store the canonical term
        self.terms[term.term.lower()] = term
        
        # Register aliases
        for alias in term.aliases:
            self.aliases_map[alias.lower()] = term.term.lower()
    
    def get_term(self, term: str) -> Optional[BusinessTerm]:
        """Get a business term by name or alias."""
        term_key = term.lower()
        
        # Check direct match
        if term_key in self.terms:
            return self.terms[term_key]
        
        # Check aliases
        if term_key in self.aliases_map:
            canonical = self.aliases_map[term_key]
            return self.terms.get(canonical)
        
        return None
    
    def extract_terms_from_query(self, query: str) -> List[Tuple[str, BusinessTerm]]:
        """
        Extract business terms from a natural language query.
        
        Returns:
            List of tuples (matched_text, BusinessTerm)
        """
        found_terms = []
        query_lower = query.lower()
        
        # Check for direct term matches
        for term_name, term in self.terms.items():
            if term_name in query_lower:
                found_terms.append((term_name, term))
        
        # Check for alias matches
        for alias, canonical in self.aliases_map.items():
            if alias in query_lower:
                term = self.terms[canonical]
                found_terms.append((alias, term))
        
        # Sort by length of match (longer matches first)
        found_terms.sort(key=lambda x: len(x[0]), reverse=True)
        
        return found_terms
    
    def fuzzy_match_terms(self, query: str, threshold: float = 0.7) -> List[Tuple[str, BusinessTerm, float]]:
        """
        Find business terms using fuzzy matching.
        
        Args:
            query: Search query
            threshold: Minimum similarity score (0.0 to 1.0)
            
        Returns:
            List of tuples (matched_term, BusinessTerm, similarity_score)
        """
        import difflib
        
        matches = []
        query_words = query.lower().split()
        
        # Check all terms and aliases
        all_terms = []
        for term_name, term in self.terms.items():
            all_terms.append((term_name, term))
            for alias in term.aliases:
                all_terms.append((alias.lower(), term))
        
        for term_name, term in all_terms:
            # Calculate similarity for each word in the query
            for word in query_words:
                similarity = difflib.SequenceMatcher(None, word, term_name).ratio()
                if similarity >= threshold:
                    matches.append((term_name, term, similarity))
        
        # Remove duplicates and sort by similarity
        seen = set()
        unique_matches = []
        for match in sorted(matches, key=lambda x: x[2], reverse=True):
            key = (match[0], match[1].term)
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        return unique_matches
    
    def resolve_terms_to_sql(self, terms: List[BusinessTerm], query_context: str = "") -> Dict[str, any]:
        """
        Convert resolved business terms into SQL patterns and table information.
        
        Args:
            terms: List of resolved business terms
            query_context: Original query for additional context
            
        Returns:
            Dictionary with SQL patterns, tables, and mappings
        """
        result = {
            "sql_patterns": [],
            "tables_involved": set(),
            "category_mappings": {},
            "term_mappings": {},
            "join_hints": [],
        }
        
        for term in terms:
            result["sql_patterns"].append({
                "term": term.term,
                "pattern": term.sql_pattern,
                "description": term.description
            })
            
            result["tables_involved"].update(term.tables_involved)
            
            if term.category.value not in result["category_mappings"]:
                result["category_mappings"][term.category.value] = []
            result["category_mappings"][term.category.value].append(term.term)
            
            result["term_mappings"][term.term] = {
                "sql": term.sql_pattern,
                "tables": term.tables_involved,
                "category": term.category.value
            }
        
        # Generate JOIN hints based on table combinations
        result["join_hints"] = self._generate_join_hints(result["tables_involved"])
        
        return result
    
    def _generate_join_hints(self, tables: Set[str]) -> List[str]:
        """Generate JOIN hints based on common table relationships."""
        join_hints = []
        tables_list = list(tables)
        
        # Common JOIN patterns in WINCASA
        join_patterns = {
            ("BEWOHNER", "BEWADR"): "BEWOHNER.BEWNR = BEWADR.BEWNR",
            ("EIGENTUEMER", "EIGADR"): "EIGENTUEMER.EIGNR = EIGADR.EIGNR",
            ("EIGENTUEMER", "VEREIG"): "EIGENTUEMER.EIGNR = VEREIG.EIGNR",
            ("VEREIG", "OBJEKTE"): "VEREIG.ONR = OBJEKTE.ONR",
            ("BEWOHNER", "KONTEN"): "BEWOHNER.ONR = KONTEN.ONR AND BEWOHNER.KNR = KONTEN.KNR",
            ("OBJEKTE", "WOHNUNG"): "OBJEKTE.ONR = WOHNUNG.ONR",
            ("OBJEKTE", "KONTEN"): "OBJEKTE.ONR = KONTEN.ONR",
            ("NKMASTER", "NKDETAIL"): "NKMASTER.ONR = NKDETAIL.ONR",
        }
        
        # Find applicable JOIN patterns
        for (table1, table2), join_condition in join_patterns.items():
            if table1 in tables and table2 in tables:
                join_hints.append(f"JOIN {table2} ON {join_condition}")
        
        return join_hints
    
    def get_enhanced_context_for_terms(self, terms: List[BusinessTerm]) -> List[Document]:
        """
        Generate enhanced context documents for resolved business terms.
        
        Args:
            terms: List of resolved business terms
            
        Returns:
            List of LangChain Document objects with business context
        """
        documents = []
        
        for term in terms:
            # Create a context document for each term
            content = f"""
Business Term: {term.term}
Category: {term.category.value}
Description: {term.description}

SQL Pattern: {term.sql_pattern}
Tables Involved: {', '.join(term.tables_involved)}

Aliases: {', '.join(term.aliases) if term.aliases else 'None'}

Examples:
{chr(10).join(f'- {example}' for example in term.examples)}

Usage Context:
This term should be used when queries involve {term.description.lower()}. 
The SQL pattern can be integrated into WHERE clauses or used as subqueries.
            """.strip()
            
            metadata = {
                "source": "business_glossar",
                "term": term.term,
                "category": term.category.value,
                "tables": term.tables_involved,
                "type": "business_term_definition"
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def create_glossar_prompt_section(self, resolved_terms: List[BusinessTerm]) -> str:
        """
        Create a formatted prompt section with resolved business terms.
        
        Args:
            resolved_terms: List of business terms found in the query
            
        Returns:
            Formatted string for inclusion in LLM prompts
        """
        if not resolved_terms:
            return ""
        
        sections = ["=== BUSINESS GLOSSAR MAPPINGS ==="]
        
        for term in resolved_terms:
            sections.append(f"• {term.term.upper()}: {term.description}")
            sections.append(f"  SQL Pattern: {term.sql_pattern}")
            sections.append(f"  Tables: {', '.join(term.tables_involved)}")
            if term.aliases:
                sections.append(f"  Aliases: {', '.join(term.aliases)}")
            sections.append("")
        
        sections.append("=== END BUSINESS GLOSSAR ===")
        
        return "\n".join(sections)


def extract_business_entities(query: str, glossar: BusinessGlossar) -> Dict[str, any]:
    """
    Extract business entities from a natural language query using the business glossar.
    
    This function serves as the main interface for the business glossar module,
    providing entity extraction capabilities for the LangGraph workflow.
    
    Args:
        query: Natural language query from user
        glossar: BusinessGlossar instance
        
    Returns:
        Dictionary with extracted terms, SQL patterns, and context
    """
    # Direct term extraction
    direct_matches = glossar.extract_terms_from_query(query)
    
    # Fuzzy matching for partial matches
    fuzzy_matches = glossar.fuzzy_match_terms(query, threshold=0.6)
    
    # Combine results (prioritize direct matches)
    all_terms = []
    seen_terms = set()
    
    # Add direct matches first
    for matched_text, term in direct_matches:
        if term.term not in seen_terms:
            all_terms.append(term)
            seen_terms.add(term.term)
    
    # Add fuzzy matches if not already included
    for matched_text, term, score in fuzzy_matches:
        if term.term not in seen_terms:
            all_terms.append(term)
            seen_terms.add(term.term)
    
    # Resolve terms to SQL patterns
    sql_resolution = glossar.resolve_terms_to_sql(all_terms, query)
    
    # Generate enhanced context documents
    context_documents = glossar.get_enhanced_context_for_terms(all_terms)
    
    return {
        "query": query,
        "extracted_terms": [term.term for term in all_terms],
        "business_terms": all_terms,
        "sql_patterns": sql_resolution["sql_patterns"],
        "tables_involved": list(sql_resolution["tables_involved"]),
        "join_hints": sql_resolution["join_hints"],
        "category_mappings": sql_resolution["category_mappings"],
        "context_documents": context_documents,
        "prompt_section": glossar.create_glossar_prompt_section(all_terms),
        "direct_matches": len(direct_matches),
        "fuzzy_matches": len(fuzzy_matches)
    }


# Global instance for use throughout the application
WINCASA_GLOSSAR = BusinessGlossar()


if __name__ == "__main__":
    # Demo usage
    glossar = BusinessGlossar()
    
    # Test queries
    test_queries = [
        "Wer wohnt in der Marienstraße 26?",
        "Welche Eigentümer haben offene Posten?",
        "Zeige mir alle leerstehenden Wohnungen",
        "Wie hoch sind die Nebenkosten für Mieter?",
        "Welche Kautionen wurden von Bewohnern hinterlegt?"
    ]
    
    print("=== BUSINESS GLOSSAR DEMO ===\n")
    
    for query in test_queries:
        print(f"Query: {query}")
        result = extract_business_entities(query, glossar)
        
        print(f"Found {len(result['extracted_terms'])} terms: {', '.join(result['extracted_terms'])}")
        print(f"Tables involved: {', '.join(result['tables_involved'])}")
        print(f"JOIN hints: {len(result['join_hints'])}")
        print(f"Direct matches: {result['direct_matches']}, Fuzzy matches: {result['fuzzy_matches']}")
        print("-" * 60)