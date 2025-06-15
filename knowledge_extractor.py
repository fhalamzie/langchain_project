#!/usr/bin/env python3
"""
Knowledge Extractor for WINCASA System
Extracts field mappings, join relationships, and business vocabulary from SQL files
"""

import json
import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import sqlparse
from sqlparse.sql import Identifier, IdentifierList, Token

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeExtractor:
    def __init__(self, sql_dir: str = "SQL_QUERIES", output_dir: str = "knowledge_base"):
        self.sql_dir = Path(sql_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Knowledge stores
        self.alias_map = {}
        self.join_graph = defaultdict(set)
        self.business_vocabulary_candidates = {}
        self.table_columns = defaultdict(set)
        
    def extract_all(self):
        """Main extraction process"""
        logger.info(f"Starting knowledge extraction from {self.sql_dir}")
        
        sql_files = sorted(self.sql_dir.glob("*.sql"))
        logger.info(f"Found {len(sql_files)} SQL files")
        
        for sql_file in sql_files:
            logger.info(f"Processing {sql_file.name}")
            self._process_sql_file(sql_file)
            
        # Generate output files
        self._save_alias_map()
        self._save_join_graph()
        self._save_business_vocabulary_candidates()
        self._generate_extraction_report()
        
        logger.info("Knowledge extraction completed")
        
    def _process_sql_file(self, sql_file: Path):
        """Process a single SQL file"""
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract business terms from filename
            self._extract_business_terms(sql_file.name, content)
            
            # Parse SQL for aliases and joins
            self._parse_sql_content(content, sql_file.name)
            
        except Exception as e:
            logger.error(f"Error processing {sql_file.name}: {str(e)}")
            
    def _extract_business_terms(self, filename: str, content: str):
        """Extract business vocabulary from filename and comments"""
        # Extract from filename (e.g., "01_eigentuemer.sql" -> "eigentuemer")
        match = re.match(r'^\d+_(.+)\.sql$', filename)
        if match:
            term = match.group(1).replace('_', ' ')
            
            # Try to find the main table from comments
            table_pattern = r'HAUPTTABELLEN?:.*?([A-Z][A-Z0-9_]+)'
            table_match = re.search(table_pattern, content, re.MULTILINE | re.DOTALL)
            
            if table_match:
                main_table = table_match.group(1).strip()
                self.business_vocabulary_candidates[term] = {
                    'source_file': filename,
                    'primary_table': main_table,
                    'description': self._extract_business_purpose(content)
                }
                
    def _extract_business_purpose(self, content: str) -> str:
        """Extract business purpose from SQL comments"""
        purpose_pattern = r'BUSINESS PURPOSE:|GESCHÄFTSZWECK:(.*?)(?=\n[A-Z]|\*/)'
        match = re.search(purpose_pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
        
    def _parse_sql_content(self, content: str, source_file: str):
        """Parse SQL content for aliases and joins"""
        # Remove comments for parsing
        sql_without_comments = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        sql_without_comments = re.sub(r'--.*?$', '', sql_without_comments, flags=re.MULTILINE)
        
        # Find main SELECT statement
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_without_comments, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            self._parse_select_clause(select_clause, source_file)
            
        # Find FROM and JOIN clauses
        from_pattern = r'FROM\s+([A-Z][A-Z0-9_]+)(?:\s+(?:AS\s+)?([A-Z][A-Z0-9_]+))?'
        join_pattern = r'(?:LEFT|RIGHT|INNER|OUTER)?\s*JOIN\s+([A-Z][A-Z0-9_]+)(?:\s+(?:AS\s+)?([A-Z][A-Z0-9_]+))?\s+ON'
        
        # Extract table relationships
        tables_in_query = set()
        
        for match in re.finditer(from_pattern, sql_without_comments, re.IGNORECASE):
            table_name = match.group(1)
            alias = match.group(2) or table_name
            tables_in_query.add(table_name)
            
        for match in re.finditer(join_pattern, sql_without_comments, re.IGNORECASE):
            table_name = match.group(1)
            alias = match.group(2) or table_name
            tables_in_query.add(table_name)
            
        # Build join graph (all tables in same query are connected)
        tables_list = list(tables_in_query)
        for i in range(len(tables_list)):
            for j in range(i + 1, len(tables_list)):
                self.join_graph[tables_list[i]].add(tables_list[j])
                self.join_graph[tables_list[j]].add(tables_list[i])
                
    def _parse_select_clause(self, select_clause: str, source_file: str):
        """Parse SELECT clause for column aliases"""
        # Split by commas (handling nested functions)
        items = self._split_select_items(select_clause)
        
        for item in items:
            item = item.strip()
            if not item:
                continue
                
            # Pattern for: expression AS alias
            as_pattern = r'^(.+?)\s+AS\s+([A-Z][A-Z0-9_]+)\s*$'
            match = re.match(as_pattern, item, re.IGNORECASE)
            
            if match:
                expression = match.group(1).strip()
                alias = match.group(2).strip()
                
                # Determine canonical name
                canonical = self._extract_canonical_name(expression)
                
                if alias and canonical:
                    if alias in self.alias_map and self.alias_map[alias]['canonical'] != canonical:
                        logger.warning(f"Alias conflict: {alias} maps to both {self.alias_map[alias]['canonical']} and {canonical}")
                    
                    self.alias_map[alias] = {
                        'canonical': canonical,
                        'source_file': source_file,
                        'is_computed': self._is_computed_field(expression)
                    }
                    
    def _split_select_items(self, select_clause: str) -> List[str]:
        """Split SELECT items handling nested parentheses"""
        items = []
        current = ""
        paren_level = 0
        
        for char in select_clause:
            if char == '(' :
                paren_level += 1
            elif char == ')':
                paren_level -= 1
            elif char == ',' and paren_level == 0:
                items.append(current)
                current = ""
                continue
                
            current += char
            
        if current:
            items.append(current)
            
        return items
        
    def _extract_canonical_name(self, expression: str) -> Optional[str]:
        """Extract canonical column name from expression"""
        expression = expression.strip()
        
        # Handle CASE statements
        if expression.upper().startswith('CASE'):
            return f"COMPUTED: {expression[:50]}..."
            
        # Handle function calls
        func_pattern = r'^[A-Z]+\s*\((.+)\)$'
        func_match = re.match(func_pattern, expression, re.IGNORECASE)
        if func_match:
            inner = func_match.group(1).strip()
            return self._extract_canonical_name(inner)
            
        # Handle table.column or alias.column
        column_pattern = r'^([A-Z][A-Z0-9_]+)\.([A-Z][A-Z0-9_]+)$'
        match = re.match(column_pattern, expression, re.IGNORECASE)
        if match:
            return f"{match.group(1)}.{match.group(2)}"
            
        # Handle simple column names
        if re.match(r'^[A-Z][A-Z0-9_]+$', expression, re.IGNORECASE):
            return expression
            
        # Complex expression
        return f"EXPRESSION: {expression[:50]}..."
        
    def _is_computed_field(self, expression: str) -> bool:
        """Check if field is computed rather than direct column"""
        computed_indicators = ['CASE', 'WHEN', 'COALESCE', 'SUM', 'COUNT', 'AVG', 'MAX', 'MIN', 'CAST', '||']
        expression_upper = expression.upper()
        return any(indicator in expression_upper for indicator in computed_indicators)
        
    def _save_alias_map(self):
        """Save alias mappings to JSON"""
        output_file = self.output_dir / "alias_map.json"
        
        # Sort by key for consistency
        sorted_map = dict(sorted(self.alias_map.items()))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_map, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved {len(sorted_map)} alias mappings to {output_file}")
        
    def _save_join_graph(self):
        """Save join relationships to JSON"""
        output_file = self.output_dir / "join_graph.json"
        
        # Convert sets to lists for JSON serialization
        join_dict = {table: sorted(list(connections)) 
                     for table, connections in sorted(self.join_graph.items())}
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(join_dict, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved join graph with {len(join_dict)} tables to {output_file}")
        
    def _save_business_vocabulary_candidates(self):
        """Save business vocabulary candidates for manual curation"""
        output_file = self.output_dir / "business_vocabulary_candidates.json"
        
        # Add note about manual curation
        output = {
            "_note": "This file contains candidates extracted from SQL filenames. Please review and curate into business_vocabulary.json",
            "candidates": dict(sorted(self.business_vocabulary_candidates.items()))
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved {len(self.business_vocabulary_candidates)} vocabulary candidates to {output_file}")
        
    def _generate_extraction_report(self):
        """Generate detailed extraction report"""
        report_file = self.output_dir / "extraction_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("WINCASA Knowledge Extraction Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total SQL files processed: {len(list(self.sql_dir.glob('*.sql')))}\n")
            f.write(f"Total aliases extracted: {len(self.alias_map)}\n")
            f.write(f"Total tables in join graph: {len(self.join_graph)}\n")
            f.write(f"Total business terms found: {len(self.business_vocabulary_candidates)}\n\n")
            
            # List computed fields
            f.write("Computed Fields Found:\n")
            f.write("-" * 30 + "\n")
            computed = [alias for alias, info in self.alias_map.items() if info.get('is_computed')]
            for alias in sorted(computed):
                f.write(f"  {alias}: {self.alias_map[alias]['canonical'][:60]}...\n")
                
            f.write(f"\nTotal computed fields: {len(computed)}\n\n")
            
            # List potential conflicts
            f.write("Potential Issues:\n")
            f.write("-" * 30 + "\n")
            
            # Check for isolated tables
            isolated_tables = [table for table, connections in self.join_graph.items() if len(connections) == 0]
            if isolated_tables:
                f.write(f"Isolated tables (no joins): {', '.join(isolated_tables)}\n")
                
            # Summary
            f.write("\nNext Steps:\n")
            f.write("1. Review business_vocabulary_candidates.json and create business_vocabulary.json\n")
            f.write("2. Validate alias_map.json for any incorrect mappings\n")
            f.write("3. Check join_graph.json for missing relationships\n")
            
        logger.info(f"Generated extraction report: {report_file}")


def main():
    extractor = KnowledgeExtractor()
    extractor.extract_all()


if __name__ == "__main__":
    main()