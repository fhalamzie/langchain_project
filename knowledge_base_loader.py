"""
Knowledge Base Loader for WINCASA System
Loads and provides access to extracted knowledge from SQL files
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class KnowledgeBaseLoader:
    def __init__(self, knowledge_dir: str = "knowledge_base"):
        self.knowledge_dir = Path(knowledge_dir)
        self.alias_map = {}
        self.join_graph = {}
        self.business_vocabulary = {}
        
        self._load_knowledge_base()
        
    def _load_knowledge_base(self):
        """Load all knowledge base files"""
        try:
            # Load alias mappings
            alias_file = self.knowledge_dir / "alias_map.json"
            if alias_file.exists():
                with open(alias_file, 'r', encoding='utf-8') as f:
                    self.alias_map = json.load(f)
                logger.info(f"Loaded {len(self.alias_map)} alias mappings")
            
            # Load join graph
            join_file = self.knowledge_dir / "join_graph.json"
            if join_file.exists():
                with open(join_file, 'r', encoding='utf-8') as f:
                    self.join_graph = json.load(f)
                logger.info(f"Loaded join graph with {len(self.join_graph)} tables")
            
            # Load business vocabulary (check both files)
            vocab_file = self.knowledge_dir / "business_vocabulary.json"
            if not vocab_file.exists():
                vocab_file = self.knowledge_dir / "business_vocabulary_candidates.json"
                
            if vocab_file.exists():
                with open(vocab_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "candidates" in data:
                        self.business_vocabulary = data["candidates"]
                    else:
                        self.business_vocabulary = data
                logger.info(f"Loaded {len(self.business_vocabulary)} business terms")
                
        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
            
    def get_canonical_field(self, alias: str) -> Optional[str]:
        """Get canonical database field for an alias"""
        if alias in self.alias_map:
            canonical = self.alias_map[alias].get('canonical', '')
            # Clean up computed expressions
            if canonical.startswith('EXPRESSION:') or canonical.startswith('COMPUTED:'):
                return canonical
            return canonical
        return None
        
    def get_table_from_field(self, field: str) -> Optional[str]:
        """Extract table name from field like TABLE.COLUMN"""
        if '.' in field:
            return field.split('.')[0]
        return None
        
    def find_business_term(self, query: str) -> List[Dict[str, str]]:
        """Find business terms in user query"""
        query_lower = query.lower()
        found_terms = []
        
        for term, info in self.business_vocabulary.items():
            if term.lower() in query_lower:
                found_terms.append({
                    'term': term,
                    'table': info.get('primary_table', ''),
                    'description': info.get('description', '')
                })
                
        # Also check for common variations
        term_variations = {
            'mieter': ['mieter', 'bewohner', 'tenant'],
            'eigentümer': ['eigentümer', 'eigentuemer', 'owner', 'vermieter'],
            'wohnung': ['wohnung', 'apartment', 'einheit'],
            'objekt': ['objekt', 'gebäude', 'liegenschaft', 'immobilie']
        }
        
        for base_term, variations in term_variations.items():
            for variation in variations:
                if variation in query_lower and base_term in self.business_vocabulary:
                    info = self.business_vocabulary[base_term]
                    found_terms.append({
                        'term': base_term,
                        'table': info.get('primary_table', ''),
                        'description': info.get('description', '')
                    })
                    break
                    
        return found_terms
        
    def find_aliases_in_query(self, query: str) -> List[Tuple[str, str]]:
        """Find known aliases mentioned in query"""
        query_upper = query.upper()
        found_aliases = []
        
        for alias in self.alias_map:
            # Check for whole word match
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, query_upper):
                canonical = self.get_canonical_field(alias)
                if canonical:
                    found_aliases.append((alias, canonical))
                    
        return found_aliases
        
    def get_join_path(self, tables: List[str]) -> List[Tuple[str, str]]:
        """Find join path between tables using BFS"""
        if len(tables) < 2:
            return []
            
        # Simple BFS to find shortest path
        start = tables[0]
        end = tables[1]
        
        if start not in self.join_graph:
            return []
            
        visited = {start}
        queue = [(start, [])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current == end:
                return path
                
            for neighbor in self.join_graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [(current, neighbor)]
                    queue.append((neighbor, new_path))
                    
        return []
        
    def enhance_prompt_with_knowledge(self, user_query: str) -> str:
        """Create enhanced context for LLM based on query"""
        context_parts = []
        query_lower = user_query.lower()
        
        # Special handling for KALTMIETE queries
        if 'kaltmiete' in query_lower:
            context_parts.append("WICHTIG für KALTMIETE:")
            context_parts.append("- KALTMIETE ist in BEWOHNER.Z1 gespeichert (NICHT in KONTEN!)")
            context_parts.append("- Für Eigentümer-Kaltmieten: JOIN über EIGADR -> OBJEKTE -> BEWOHNER")
            context_parts.append("- Beispiel: SELECT SUM(B.Z1) FROM EIGADR E JOIN OBJEKTE O ON E.EIGNR = O.EIGNR JOIN BEWOHNER B ON O.ONR = B.ONR WHERE E.ENOTIZ = 'CODE'")
            context_parts.append("")
        
        # Find business terms
        business_terms = self.find_business_term(user_query)
        if business_terms:
            context_parts.append("BUSINESS BEGRIFFE:")
            for term in business_terms:
                context_parts.append(f"- '{term['term']}' -> Tabelle: {term['table']}")
                
        # Find aliases
        aliases = self.find_aliases_in_query(user_query)
        if aliases:
            context_parts.append("\nFELD MAPPINGS:")
            for alias, canonical in aliases:
                context_parts.append(f"- {alias} = {canonical}")
                
        # Extract tables and suggest joins
        tables = set()
        for term in business_terms:
            if term['table']:
                tables.add(term['table'])
                
        for alias, canonical in aliases:
            table = self.get_table_from_field(canonical)
            if table and not table.startswith('EXPRESSION'):
                tables.add(table)
                
        if len(tables) >= 2:
            tables_list = list(tables)
            join_path = self.get_join_path(tables_list[:2])
            if join_path:
                context_parts.append("\nVORGESCHLAGENE JOINS:")
                for t1, t2 in join_path:
                    context_parts.append(f"- {t1} JOIN {t2}")
                    
        return "\n".join(context_parts) if context_parts else ""
        
    def validate_sql_fields(self, sql_query: str) -> List[str]:
        """Validate fields in SQL query against knowledge base"""
        issues = []
        
        # Extract field names from SQL
        field_pattern = r'\b([A-Z][A-Z0-9_]*)\s*='
        fields_in_query = re.findall(field_pattern, sql_query, re.IGNORECASE)
        
        for field in fields_in_query:
            field_upper = field.upper()
            
            # Check if it's a known alias
            if field_upper not in self.alias_map:
                # Try to find similar aliases
                similar = [alias for alias in self.alias_map 
                          if alias.startswith(field_upper[:3])]
                
                if similar:
                    issues.append(f"Unbekanntes Feld '{field}'. Meinten Sie: {', '.join(similar[:3])}?")
                else:
                    issues.append(f"Unbekanntes Feld '{field}'")
                    
        return issues


# Singleton instance
_knowledge_base = None

def get_knowledge_base() -> KnowledgeBaseLoader:
    """Get singleton knowledge base instance"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBaseLoader()
    return _knowledge_base