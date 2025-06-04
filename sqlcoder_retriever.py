#!/usr/bin/env python3
"""
SQLCoder-2 Retriever with JOIN-Aware Prompting

This module implements a specialized retriever using SQLCoder-2 model for SQL generation
with enhanced JOIN-aware prompting strategies optimized for Firebird databases.
"""

import os
import re
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from langchain_core.documents import Document

from retrievers import BaseDocumentationRetriever
from phoenix_monitoring import get_monitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLCoderRetriever:
    """
    SQLCoder-2 based retriever with JOIN-aware prompting for complex table relationships.
    Optimized for Firebird SQL dialect and WINCASA database schema.
    """
    
    def __init__(
        self,
        model_name: str = "defog/sqlcoder2",
        parsed_docs: List[Document] = None,
        openai_api_key: str = "",
        use_quantization: bool = True,
        max_new_tokens: int = 512,
        temperature: float = 0.1,
        device_map: str = "auto"
    ):
        """
        Initialize SQLCoder-2 retriever.
        
        Args:
            model_name: HuggingFace model name for SQLCoder-2
            parsed_docs: Preloaded documentation documents
            openai_api_key: API key for fallback embeddings
            use_quantization: Use 4-bit quantization for memory efficiency
            max_new_tokens: Maximum tokens to generate
            temperature: Generation temperature
            device_map: Device mapping for model loading
        """
        self.model_name = model_name
        self.parsed_docs = parsed_docs or []
        self.openai_api_key = openai_api_key
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.device_map = device_map
        
        # Model and tokenizer placeholders
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        
        # Global context and schema cache
        self.global_context = ""
        self.schema_cache = {}
        self.join_patterns = {}
        
        # Phoenix monitoring
        self.monitor = get_monitor(enable_ui=False)
        
        # Quantization config for memory efficiency
        if use_quantization:
            self.quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        else:
            self.quantization_config = None
            
        # Initialize components
        self._load_global_context()
        self._extract_schema_patterns()
        self._load_model()
        
        logger.info(f"SQLCoder retriever initialized with model: {model_name}")
    
    def _load_global_context(self):
        """Load global database context for consistent prompting."""
        try:
            from global_context import get_global_context_prompt
            self.global_context = get_global_context_prompt()
            logger.info("✅ Loaded global context for SQLCoder prompting")
        except ImportError:
            # Fallback to static context
            self.global_context = """
            WINCASA Property Management Database Context:
            
            Core Entities:
            - BEWOHNER (Tenants): BWO=ONR, BSTR (Street+Number), BPLZORT (ZIP+City)
            - EIGENTUEMER (Owners): Connected via VEREIG table
            - OBJEKTE (Properties): ONR primary key, connected to all entities
            - KONTEN (Accounts): Financial data, KNR=BKNR relationships
            
            Key Relationships:
            - BEWOHNER -> OBJEKTE: BWO = ONR
            - EIGENTUEMER -> OBJEKTE: via VEREIG table
            - KONTEN -> BUCHUNG: KNR = BKNR
            - FINANZABFRAGEN: KONTEN -> ZAHLUNG -> SOLLSTELLUNG
            
            Critical Patterns:
            - Address searches: Use LIKE with BSTR and BPLZORT
            - Financial queries: Multi-table JOINs through account tables
            - Owner queries: Always include VEREIG junction table
            """
            logger.warning("⚠️ Using fallback context for SQLCoder")
    
    def _extract_schema_patterns(self):
        """Extract schema patterns and JOIN hints from documentation."""
        if not self.parsed_docs:
            logger.warning("No parsed docs available for schema pattern extraction")
            return
            
        # Extract table relationships and JOIN patterns
        table_relations = defaultdict(list)
        join_hints = {}
        
        for doc in self.parsed_docs:
            if doc.metadata.get('type') == 'yaml_definition':
                content = doc.page_content
                
                # Extract table name
                table_match = re.search(r'Entity Name: (\w+)', content)
                if table_match:
                    table_name = table_match.group(1)
                    
                    # Extract relations
                    relations_section = re.search(r'Relations:\s*\n(.*?)(?:\n\n|$)', content, re.DOTALL)
                    if relations_section:
                        relations = relations_section.group(1).strip().split('\n')
                        for relation in relations:
                            relation = relation.strip().replace('- ', '')
                            if relation:
                                table_relations[table_name].append(relation)
                                
                                # Build JOIN hints
                                if '->' in relation:
                                    parts = relation.split('->')
                                    if len(parts) == 2:
                                        from_table, to_info = parts
                                        from_table = from_table.strip()
                                        to_info = to_info.strip()
                                        
                                        join_key = f"{from_table}_{table_name}"
                                        join_hints[join_key] = {
                                            'from_table': from_table,
                                            'to_table': table_name,
                                            'hint': to_info
                                        }
        
        self.schema_cache = dict(table_relations)
        self.join_patterns = join_hints
        
        logger.info(f"Extracted schema patterns for {len(self.schema_cache)} tables")
        logger.info(f"Built {len(self.join_patterns)} JOIN patterns")
    
    def _load_model(self):
        """Load SQLCoder-2 model with error handling."""
        try:
            logger.info(f"Loading SQLCoder-2 model: {self.model_name}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            # Load model with quantization if specified
            if self.quantization_config:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    quantization_config=self.quantization_config,
                    device_map=self.device_map,
                    torch_dtype=torch.float16,
                    trust_remote_code=True
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map=self.device_map,
                    torch_dtype=torch.float16,
                    trust_remote_code=True
                )
            
            self.model_loaded = True
            logger.info("✅ SQLCoder-2 model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load SQLCoder-2 model: {e}")
            self.model_loaded = False
            # Could implement fallback to OpenAI here
    
    def _build_join_aware_prompt(
        self, 
        query: str, 
        schema_context: str, 
        relevant_tables: List[str]
    ) -> str:
        """
        Build JOIN-aware prompt with advanced schema context and relationship hints.
        
        Args:
            query: Natural language query
            schema_context: Relevant schema information
            relevant_tables: List of tables likely needed for the query
            
        Returns:
            Formatted prompt for SQLCoder-2
        """
        # Identify relevant JOIN patterns with enhanced logic
        join_hints = []
        join_strategies = []
        
        # Enhanced JOIN pattern detection
        for table in relevant_tables:
            for pattern_key, pattern_info in self.join_patterns.items():
                if table in pattern_key:
                    hint = f"JOIN {pattern_info['from_table']} -> {pattern_info['to_table']}: {pattern_info['hint']}"
                    join_hints.append(hint)
        
        # Add common WINCASA JOIN strategies
        if 'BEWOHNER' in relevant_tables and 'OBJEKTE' in relevant_tables:
            join_strategies.append("BEWOHNER.BWO = OBJEKTE.ONR (tenant to property)")
        
        if 'EIGENTUEMER' in relevant_tables and 'OBJEKTE' in relevant_tables:
            join_strategies.append("EIGENTUEMER JOIN VEREIG ON EIGENTUEMER.ENR = VEREIG.VENR JOIN OBJEKTE ON VEREIG.VONR = OBJEKTE.ONR (owner to property via junction)")
        
        if 'KONTEN' in relevant_tables and 'BUCHUNG' in relevant_tables:
            join_strategies.append("KONTEN.KNR = BUCHUNG.BKNR (account to booking)")
        
        # Analyze query intent for better prompting
        query_intent = self._analyze_query_intent(query)
        
        # Build context-aware prompt with query intent
        prompt = f"""### Task
Generate a syntactically correct Firebird SQL query for the following request.

### Query Intent Analysis
- Type: {query_intent.get('type', 'general')}
- Expected Result: {query_intent.get('expected_result', 'data retrieval')}
- Complexity: {query_intent.get('complexity', 'medium')}

### Database Context
{self.global_context}

### Schema Information
{schema_context}

### JOIN Patterns (Critical for relationships)
{chr(10).join(join_hints) if join_hints else "No specific JOIN patterns from schema."}

### Common JOIN Strategies for WINCASA
{chr(10).join(join_strategies) if join_strategies else "Standard table relationships apply."}

### Firebird SQL Syntax Rules
- Use `SELECT FIRST N` instead of `LIMIT N` for row limiting
- Address searches: Use LIKE with wildcards (BSTR LIKE 'Marienstraße%' AND BPLZORT LIKE '%Essen%')
- String comparisons are case-sensitive unless using UPPER()
- Date format: 'YYYY-MM-DD' 
- Aggregate functions: COUNT(), SUM(), AVG(), MAX(), MIN()
- Window functions supported: ROW_NUMBER() OVER (ORDER BY ...)

### Query Optimization Hints
- For address searches: Always use LIKE patterns, never exact matches
- For counts: Use COUNT(*) for row counts, COUNT(column) for non-null counts  
- For JOINs: Prefer INNER JOIN for required relationships, LEFT JOIN for optional
- For multiple conditions: Use AND/OR appropriately with parentheses

### Request
{query}

### SQL Query (complete and executable)
SELECT"""
        
        return prompt
    
    def _analyze_query_intent(self, query: str) -> Dict[str, str]:
        """
        Analyze query intent to improve prompting strategy.
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with query analysis
        """
        query_lower = query.lower()
        
        # Determine query type
        if any(word in query_lower for word in ['wie viele', 'anzahl', 'count', 'zählen']):
            query_type = 'count_aggregation'
            expected_result = 'numeric count'
        elif any(word in query_lower for word in ['zeige', 'liste', 'alle', 'show', 'list']):
            query_type = 'data_retrieval'
            expected_result = 'table data'
        elif any(word in query_lower for word in ['welche', 'wer', 'wo', 'which', 'who', 'where']):
            query_type = 'filtered_search'
            expected_result = 'filtered results'
        elif any(word in query_lower for word in ['mehr als', 'weniger als', 'größer', 'kleiner']):
            query_type = 'comparison'
            expected_result = 'comparative results'
        else:
            query_type = 'general'
            expected_result = 'data retrieval'
        
        # Determine complexity
        join_indicators = ['und ihre', 'mit', 'von', 'in', 'gehören zu', 'besitzen']
        aggregate_indicators = ['durchschnitt', 'summe', 'maximum', 'minimum', 'gesamt']
        
        complexity_score = 0
        if any(indicator in query_lower for indicator in join_indicators):
            complexity_score += 1
        if any(indicator in query_lower for indicator in aggregate_indicators):
            complexity_score += 1
        if len(query.split()) > 8:
            complexity_score += 1
        
        if complexity_score >= 2:
            complexity = 'high'
        elif complexity_score == 1:
            complexity = 'medium'
        else:
            complexity = 'low'
        
        return {
            'type': query_type,
            'expected_result': expected_result,
            'complexity': complexity
        }
    
    def _identify_relevant_tables(self, query: str) -> List[str]:
        """
        Identify tables relevant to the query using keyword matching and patterns.
        
        Args:
            query: Natural language query
            
        Returns:
            List of relevant table names
        """
        query_lower = query.lower()
        relevant_tables = []
        
        # Keyword-based table identification
        table_keywords = {
            'BEWOHNER': ['bewohner', 'mieter', 'tenant', 'resident', 'wohnt', 'adresse'],
            'EIGENTUEMER': ['eigentümer', 'besitzer', 'owner', 'eigentum'],
            'OBJEKTE': ['objekt', 'immobilie', 'property', 'wohnung', 'haus'],
            'KONTEN': ['konto', 'account', 'finanzen', 'geld', 'betrag'],
            'BUCHUNG': ['buchung', 'zahlung', 'payment', 'transaction'],
            'SOLLSTELLUNG': ['soll', 'forderung', 'debt', 'schuld'],
            'VEREIG': ['besitz', 'eigentum', 'ownership']
        }
        
        for table, keywords in table_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                relevant_tables.append(table)
        
        # If no specific tables identified, add core tables
        if not relevant_tables:
            relevant_tables = ['BEWOHNER', 'OBJEKTE', 'EIGENTUEMER']
        
        return relevant_tables
    
    def _extract_schema_context(self, relevant_tables: List[str]) -> str:
        """
        Extract schema context for relevant tables from parsed documents.
        
        Args:
            relevant_tables: List of table names
            
        Returns:
            Formatted schema context string
        """
        schema_parts = []
        
        for table in relevant_tables:
            # Find schema info in parsed docs
            for doc in self.parsed_docs:
                if (doc.metadata.get('type') == 'yaml_definition' and 
                    table.lower() in doc.page_content.lower()):
                    
                    # Extract key information
                    content = doc.page_content
                    
                    # Extract columns
                    columns_match = re.search(r'Columns:\s*\n(.*?)(?:\nRelations:|$)', content, re.DOTALL)
                    if columns_match:
                        columns_text = columns_match.group(1).strip()
                        schema_parts.append(f"Table {table}:")
                        schema_parts.append(columns_text)
                        schema_parts.append("")  # Empty line for readability
                    break
        
        return "\n".join(schema_parts) if schema_parts else f"Schema information for tables: {', '.join(relevant_tables)}"
    
    def _generate_sql_with_model(self, prompt: str) -> str:
        """
        Generate SQL using the loaded SQLCoder-2 model.
        
        Args:
            prompt: Formatted prompt for SQL generation
            
        Returns:
            Generated SQL query
        """
        if not self.model_loaded or not self.model or not self.tokenizer:
            logger.error("Model not loaded, cannot generate SQL")
            return "-- Model not available"
        
        try:
            start_time = time.time()
            
            # Tokenize input
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=2048
            )
            
            # Move to appropriate device
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Generate SQL
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    temperature=self.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            generated_tokens = outputs[0][inputs['input_ids'].shape[1]:]
            generated_sql = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            # Clean up SQL
            generated_sql = self._clean_generated_sql(generated_sql)
            
            generation_time = time.time() - start_time
            
            # Track generation metrics
            if self.monitor:
                self.monitor.track_llm_call(
                    model=self.model_name,
                    prompt=prompt[:500],
                    response=generated_sql,
                    tokens_used=len(generated_tokens),
                    cost=0.0,  # No cost for local model
                    duration=generation_time
                )
            
            logger.info(f"Generated SQL in {generation_time:.2f}s: {generated_sql[:100]}...")
            return f"SELECT{generated_sql}"
            
        except Exception as e:
            logger.error(f"Error generating SQL with SQLCoder-2: {e}")
            return f"-- Error generating SQL: {str(e)}"
    
    def _clean_generated_sql(self, sql: str) -> str:
        """
        Clean and validate generated SQL.
        
        Args:
            sql: Raw generated SQL
            
        Returns:
            Cleaned SQL query
        """
        # Remove extra whitespace and line breaks
        sql = " ".join(sql.split())
        
        # Ensure proper SQL termination
        sql = sql.rstrip(';')
        
        # Basic validation - ensure it's a SELECT query
        sql_upper = sql.upper()
        if not sql_upper.startswith('SELECT'):
            sql = f"SELECT {sql}"
        
        # Fix common Firebird syntax issues
        sql = re.sub(r'\bLIMIT\s+(\d+)', r'FIRST \1', sql, flags=re.IGNORECASE)
        
        return sql
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Generate SQL using SQLCoder-2 with JOIN-aware prompting.
        
        Args:
            query: Natural language query
            
        Returns:
            List containing a single document with the generated SQL
        """
        start_time = time.time()
        
        try:
            # Identify relevant tables
            relevant_tables = self._identify_relevant_tables(query)
            logger.info(f"Identified relevant tables: {relevant_tables}")
            
            # Extract schema context
            schema_context = self._extract_schema_context(relevant_tables)
            
            # Build JOIN-aware prompt
            prompt = self._build_join_aware_prompt(query, schema_context, relevant_tables)
            
            # Generate SQL
            generated_sql = self._generate_sql_with_model(prompt)
            
            # Create document with generated SQL
            sql_document = Document(
                page_content=f"Generated SQL Query:\n{generated_sql}\n\nRelevant Tables: {', '.join(relevant_tables)}",
                metadata={
                    'source': 'sqlcoder2_generation',
                    'type': 'generated_sql',
                    'model': self.model_name,
                    'tables': relevant_tables,
                    'generation_time': time.time() - start_time,
                    'prompt_length': len(prompt)
                }
            )
            
            # Track retrieval metrics
            if self.monitor:
                self.monitor.track_retrieval(
                    retrieval_mode='sqlcoder',
                    query=query,
                    documents_retrieved=1,
                    relevance_scores=[1.0],  # High relevance for generated SQL
                    duration=time.time() - start_time,
                    success=True
                )
            
            return [sql_document]
            
        except Exception as e:
            logger.error(f"Error in SQLCoder retrieval: {e}")
            
            # Track failed retrieval
            if self.monitor:
                self.monitor.track_retrieval(
                    retrieval_mode='sqlcoder',
                    query=query,
                    documents_retrieved=0,
                    relevance_scores=[],
                    duration=time.time() - start_time,
                    success=False
                )
            
            # Return error document
            error_document = Document(
                page_content=f"Error generating SQL: {str(e)}",
                metadata={
                    'source': 'sqlcoder2_error',
                    'type': 'error',
                    'error': str(e)
                }
            )
            
            return [error_document]


# Utility functions for defaultdict import
from collections import defaultdict


def test_sqlcoder_retriever():
    """Test function for SQLCoder retriever."""
    print("Testing SQLCoder Retriever...")
    
    # Create test documents
    test_docs = [
        Document(
            page_content="""Entity Name: BEWOHNER
Description: Tenant information table
Columns:
  - BWO (Type: INTEGER): Object reference number
  - BSTR (Type: VARCHAR): Street address with house number
  - BPLZORT (Type: VARCHAR): ZIP code and city
Relations:
  - BEWOHNER -> OBJEKTE: BWO = ONR""",
            metadata={'type': 'yaml_definition', 'source': 'bewohner.yaml'}
        )
    ]
    
    # Initialize retriever
    retriever = SQLCoderRetriever(
        model_name="defog/sqlcoder2",
        parsed_docs=test_docs,
        use_quantization=True
    )
    
    # Test queries
    test_queries = [
        "Wie viele Bewohner gibt es?",
        "Zeige mir Bewohner in der Marienstraße",
        "Welche Eigentümer haben mehr als 2 Objekte?"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        docs = retriever.get_relevant_documents(query)
        for doc in docs:
            print(f"Generated: {doc.page_content}")
            print(f"Metadata: {doc.metadata}")


if __name__ == "__main__":
    test_sqlcoder_retriever()