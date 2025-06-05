#!/usr/bin/env python3
"""
Adaptive TAG Synthesizer - Enhanced Query Processing with ML Classification

Replaces the rule-based TAG synthesizer with ML-powered classification
and dynamic schema discovery.

Key improvements:
1. ML-based query classification via AdaptiveTAGClassifier
2. Dynamic schema discovery and relationship mapping
3. Extended query type coverage (10+ types)
4. Learning from successful query patterns
5. Confidence-based fallback strategies
"""

import logging
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from adaptive_tag_classifier import AdaptiveTAGClassifier, ClassificationResult

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveSynthesisResult:
    """Enhanced synthesis result with ML classification info"""
    sql: str
    query_type: str
    entities: List[str]
    schema_context: Dict[str, Any]
    confidence: float
    reasoning: str
    alternatives: List[Tuple[str, float]]
    dynamic_tables: List[str]
    relationship_map: Dict[str, List[str]]


class DynamicSchemaDiscovery:
    """
    Dynamic schema discovery system that learns table relationships
    and patterns from successful queries.
    """
    
    def __init__(self, schema_info: Dict[str, Any]):
        """
        Initialize with base schema information.
        
        Args:
            schema_info: Basic schema information with table names
        """
        self.base_schema = schema_info
        self.available_tables = list(schema_info.get("tables", {}).keys())
        
        # Dynamic relationship mapping
        self.table_relationships: Dict[str, List[str]] = {}
        self.query_patterns: Dict[str, List[str]] = {}
        
        # Load existing patterns if available
        self._load_discovered_patterns()
    
    def _load_discovered_patterns(self):
        """Load previously discovered patterns"""
        pattern_file = Path("models/schema_patterns.json")
        if pattern_file.exists():
            try:
                with open(pattern_file, 'r') as f:
                    data = json.load(f)
                    self.table_relationships = data.get("relationships", {})
                    self.query_patterns = data.get("patterns", {})
                logger.info("Loaded schema discovery patterns")
            except Exception as e:
                logger.warning(f"Could not load schema patterns: {e}")
    
    def discover_relevant_tables(self, query_type: str, entities: List[str]) -> List[str]:
        """
        Discover relevant tables for a query type and entities.
        
        Args:
            query_type: The classified query type
            entities: Extracted entities from the query
            
        Returns:
            List of relevant table names
        """
        relevant_tables = set()
        
        # Use base mapping from static knowledge
        base_mapping = self._get_base_table_mapping(query_type)
        relevant_tables.update(base_mapping)
        
        # Use learned patterns
        if query_type in self.query_patterns:
            learned_tables = self.query_patterns[query_type]
            relevant_tables.update(learned_tables)
        
        # Entity-based table discovery
        entity_tables = self._discover_tables_from_entities(entities)
        relevant_tables.update(entity_tables)
        
        # Filter to only available tables
        final_tables = [table for table in relevant_tables if table in self.available_tables]
        
        return final_tables
    
    def _get_base_table_mapping(self, query_type: str) -> List[str]:
        """Get base table mapping for query types"""
        base_mappings = {
            "address_lookup": ["BEWOHNER", "BEWADR"],
            "resident_lookup": ["BEWOHNER", "BEWADR"],
            "owner_lookup": ["EIGENTUEMER", "EIGADR", "VEREIG"],
            "property_queries": ["WOHNUNG", "OBJEKTE"],
            "financial_queries": ["KONTEN", "BUCHUNG", "SOLLSTELLUNG"],
            "count_queries": ["WOHNUNG", "BEWOHNER", "OBJEKTE"],
            "relationship_queries": ["BEWOHNER", "EIGENTUEMER", "OBJEKTE", "VEREIG"],
            "temporal_queries": ["BUCHUNG", "SOLLSTELLUNG"],
            "comparison_queries": ["WOHNUNG", "BEWOHNER", "BUCHUNG"],
            "business_logic_queries": ["BEWOHNER", "EIGENTUEMER", "OBJEKTE", "KONTEN"]
        }
        
        return base_mappings.get(query_type, ["BEWOHNER", "OBJEKTE"])  # Default fallback
    
    def _discover_tables_from_entities(self, entities: List[str]) -> List[str]:
        """Discover tables based on extracted entities"""
        discovered_tables = []
        
        for entity in entities:
            entity_lower = entity.lower()
            
            # Address-related entities
            if any(keyword in entity_lower for keyword in ['straße', 'str', 'weg', 'platz']):
                discovered_tables.extend(['BEWOHNER', 'BEWADR', 'EIGADR'])
            
            # Postal code entities
            elif entity.isdigit() and len(entity) == 5:
                discovered_tables.extend(['BEWOHNER', 'EIGENTUEMER'])
            
            # Person name patterns
            elif len(entity.split()) >= 2 and entity[0].isupper():
                discovered_tables.extend(['BEWOHNER', 'EIGENTUEMER'])
            
            # Financial entities
            elif any(keyword in entity_lower for keyword in ['euro', '€', 'miete', 'kosten']):
                discovered_tables.extend(['KONTEN', 'BUCHUNG'])
            
            # Property entities
            elif any(keyword in entity_lower for keyword in ['wohnung', 'objekt', 'gebäude']):
                discovered_tables.extend(['WOHNUNG', 'OBJEKTE'])
        
        return discovered_tables
    
    def learn_from_successful_query(self, query_type: str, used_tables: List[str], sql: str):
        """
        Learn table relationships from successful queries.
        
        Args:
            query_type: The query type that worked
            used_tables: Tables that were used in successful SQL
            sql: The successful SQL query
        """
        # Update query patterns
        if query_type not in self.query_patterns:
            self.query_patterns[query_type] = []
        
        for table in used_tables:
            if table not in self.query_patterns[query_type]:
                self.query_patterns[query_type].append(table)
        
        # Update table relationships by analyzing SQL
        self._analyze_sql_relationships(sql, used_tables)
        
        # Save patterns
        self._save_patterns()
    
    def _analyze_sql_relationships(self, sql: str, tables: List[str]):
        """Analyze SQL to discover table relationships"""
        sql_upper = sql.upper()
        
        # Find JOIN patterns
        for table in tables:
            if table not in self.table_relationships:
                self.table_relationships[table] = []
            
            # Look for tables this one joins with
            for other_table in tables:
                if table != other_table:
                    join_pattern = f"JOIN {other_table}"
                    if join_pattern in sql_upper and other_table not in self.table_relationships[table]:
                        self.table_relationships[table].append(other_table)
    
    def _save_patterns(self):
        """Save discovered patterns to disk"""
        try:
            pattern_file = Path("models/schema_patterns.json")
            pattern_file.parent.mkdir(exist_ok=True)
            
            data = {
                "relationships": self.table_relationships,
                "patterns": self.query_patterns,
                "updated_at": str(logger.info("Saved schema discovery patterns"))
            }
            
            with open(pattern_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save schema patterns: {e}")
    
    def get_table_relationships(self, table_name: str) -> List[str]:
        """Get known relationships for a table"""
        return self.table_relationships.get(table_name, [])


class AdaptiveTAGSynthesizer:
    """
    Enhanced TAG synthesizer with ML classification and dynamic schema discovery.
    
    Replaces static rule-based approach with adaptive learning system.
    """
    
    def __init__(self, schema_info: Dict[str, Any]):
        """
        Initialize adaptive synthesizer.
        
        Args:
            schema_info: Schema information including available tables
        """
        self.schema_info = schema_info
        
        # Initialize ML classifier
        self.classifier = AdaptiveTAGClassifier()
        
        # Initialize dynamic schema discovery
        self.schema_discovery = DynamicSchemaDiscovery(schema_info)
        
        # Enhanced schema contexts with more comprehensive information
        self.enhanced_schemas = self._load_enhanced_schemas()
        
        logger.info("Adaptive TAG synthesizer initialized")
    
    def _load_enhanced_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load enhanced schema contexts for each query type"""
        return {
            "address_lookup": {
                "description": "Find residents by address with flexible pattern matching",
                "primary_tables": ["BEWOHNER"],
                "secondary_tables": ["BEWADR", "OBJEKTE"],
                "key_columns": {
                    "BEWOHNER": {
                        "BWO": "Bewohner ID (Primary Key)",
                        "BSTR": "Straßenname + Hausnummer (z.B. 'Marienstraße 26')",
                        "BPLZORT": "PLZ + Ort (z.B. '45307 Essen')",
                        "BNAME": "Nachname", "BVNAME": "Vorname",
                        "ONR": "Objekt-Nummer (Foreign Key zu OBJEKTE)"
                    }
                },
                "critical_rules": [
                    "ALWAYS use LIKE patterns for addresses",
                    "BSTR format: 'Straßenname Hausnummer'",
                    "BPLZORT format: 'PLZ Ort'",
                    "Use % wildcards for partial matching"
                ],
                "sql_templates": [
                    "SELECT BNAME, BVNAME, BSTR, BPLZORT FROM BEWOHNER WHERE BSTR LIKE '%{street}%'",
                    "SELECT * FROM BEWOHNER WHERE BPLZORT LIKE '%{postal}%'"
                ]
            },
            "resident_lookup": {
                "description": "Find specific residents by name or characteristics",
                "primary_tables": ["BEWOHNER"],
                "secondary_tables": ["BEWADR"],
                "key_columns": {
                    "BEWOHNER": {
                        "BNAME": "Nachname (for name searches)",
                        "BVNAME": "Vorname (for name searches)",
                        "BWO": "Bewohner ID (Primary Key)"
                    }
                },
                "critical_rules": [
                    "Use LIKE for partial name matching",
                    "Consider both BNAME and BVNAME for full names"
                ],
                "sql_templates": [
                    "SELECT * FROM BEWOHNER WHERE BNAME LIKE '%{name}%'",
                    "SELECT * FROM BEWOHNER WHERE BVNAME LIKE '%{firstname}%'"
                ]
            },
            "owner_lookup": {
                "description": "Find property owners with complex relationship handling",
                "primary_tables": ["EIGENTUEMER"],
                "secondary_tables": ["EIGADR", "VEREIG", "OBJEKTE"],
                "key_columns": {
                    "EIGENTUEMER": {"ENR": "Eigentümer ID", "ENAME": "Name", "EVNAME": "Vorname"},
                    "VEREIG": {"ENR": "Eigentümer ID (FK)", "ONR": "Objekt ID (FK)"},
                    "EIGADR": {"ENR": "Eigentümer ID (FK)", "ESTR": "Straße", "EPLZORT": "PLZ+Ort"}
                },
                "critical_rules": [
                    "JOIN EIGENTUEMER with VEREIG for property relationships",
                    "JOIN with EIGADR for owner addresses",
                    "Use ONR to link to properties"
                ],
                "sql_templates": [
                    "SELECT E.ENAME, E.EVNAME FROM EIGENTUEMER E",
                    "SELECT E.* FROM EIGENTUEMER E JOIN VEREIG V ON E.ENR = V.ENR WHERE V.ONR = {property}"
                ]
            },
            "property_queries": {
                "description": "Apartment and building information with counts and details",
                "primary_tables": ["WOHNUNG", "OBJEKTE"],
                "secondary_tables": ["BEWOHNER"],
                "key_columns": {
                    "WOHNUNG": {"WNR": "Wohnung ID", "ONR": "Objekt ID (FK)", "WBEZEICHNUNG": "Bezeichnung"},
                    "OBJEKTE": {"ONR": "Objekt ID", "OBEZEICHNUNG": "Bezeichnung", "OSTR": "Straße"}
                },
                "critical_rules": [
                    "Use COUNT(*) for total counts",
                    "JOIN WOHNUNG with OBJEKTE via ONR for building details"
                ],
                "sql_templates": [
                    "SELECT COUNT(*) FROM WOHNUNG",
                    "SELECT W.*, O.OBEZEICHNUNG FROM WOHNUNG W JOIN OBJEKTE O ON W.ONR = O.ONR"
                ]
            },
            "financial_queries": {
                "description": "Financial data including rent, costs, and calculations",
                "primary_tables": ["KONTEN", "BUCHUNG"],
                "secondary_tables": ["SOLLSTELLUNG"],
                "key_columns": {
                    "KONTEN": {"KNR": "Konto ID", "ONR": "Objekt ID (FK)", "KBEZEICHNUNG": "Bezeichnung"},
                    "BUCHUNG": {"BKNR": "Buchung ID", "KNR": "Konto ID (FK)", "BBETRAG": "Betrag", "BDATUM": "Datum"}
                },
                "critical_rules": [
                    "Use AVG(), SUM() for calculations",
                    "JOIN KONTEN with BUCHUNG via KNR",
                    "Filter by dates using BDATUM"
                ],
                "sql_templates": [
                    "SELECT AVG(B.BBETRAG) FROM BUCHUNG B JOIN KONTEN K ON B.KNR = K.KNR",
                    "SELECT SUM(BBETRAG) FROM BUCHUNG WHERE BDATUM >= '{date}'"
                ]
            },
            "count_queries": {
                "description": "Counting operations for various entities",
                "primary_tables": ["WOHNUNG", "BEWOHNER", "OBJEKTE"],
                "secondary_tables": [],
                "key_columns": {"*": "Use COUNT(*) for total counts"},
                "critical_rules": [
                    "Use COUNT(*) for total counts",
                    "Use COUNT(DISTINCT column) for unique counts",
                    "Add WHERE clauses for filtered counts"
                ],
                "sql_templates": [
                    "SELECT COUNT(*) FROM {table}",
                    "SELECT COUNT(DISTINCT {column}) FROM {table}"
                ]
            },
            "relationship_queries": {
                "description": "Complex multi-table relationship queries",
                "primary_tables": ["BEWOHNER", "EIGENTUEMER", "OBJEKTE"],
                "secondary_tables": ["VEREIG", "BEWADR", "EIGADR"],
                "key_columns": {
                    "ONR": "Central linking field for all relationships"
                },
                "critical_rules": [
                    "Use ONR as primary relationship key",
                    "Multiple JOINs often required",
                    "Consider business logic relationships"
                ],
                "sql_templates": [
                    "SELECT B.BNAME, E.ENAME FROM BEWOHNER B JOIN OBJEKTE O ON B.ONR = O.ONR JOIN VEREIG V ON O.ONR = V.ONR JOIN EIGENTUEMER E ON V.ENR = E.ENR"
                ]
            },
            "temporal_queries": {
                "description": "Time-based queries with date filtering",
                "primary_tables": ["BUCHUNG"],
                "secondary_tables": ["SOLLSTELLUNG"],
                "key_columns": {
                    "BUCHUNG": {"BDATUM": "Buchungsdatum for temporal filtering"},
                    "SOLLSTELLUNG": {"SDATUM": "Sollstellungsdatum"}
                },
                "critical_rules": [
                    "Use DATE comparisons with proper format",
                    "Consider Firebird date functions",
                    "Filter with >= and <= for date ranges"
                ],
                "sql_templates": [
                    "SELECT * FROM BUCHUNG WHERE BDATUM >= '{start_date}'",
                    "SELECT * FROM BUCHUNG WHERE BDATUM BETWEEN '{start}' AND '{end}'"
                ]
            },
            "comparison_queries": {
                "description": "Comparative analysis with statistical operations",
                "primary_tables": ["BUCHUNG", "WOHNUNG"],
                "secondary_tables": ["KONTEN"],
                "key_columns": {
                    "BUCHUNG": {"BBETRAG": "Amount for comparisons"},
                    "WOHNUNG": {"WGROESSE": "Size for comparisons"}
                },
                "critical_rules": [
                    "Use comparison operators (>, <, >=, <=)",
                    "Use HAVING for aggregate comparisons",
                    "Consider GROUP BY for grouped comparisons"
                ],
                "sql_templates": [
                    "SELECT * FROM BUCHUNG WHERE BBETRAG > {amount}",
                    "SELECT ONR, AVG(BBETRAG) FROM BUCHUNG GROUP BY ONR HAVING AVG(BBETRAG) > {threshold}"
                ]
            },
            "business_logic_queries": {
                "description": "Complex business logic requiring domain knowledge",
                "primary_tables": ["BEWOHNER", "EIGENTUEMER", "OBJEKTE", "KONTEN"],
                "secondary_tables": ["VEREIG", "BUCHUNG"],
                "key_columns": {
                    "ONR": "Central business relationship key"
                },
                "critical_rules": [
                    "Apply WINCASA business rules",
                    "Consider hierarchical relationships",
                    "Use domain-specific logic"
                ],
                "sql_templates": [
                    "-- Complex business queries require context-specific SQL generation"
                ]
            }
        }
    
    def synthesize(self, query: str) -> AdaptiveSynthesisResult:
        """
        Enhanced synthesis with ML classification and dynamic schema discovery.
        
        Args:
            query: Natural language query to synthesize
            
        Returns:
            AdaptiveSynthesisResult with comprehensive query analysis
        """
        # Step 1: ML-based classification
        classification: ClassificationResult = self.classifier.classify_query(query)
        
        # Step 2: Dynamic schema discovery
        relevant_tables = self.schema_discovery.discover_relevant_tables(
            classification.query_type, classification.entities
        )
        
        # Step 3: Get enhanced schema context
        schema_context = self.enhanced_schemas.get(
            classification.query_type, 
            self.enhanced_schemas["business_logic_queries"]
        )
        
        # Step 4: Generate relationship map
        relationship_map = {}
        for table in relevant_tables:
            relationship_map[table] = self.schema_discovery.get_table_relationships(table)
        
        # Step 5: Generate targeted SQL (enhanced from original)
        sql = self._generate_enhanced_sql(
            query, classification.query_type, classification.entities, relevant_tables
        )
        
        # Step 6: Create comprehensive reasoning
        reasoning = f"ML Classification: {classification.query_type} (confidence: {classification.confidence:.3f}). "
        reasoning += f"Dynamic tables: {relevant_tables}. "
        reasoning += f"Entities: {classification.entities}. "
        reasoning += classification.reasoning
        
        return AdaptiveSynthesisResult(
            sql=sql,
            query_type=classification.query_type,
            entities=classification.entities,
            schema_context=schema_context,
            confidence=classification.confidence,
            reasoning=reasoning,
            alternatives=classification.alternatives,
            dynamic_tables=relevant_tables,
            relationship_map=relationship_map
        )
    
    def _generate_enhanced_sql(self, query: str, query_type: str, entities: List[str], tables: List[str]) -> str:
        """
        Generate SQL using enhanced patterns and dynamic table discovery.
        
        Args:
            query: Original query
            query_type: Classified query type
            entities: Extracted entities
            tables: Dynamically discovered relevant tables
            
        Returns:
            Generated SQL query
        """
        schema = self.enhanced_schemas.get(query_type, {})
        templates = schema.get("sql_templates", [])
        
        query_lower = query.lower()
        
        # Enhanced SQL generation based on query type and entities
        if query_type == "address_lookup" and entities:
            return self._generate_address_sql(entities)
        
        elif query_type == "count_queries":
            return self._generate_count_sql(query_lower, tables)
        
        elif query_type == "owner_lookup":
            return self._generate_owner_sql(query_lower, entities)
        
        elif query_type == "financial_queries":
            return self._generate_financial_sql(query_lower)
        
        elif query_type == "resident_lookup":
            return self._generate_resident_sql(entities)
        
        elif query_type == "property_queries":
            return self._generate_property_sql(query_lower)
        
        elif query_type == "temporal_queries":
            return self._generate_temporal_sql(query_lower, entities)
        
        elif query_type == "comparison_queries":
            return self._generate_comparison_sql(query_lower, entities)
        
        # Fallback to template or general business logic
        if templates:
            return templates[0]  # Use first template as fallback
        
        return f"-- {query_type} query for: {query}"
    
    def _generate_address_sql(self, entities: List[str]) -> str:
        """Generate address lookup SQL"""
        conditions = []
        
        for entity in entities:
            if any(keyword in entity.lower() for keyword in ['str', 'straße', 'weg', 'platz']):
                street_clean = entity.replace('str.', '').replace('straße', '').strip()
                conditions.append(f"BSTR LIKE '%{street_clean}%'")
            elif entity.isdigit() and len(entity) == 5:
                conditions.append(f"BPLZORT LIKE '%{entity}%'")
            elif entity.isdigit() and len(entity) <= 3:
                conditions.append(f"BSTR LIKE '%{entity}%'")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return f"SELECT BNAME, BVNAME, BSTR, BPLZORT FROM BEWOHNER WHERE {where_clause}"
    
    def _generate_count_sql(self, query: str, tables: List[str]) -> str:
        """Generate count SQL"""
        if "wohnung" in query:
            return "SELECT COUNT(*) FROM WOHNUNG"
        elif "mieter" in query or "bewohner" in query:
            return "SELECT COUNT(*) FROM BEWOHNER"
        elif "eigentümer" in query:
            return "SELECT COUNT(*) FROM EIGENTUEMER"
        elif "objekt" in query or "gebäude" in query:
            return "SELECT COUNT(*) FROM OBJEKTE"
        
        # Default to first available table
        if tables:
            return f"SELECT COUNT(*) FROM {tables[0]}"
        return "SELECT COUNT(*) FROM WOHNUNG"
    
    def _generate_owner_sql(self, query: str, entities: List[str]) -> str:
        """Generate owner lookup SQL"""
        if any(city in query for city in ["köln", "essen", "duisburg"]):
            city = next(city for city in ["köln", "essen", "duisburg"] if city in query)
            return f"SELECT E.ENAME, E.EVNAME FROM EIGENTUEMER E JOIN EIGADR A ON E.ENR = A.ENR WHERE A.EPLZORT LIKE '%{city}%'"
        elif "alle eigentümer" in query:
            return "SELECT ENAME, EVNAME FROM EIGENTUEMER"
        
        return "SELECT ENAME, EVNAME FROM EIGENTUEMER"
    
    def _generate_financial_sql(self, query: str) -> str:
        """Generate financial SQL"""
        if "durchschnittliche miete" in query or "durchschnitt" in query:
            return "SELECT AVG(B.BBETRAG) FROM BUCHUNG B JOIN KONTEN K ON B.KNR = K.KNR"
        elif "summe" in query or "gesamt" in query:
            return "SELECT SUM(B.BBETRAG) FROM BUCHUNG B"
        
        return "SELECT B.BBETRAG, B.BDATUM FROM BUCHUNG B JOIN KONTEN K ON B.KNR = K.KNR"
    
    def _generate_resident_sql(self, entities: List[str]) -> str:
        """Generate resident lookup SQL"""
        if entities:
            name_entity = next((e for e in entities if len(e.split()) >= 2), None)
            if name_entity:
                return f"SELECT * FROM BEWOHNER WHERE BNAME LIKE '%{name_entity.split()[-1]}%'"
        
        return "SELECT BNAME, BVNAME, BSTR, BPLZORT FROM BEWOHNER"
    
    def _generate_property_sql(self, query: str) -> str:
        """Generate property SQL"""
        if "wie viele" in query or "anzahl" in query:
            return "SELECT COUNT(*) FROM WOHNUNG"
        
        return "SELECT W.WBEZEICHNUNG, O.OBEZEICHNUNG FROM WOHNUNG W JOIN OBJEKTE O ON W.ONR = O.ONR"
    
    def _generate_temporal_sql(self, query: str, entities: List[str]) -> str:
        """Generate temporal SQL"""
        # Look for date entities
        date_entities = [e for e in entities if any(char.isdigit() for char in e)]
        
        if date_entities:
            date_val = date_entities[0]
            return f"SELECT * FROM BUCHUNG WHERE BDATUM >= '{date_val}'"
        
        return "SELECT * FROM BUCHUNG ORDER BY BDATUM DESC"
    
    def _generate_comparison_sql(self, query: str, entities: List[str]) -> str:
        """Generate comparison SQL"""
        # Look for numeric entities
        numeric_entities = [e for e in entities if e.isdigit()]
        
        if "mehr als" in query and numeric_entities:
            value = numeric_entities[0]
            return f"SELECT * FROM BUCHUNG WHERE BBETRAG > {value}"
        elif "weniger als" in query and numeric_entities:
            value = numeric_entities[0]
            return f"SELECT * FROM BUCHUNG WHERE BBETRAG < {value}"
        
        return "SELECT * FROM BUCHUNG ORDER BY BBETRAG DESC"
    
    def learn_from_success(self, query: str, query_type: str, sql: str, success: bool):
        """
        Learn from successful query execution to improve future classifications.
        
        Args:
            query: The original query
            query_type: The classified query type
            sql: The generated SQL
            success: Whether the execution was successful
        """
        # Update classifier learning
        self.classifier.learn_from_success(query, query_type, sql, success)
        
        # Update schema discovery if successful
        if success:
            # Extract table names from SQL
            used_tables = self._extract_tables_from_sql(sql)
            self.schema_discovery.learn_from_successful_query(query_type, used_tables, sql)
    
    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        """Extract table names from SQL query"""
        sql_upper = sql.upper()
        tables = []
        
        # Simple pattern matching for table names
        for table in self.schema_discovery.available_tables:
            if table in sql_upper:
                tables.append(table)
        
        return tables


def test_adaptive_synthesizer():
    """Test the adaptive synthesizer"""
    print("🧪 Testing Adaptive TAG Synthesizer")
    print("=" * 50)
    
    # Mock schema info
    schema_info = {
        "tables": {
            "BEWOHNER": {},
            "EIGENTUEMER": {},
            "OBJEKTE": {},
            "WOHNUNG": {},
            "KONTEN": {},
            "BUCHUNG": {},
        }
    }
    
    synthesizer = AdaptiveTAGSynthesizer(schema_info)
    
    test_queries = [
        "Wer wohnt in der Marienstraße 26?",
        "Wie viele Wohnungen gibt es insgesamt?",
        "Alle Eigentümer aus Köln",
        "Durchschnittliche Miete in Essen",
        "Miete seit Januar 2023",
        "Wohnungen mehr als 500 Euro",
        "Liste aller Mieter",
        "Hausverwaltung Objekte"
    ]
    
    for query in test_queries:
        result = synthesizer.synthesize(query)
        print(f"\nQuery: {query}")
        print(f"  Type: {result.query_type} (confidence: {result.confidence:.3f})")
        print(f"  Tables: {result.dynamic_tables}")
        print(f"  Entities: {result.entities}")
        print(f"  SQL: {result.sql}")
        print(f"  Alternatives: {result.alternatives[:2]}")


if __name__ == "__main__":
    test_adaptive_synthesizer()