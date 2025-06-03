#!/usr/bin/env python3
"""
Intelligent Query Preprocessor

This module preprocesses natural language queries to:
- Identify business entities
- Map them to database tables
- Find optimal join paths
- Enrich queries with contextual information
"""

import re
import json
import logging
from typing import List, Dict, Any, Tuple, Optional, Set
from collections import defaultdict, deque
import networkx as nx
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryPreprocessor:
    """Preprocesses natural language queries for better SQL generation."""
    
    def __init__(self, knowledge_base_path: str = None):
        """Initialize the query preprocessor."""
        # Load knowledge base
        if knowledge_base_path:
            self.kb_path = knowledge_base_path
        else:
            self.kb_path = Path("output/compiled_knowledge_base.json")
        
        self.knowledge_base = self._load_knowledge_base()
        
        # Build entity mappings
        self._build_entity_mappings()
        
        # Build relationship graph
        self._build_relationship_graph()
        
        # Initialize German NLP patterns
        self._initialize_nlp_patterns()
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load the compiled knowledge base."""
        if self.kb_path.exists():
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"Knowledge base not found at {self.kb_path}")
            return {}
    
    def _build_entity_mappings(self):
        """Build mappings from business terms to table names."""
        self.entity_mappings = {}
        
        # Direct table name mappings
        for table_name in self.knowledge_base.get('core_entities', {}):
            self.entity_mappings[table_name.lower()] = table_name
        
        # Business glossary mappings
        glossary = self.knowledge_base.get('business_glossary', {})
        for term, meaning in glossary.items():
            self.entity_mappings[term.lower()] = term
            # Also add variations
            if 'owner' in meaning.lower():
                self.entity_mappings[term.lower()] = 'EIGENTUEMER'
            elif 'tenant' in meaning.lower() or 'resident' in meaning.lower():
                self.entity_mappings[term.lower()] = 'BEWOHNER'
            elif 'propert' in meaning.lower() or 'building' in meaning.lower():
                self.entity_mappings[term.lower()] = 'OBJEKTE'
            elif 'account' in meaning.lower():
                self.entity_mappings[term.lower()] = 'KONTEN'
            elif 'payment' in meaning.lower():
                self.entity_mappings[term.lower()] = 'ZAHLUNG'
        
        # Additional German mappings
        german_mappings = {
            'mieter': 'BEWOHNER',
            'mietern': 'BEWOHNER',
            'eigentümer': 'EIGENTUEMER',
            'eigentümern': 'EIGENTUEMER',
            'wohnung': 'WOHNUNG',
            'wohnungen': 'WOHNUNG',
            'objekt': 'OBJEKTE',
            'objekte': 'OBJEKTE',
            'gebäude': 'OBJEKTE',
            'immobilie': 'OBJEKTE',
            'immobilien': 'OBJEKTE',
            'konto': 'KONTEN',
            'konten': 'KONTEN',
            'zahlung': 'ZAHLUNG',
            'zahlungen': 'ZAHLUNG',
            'miete': 'SOLLSTELLUNG',
            'mieten': 'SOLLSTELLUNG',
            'vertrag': 'VERTRAEGE',
            'verträge': 'VERTRAEGE',
            'rechnung': 'SOLLSTELLUNG',
            'rechnungen': 'SOLLSTELLUNG',
            'nebenkosten': 'NKMASTER',
            'abrechnung': 'ABRECHNUNG',
            'abrechnungen': 'ABRECHNUNG',
            'person': 'PERSONEN',
            'personen': 'PERSONEN',
            'bank': 'BANKEN',
            'banken': 'BANKEN',
            'verwalter': 'VERWALTER',
            'verwaltung': 'VERWALTUNG',
            'zähler': 'ZAEHLERSTAMM',
            'zählerstände': 'ZAEHLERSTAND',
            'heizung': 'HK_KOSTEN',
            'heizkosten': 'HK_KOSTEN'
        }
        
        for term, table in german_mappings.items():
            self.entity_mappings[term] = table
    
    def _build_relationship_graph(self):
        """Build a graph of table relationships for path finding."""
        self.relationship_graph = nx.DiGraph()
        
        # Add all tables as nodes
        for table in self.knowledge_base.get('core_entities', {}):
            self.relationship_graph.add_node(table)
        
        # Add all tables from top_20
        for table_info in self.knowledge_base.get('top_20_tables', []):
            self.relationship_graph.add_node(table_info['table'])
        
        # Add relationships as edges
        for rel in self.knowledge_base.get('relationships', []):
            from_table = rel['from_table']
            to_table = rel['to_table']
            from_col = rel['from_column']
            to_col = rel['to_column']
            
            # Add edge with relationship details
            self.relationship_graph.add_edge(
                from_table, 
                to_table,
                from_column=from_col,
                to_column=to_col,
                relationship=f"{from_table}.{from_col} -> {to_table}.{to_col}"
            )
    
    def _initialize_nlp_patterns(self):
        """Initialize NLP patterns for German and English."""
        # Patterns for extracting numeric values
        self.numeric_patterns = [
            (r'\b(\d+)\b', 'number'),
            (r'\b(\d+[.,]\d+)\b', 'decimal'),
            (r'\b(erste|zweite|dritte|vierte|fünfte)\b', 'ordinal'),
            (r'\b(first|second|third|fourth|fifth)\b', 'ordinal_en')
        ]
        
        # Patterns for time expressions
        self.time_patterns = [
            (r'\b(heute|today)\b', 'today'),
            (r'\b(gestern|yesterday)\b', 'yesterday'),
            (r'\b(morgen|tomorrow)\b', 'tomorrow'),
            (r'\b(diese woche|this week)\b', 'this_week'),
            (r'\b(letzten? monat|last month)\b', 'last_month'),
            (r'\b(dieses jahr|this year)\b', 'this_year'),
            (r'\b(\d{4})\b', 'year'),
            (r'\b(\d{1,2})[./](\d{1,2})[./](\d{2,4})\b', 'date')
        ]
        
        # Query intent patterns
        self.intent_patterns = {
            'list': [r'\b(liste|list|zeige|show|anzeigen|display)\b'],
            'count': [r'\b(anzahl|count|wieviele|how many|zähle)\b'],
            'sum': [r'\b(summe|sum|gesamt|total|betrag)\b'],
            'average': [r'\b(durchschnitt|average|mittel|avg)\b'],
            'filter': [r'\b(wo|where|mit|with|ohne|without)\b'],
            'join': [r'\b(und|and|mit|with|inklusive|including)\b'],
            'sort': [r'\b(sortiert|sorted|geordnet|ordered)\b'],
            'group': [r'\b(gruppiert|grouped|pro|per|nach|by)\b']
        }
    
    def preprocess_query(self, query: str) -> Dict[str, Any]:
        """
        Preprocess a natural language query.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with preprocessed information
        """
        logger.info(f"Preprocessing query: {query}")
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Identify tables
        tables = self._identify_tables(query, entities)
        
        # Find relationships if multiple tables
        join_paths = []
        if len(tables) > 1:
            join_paths = self._find_join_paths(tables)
        
        # Extract query intent
        intent = self._extract_intent(query)
        
        # Extract conditions
        conditions = self._extract_conditions(query)
        
        # Generate enriched query
        enriched_query = self._enrich_query(query, tables, join_paths, intent)
        
        # Build context information
        context = self._build_context(tables, join_paths)
        
        result = {
            'original_query': query,
            'enriched_query': enriched_query,
            'entities': entities,
            'tables': tables,
            'join_paths': join_paths,
            'intent': intent,
            'conditions': conditions,
            'context': context,
            'suggestions': self._generate_suggestions(tables, intent)
        }
        
        return result
    
    def _extract_entities(self, query: str) -> List[Dict[str, str]]:
        """Extract business entities from the query."""
        entities = []
        query_lower = query.lower()
        
        # Check for known entities
        for term, table in self.entity_mappings.items():
            if term in query_lower:
                entities.append({
                    'term': term,
                    'table': table,
                    'type': 'business_entity'
                })
        
        # Extract numeric values
        for pattern, num_type in self.numeric_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'term': match.group(0),
                    'value': match.group(1),
                    'type': f'numeric_{num_type}'
                })
        
        # Extract time expressions
        for pattern, time_type in self.time_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'term': match.group(0),
                    'type': f'time_{time_type}'
                })
        
        return entities
    
    def _identify_tables(self, query: str, entities: List[Dict[str, str]]) -> List[str]:
        """Identify relevant tables from the query and entities."""
        tables = set()
        
        # Add tables from entities
        for entity in entities:
            if entity.get('table'):
                tables.add(entity['table'])
        
        # Check for table names directly in query
        query_upper = query.upper()
        for table_name in self.knowledge_base.get('core_entities', {}):
            if table_name in query_upper:
                tables.add(table_name)
        
        # If no tables found, try to infer from query context
        if not tables:
            query_lower = query.lower()
            
            # Financial context
            if any(term in query_lower for term in ['zahlung', 'payment', 'saldo', 'balance', 'konto']):
                tables.update(['KONTEN', 'ZAHLUNG', 'BUCHUNG'])
            
            # Property context
            elif any(term in query_lower for term in ['objekt', 'property', 'wohnung', 'apartment']):
                tables.update(['OBJEKTE', 'WOHNUNG'])
            
            # Person context
            elif any(term in query_lower for term in ['eigentümer', 'owner', 'mieter', 'tenant']):
                tables.update(['EIGENTUEMER', 'BEWOHNER'])
        
        return list(tables)
    
    def _find_join_paths(self, tables: List[str]) -> List[Dict[str, Any]]:
        """Find optimal join paths between tables."""
        join_paths = []
        
        # For each pair of tables, find shortest path
        for i in range(len(tables)):
            for j in range(i + 1, len(tables)):
                try:
                    # Find shortest path in relationship graph
                    path = nx.shortest_path(self.relationship_graph, tables[i], tables[j])
                    
                    # Build join conditions
                    joins = []
                    for k in range(len(path) - 1):
                        edge_data = self.relationship_graph.get_edge_data(path[k], path[k + 1])
                        if edge_data:
                            joins.append({
                                'from_table': path[k],
                                'to_table': path[k + 1],
                                'from_column': edge_data.get('from_column'),
                                'to_column': edge_data.get('to_column'),
                                'relationship': edge_data.get('relationship')
                            })
                    
                    join_paths.append({
                        'tables': [tables[i], tables[j]],
                        'path': path,
                        'joins': joins,
                        'distance': len(path) - 1
                    })
                    
                except nx.NetworkXNoPath:
                    # No path found between tables
                    logger.warning(f"No relationship path found between {tables[i]} and {tables[j]}")
        
        return join_paths
    
    def _extract_intent(self, query: str) -> Dict[str, Any]:
        """Extract the query intent."""
        query_lower = query.lower()
        intent = {
            'type': 'list',  # default
            'aggregations': [],
            'filters': [],
            'sorting': None,
            'grouping': None
        }
        
        # Check for intent patterns
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    if intent_type in ['count', 'sum', 'average']:
                        intent['aggregations'].append(intent_type)
                    elif intent_type == 'filter':
                        intent['filters'].append('has_conditions')
                    elif intent_type == 'sort':
                        intent['sorting'] = True
                    elif intent_type == 'group':
                        intent['grouping'] = True
                    else:
                        intent['type'] = intent_type
        
        return intent
    
    def _extract_conditions(self, query: str) -> List[Dict[str, Any]]:
        """Extract filter conditions from the query."""
        conditions = []
        
        # Pattern for "field = value" type conditions
        condition_patterns = [
            r'(\w+)\s*=\s*["\']?(\w+)["\']?',
            r'(\w+)\s+(?:ist|is|equals)\s+["\']?(\w+)["\']?',
            r'(\w+)\s+(?:größer|greater|mehr)\s+(?:als|than)?\s*(\d+)',
            r'(\w+)\s+(?:kleiner|less|weniger)\s+(?:als|than)?\s*(\d+)'
        ]
        
        for pattern in condition_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                conditions.append({
                    'field': match.group(1),
                    'operator': 'equals',  # simplified
                    'value': match.group(2)
                })
        
        return conditions
    
    def _enrich_query(self, query: str, tables: List[str], join_paths: List[Dict], intent: Dict) -> str:
        """Enrich the query with additional context."""
        enriched_parts = [query]
        
        # Add table context
        if tables:
            table_context = f"Focus on tables: {', '.join(tables)}"
            enriched_parts.append(table_context)
        
        # Add join context
        if join_paths:
            join_context = "Join relationships: "
            for path in join_paths:
                join_desc = " -> ".join(path['path'])
                join_context += f"{join_desc}; "
            enriched_parts.append(join_context)
        
        # Add intent context
        if intent['aggregations']:
            agg_context = f"Perform aggregations: {', '.join(intent['aggregations'])}"
            enriched_parts.append(agg_context)
        
        return " | ".join(enriched_parts)
    
    def _build_context(self, tables: List[str], join_paths: List[Dict]) -> str:
        """Build context information for the LLM."""
        context_parts = []
        
        # Add table descriptions
        for table in tables[:3]:  # Limit to avoid token overflow
            if table in self.knowledge_base.get('core_entities', {}):
                entity_info = self.knowledge_base['core_entities'][table]
                context_parts.append(
                    f"{table}: {entity_info.get('description', '')[:200]}"
                )
        
        # Add relationship context
        if join_paths:
            context_parts.append("\nKey relationships:")
            for path in join_paths[:2]:  # Limit paths
                for join in path['joins']:
                    context_parts.append(
                        f"- {join['relationship']}"
                    )
        
        return "\n".join(context_parts)
    
    def _generate_suggestions(self, tables: List[str], intent: Dict) -> List[str]:
        """Generate query suggestions based on identified tables and intent."""
        suggestions = []
        
        # Table-specific suggestions
        if 'KONTEN' in tables:
            suggestions.append("Consider using KONTOSALDO procedure for balance calculations")
        
        if 'EIGENTUEMER' in tables and 'OBJEKTE' in tables:
            suggestions.append("Join through VEREIG table for owner-property relationships")
        
        if 'BEWOHNER' in tables and 'WOHNUNG' in tables:
            suggestions.append("Use WOHNUNG.KNR to link tenants to apartments")
        
        # Intent-specific suggestions
        if 'sum' in intent['aggregations'] and 'ZAHLUNG' in tables:
            suggestions.append("Group by ZAHLUNG.ART for payment type summaries")
        
        if intent['grouping'] and 'OBJEKTE' in tables:
            suggestions.append("Consider grouping by OBJEKTE.VERWNR for management units")
        
        return suggestions
    
    def get_table_clusters(self, tables: List[str]) -> Dict[str, List[str]]:
        """Get related tables that might be useful for the query."""
        clusters = defaultdict(list)
        
        # Use table clusters from knowledge base
        kb_clusters = self.knowledge_base.get('table_clusters', {})
        
        for table in tables:
            # Find which cluster this table belongs to
            for cluster_name, cluster_tables in kb_clusters.items():
                if table in cluster_tables:
                    clusters[cluster_name].extend(cluster_tables)
        
        # Remove duplicates
        for cluster_name in clusters:
            clusters[cluster_name] = list(set(clusters[cluster_name]))
        
        return dict(clusters)


if __name__ == "__main__":
    # Test the preprocessor
    preprocessor = QueryPreprocessor()
    
    test_queries = [
        "Zeige alle Eigentümer mit ihren Objekten",
        "Was ist der aktuelle Saldo für Konto 1000?",
        "Liste alle Mieter die keine Miete bezahlt haben",
        "Anzahl der Wohnungen pro Gebäude",
        "Summe der Zahlungen im letzten Monat"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        result = preprocessor.preprocess_query(query)
        print(f"Tables: {result['tables']}")
        print(f"Intent: {result['intent']['type']}")
        if result['join_paths']:
            print(f"Join paths: {[p['path'] for p in result['join_paths']]}")
        print(f"Enriched: {result['enriched_query']}")
        if result['suggestions']:
            print(f"Suggestions: {result['suggestions']}")