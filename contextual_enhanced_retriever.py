#!/usr/bin/env python3
"""
Contextual Enhanced Retriever - Optimized version of Enhanced Multi-Stage Retriever

Key improvements over original Enhanced mode:
1. Query-Type-based document filtering (address_lookup, financial, owner, etc.)
2. HV-Domain contextual chunks with business purpose
3. Anthropic-style chunk enrichment for better context understanding
4. Reduces information overload from static 9-document selection

This addresses Task 1.1: Enhanced → Contextual Enhanced
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Set
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Import SQL execution components
from sql_execution_engine import SQLExecutionEngine, SQLExecutionResult
from adaptive_tag_classifier import AdaptiveTAGClassifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueryContext:
    """Context information extracted from query analysis."""
    query_type: str
    identified_entities: List[str]
    required_tables: List[str]
    business_context: str
    confidence_score: float


@dataclass 
class ContextualChunk:
    """Enhanced chunk with business context and relationships."""
    content: str
    table_name: str
    business_purpose: str
    technical_details: str
    relationships: List[str]
    query_types: List[str]  # Which query types this chunk is relevant for


@dataclass
class ContextualEnhancedResult:
    """Result from Contextual Enhanced Retriever with SQL execution."""
    documents: List[Document]
    sql_query: str
    execution_result: SQLExecutionResult
    query_context: QueryContext
    retrieval_time: float


class QueryTypeClassifier:
    """Classifies queries into specific types for targeted document retrieval."""
    
    QUERY_TYPE_PATTERNS = {
        "address_lookup": {
            "keywords": ["wohnt", "bewohner", "mieter", "straße", "str.", "adresse", "plz"],
            "tables": ["BEWOHNER", "BEWADR"],
            "business_context": "Suche nach Bewohnern/Mietern basierend auf Adressinformationen"
        },
        "owner_lookup": {
            "keywords": ["eigentümer", "besitzer", "verwalter", "hauseigentümer"],
            "tables": ["EIGENTUEMER", "EIGADR", "VEREIG"],
            "business_context": "Suche nach Eigentümern und deren Verwaltungsbeziehungen"
        },
        "financial_query": {
            "keywords": ["miete", "kosten", "buchung", "zahlung", "saldo", "konto", "durchschnitt"],
            "tables": ["KONTEN", "BUCHUNG", "SOLLSTELLUNG"],
            "business_context": "Finanzielle Abfragen zu Mieten, Kosten und Zahlungen"
        },
        "property_count": {
            "keywords": ["anzahl", "viele", "count", "wohnungen", "objekte"],
            "tables": ["WOHNUNG", "OBJEKTE"],
            "business_context": "Zählung und Statistiken zu Immobilien und Wohnungen"
        },
        "general_property": {
            "keywords": ["objekt", "gebäude", "haus", "wohnung", "immobilie"],
            "tables": ["OBJEKTE", "WOHNUNG", "BEWOHNER"],
            "business_context": "Allgemeine Immobilien- und Objektinformationen"
        }
    }
    
    def classify_query(self, query: str) -> QueryContext:
        """
        Classify query into specific type for targeted retrieval.
        
        Args:
            query: Natural language query
            
        Returns:
            QueryContext with classification results
        """
        query_lower = query.lower()
        scores = {}
        
        # Score each query type based on keyword matches
        for query_type, pattern in self.QUERY_TYPE_PATTERNS.items():
            score = 0
            matched_keywords = []
            
            for keyword in pattern["keywords"]:
                if keyword in query_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                scores[query_type] = {
                    "score": score / len(pattern["keywords"]),
                    "matched_keywords": matched_keywords,
                    "tables": pattern["tables"],
                    "business_context": pattern["business_context"]
                }
        
        if not scores:
            # Default to general_property for unknown queries
            best_type = "general_property"
            best_info = self.QUERY_TYPE_PATTERNS[best_type]
            confidence = 0.3
            entities = []
        else:
            # Get best match
            best_type = max(scores.keys(), key=lambda k: scores[k]["score"])
            best_info = scores[best_type]
            confidence = best_info["score"]
            entities = best_info["matched_keywords"]
        
        return QueryContext(
            query_type=best_type,
            identified_entities=entities,
            required_tables=best_info["tables"],
            business_context=best_info["business_context"],
            confidence_score=confidence
        )


class HVDomainChunkEnricher:
    """Creates HV-domain contextual chunks with business purpose and relationships."""
    
    def __init__(self):
        """Initialize with Hausverwaltung domain knowledge."""
        # Top-10 Tabellen mit Geschäftskontext anreichern
        self.table_business_contexts = {
            "BEWOHNER": {
                "business_purpose": "Zentrale Mieterdatenbank - enthält alle aktuellen und ehemaligen Bewohner",
                "key_relationships": ["BEWADR (Adressen)", "OBJEKTE (über ONR)", "KONTEN (Mietzahlungen)"],
                "critical_columns": "BSTR (Straße+Hausnummer), BPLZORT (PLZ+Ort), BNAME/BVNAME (Name)",
                "business_rules": "IMMER LIKE-Pattern für Adressen verwenden"
            },
            "EIGENTUEMER": {
                "business_purpose": "Eigentümerdatenbank - rechtliche Besitzverhältnisse und Kontaktdaten",
                "key_relationships": ["EIGADR (Adressen)", "VEREIG (Besitzverhältnisse)", "OBJEKTE"],
                "critical_columns": "NAME, VNAME für Eigentümeridentifikation",
                "business_rules": "Verbindung zu Objekten über VEREIG-Tabelle"
            },
            "OBJEKTE": {
                "business_purpose": "Immobilienobjekte - Gebäude und deren Grunddaten",
                "key_relationships": ["WOHNUNG (Einzelwohnungen)", "BEWOHNER (über ONR)", "EIGENTUEMER"],
                "critical_columns": "ONR (Objektnummer) ist zentrale Verknüpfung",
                "business_rules": "ONR verknüpft Objekte mit Bewohnern, Eigentümern und Konten"
            },
            "WOHNUNG": {
                "business_purpose": "Einzelne Wohneinheiten innerhalb der Objekte",
                "key_relationships": ["OBJEKTE (Gebäudezuordnung)", "BEWOHNER (Mietverhältnisse)"],
                "critical_columns": "Wohnungsnummer, Größe, Ausstattungsmerkmale",
                "business_rules": "Für Zählungen und Statistiken verwenden"
            },
            "KONTEN": {
                "business_purpose": "Finanzkonten für Mietzahlungen und Hausgeld",
                "key_relationships": ["BUCHUNG (Kontobewegungen)", "OBJEKTE (über ONR)"],
                "critical_columns": "ONR für Objektzuordnung, Kontosaldo",
                "business_rules": "Zentral für alle finanziellen Abfragen"
            }
        }
    
    def enrich_document(self, doc: Document, table_name: str) -> ContextualChunk:
        """
        Enrich document with HV-domain business context.
        
        Args:
            doc: Original document
            table_name: Database table name
            
        Returns:
            ContextualChunk with enriched context
        """
        # Get business context for table
        business_info = self.table_business_contexts.get(table_name, {
            "business_purpose": f"Database table: {table_name}",
            "key_relationships": [],
            "critical_columns": "Standard database columns",
            "business_rules": "Standard SQL operations"
        })
        
        # Determine relevant query types
        relevant_query_types = []
        table_upper = table_name.upper()
        
        if table_upper in ["BEWOHNER", "BEWADR"]:
            relevant_query_types.extend(["address_lookup", "general_property"])
        if table_upper in ["EIGENTUEMER", "EIGADR", "VEREIG"]:
            relevant_query_types.extend(["owner_lookup", "general_property"])
        if table_upper in ["KONTEN", "BUCHUNG", "SOLLSTELLUNG"]:
            relevant_query_types.extend(["financial_query"])
        if table_upper in ["WOHNUNG", "OBJEKTE"]:
            relevant_query_types.extend(["property_count", "general_property"])
        
        if not relevant_query_types:
            relevant_query_types = ["general_property"]
        
        # Create enriched chunk with Anthropic-style context
        enhanced_content = f"""
HAUSVERWALTUNG TABLE: {table_name}

BUSINESS PURPOSE: {business_info['business_purpose']}

TECHNICAL DETAILS: {doc.page_content}

KEY RELATIONSHIPS: {', '.join(business_info['key_relationships'])}

CRITICAL COLUMNS: {business_info['critical_columns']}

BUSINESS RULES: {business_info['business_rules']}

RELEVANT FOR: {', '.join(relevant_query_types)} queries
"""
        
        return ContextualChunk(
            content=enhanced_content,
            table_name=table_name,
            business_purpose=business_info['business_purpose'],
            technical_details=doc.page_content,
            relationships=business_info['key_relationships'],
            query_types=relevant_query_types
        )


class ContextualEnhancedRetriever:
    """
    Contextual Enhanced Retriever - addresses Enhanced mode's information overload.
    
    Key improvements:
    1. Query-type classification for targeted document selection
    2. Business-context-enriched chunks instead of raw technical docs
    3. 3-5 relevant docs instead of overwhelming 9-document selection
    4. SQL generation and execution using retrieved schema documents
    5. Real database results instead of text generation
    """
    
    def __init__(self, documents: List[Document], openai_api_key: str, 
                 db_connection_string: str = None, llm: BaseLanguageModel = None):
        """
        Initialize Contextual Enhanced Retriever.
        
        Args:
            documents: Original document collection
            openai_api_key: OpenAI API key for embeddings
            db_connection_string: Database connection for SQL execution
            llm: Language model for SQL generation
        """
        self.openai_api_key = openai_api_key
        self.db_connection_string = db_connection_string or "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
        self.llm = llm
        
        self.classifier = QueryTypeClassifier()
        self.enricher = HVDomainChunkEnricher()
        
        # Initialize SQL execution engine
        self.sql_engine = SQLExecutionEngine(self.db_connection_string)
        
        # Initialize learning components
        self.tag_classifier = AdaptiveTAGClassifier()
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=openai_api_key,
            dimensions=1536  # Optimized for performance
        )
        
        # Process and enrich documents
        logger.info("Processing %d documents for contextual enrichment", len(documents))
        self.contextual_chunks = self._process_documents(documents)
        
        # Create query-type-specific vector stores
        self._create_specialized_stores()
        
        logger.info("Contextual Enhanced Retriever initialized with %d enriched chunks", 
                   len(self.contextual_chunks))
    
    def _process_documents(self, documents: List[Document]) -> List[ContextualChunk]:
        """Process documents into contextual chunks."""
        chunks = []
        
        for doc in documents:
            # Extract table name from document metadata or content
            table_name = self._extract_table_name(doc)
            
            # Enrich with business context
            enriched_chunk = self.enricher.enrich_document(doc, table_name)
            chunks.append(enriched_chunk)
        
        return chunks
    
    def _extract_table_name(self, doc: Document) -> str:
        """Extract table name from document."""
        # Try metadata first
        if hasattr(doc, 'metadata') and 'table_name' in doc.metadata:
            return doc.metadata['table_name']
        
        # Try to parse from content
        content = doc.page_content.upper()
        for table in self.enricher.table_business_contexts.keys():
            if table in content:
                return table
        
        return "UNKNOWN"
    
    def _create_specialized_stores(self):
        """Create specialized vector stores for each query type."""
        self.query_type_stores = {}
        
        for query_type in self.classifier.QUERY_TYPE_PATTERNS.keys():
            # Get chunks relevant for this query type
            relevant_chunks = [
                chunk for chunk in self.contextual_chunks 
                if query_type in chunk.query_types
            ]
            
            if relevant_chunks:
                # Create documents for FAISS
                docs = [
                    Document(page_content=chunk.content, metadata={
                        "table_name": chunk.table_name,
                        "query_type": query_type,
                        "business_purpose": chunk.business_purpose
                    })
                    for chunk in relevant_chunks
                ]
                
                # Create FAISS store
                store = FAISS.from_documents(docs, self.embeddings)
                self.query_type_stores[query_type] = store
                
                logger.info("Created store for %s with %d documents", 
                           query_type, len(docs))
    
    def retrieve_contextual_documents(self, query: str, k: int = 4) -> List[Document]:
        """
        Retrieve contextually relevant documents based on query type.
        
        Args:
            query: Natural language query
            k: Number of documents to retrieve (default 4, much less than Enhanced's 9)
            
        Returns:
            List of most relevant contextual documents
        """
        start_time = time.time()
        
        # Classify query
        query_context = self.classifier.classify_query(query)
        
        logger.info("Query classified as: %s (confidence: %.2f)", 
                   query_context.query_type, query_context.confidence_score)
        
        # Get specialized store for query type
        store = self.query_type_stores.get(query_context.query_type)
        
        if not store:
            logger.warning("No specialized store for %s, using general_property", 
                          query_context.query_type)
            store = self.query_type_stores.get("general_property")
        
        if not store:
            logger.error("No stores available for retrieval")
            return []
        
        # Retrieve targeted documents (much fewer than Enhanced's 9)
        docs = store.similarity_search(query, k=k)
        
        retrieval_time = time.time() - start_time
        logger.info("Contextual retrieval completed: %d docs in %.2fs for %s queries",
                   len(docs), retrieval_time, query_context.query_type)
        
        return docs
    
    def retrieve(self, query: str, k: int = 4) -> ContextualEnhancedResult:
        """
        Complete retrieval with SQL generation and execution.
        
        Args:
            query: Natural language query
            k: Number of documents to retrieve
            
        Returns:
            ContextualEnhancedResult with documents, SQL, and database results
        """
        start_time = time.time()
        
        try:
            # Step 1: Retrieve relevant schema documents
            retrieved_docs = self.retrieve_contextual_documents(query, k)
            query_context = self.classifier.classify_query(query)
            
            if not retrieved_docs:
                raise Exception("No relevant documents found for query")
            
            # Step 2: Generate SQL using retrieved schema documents and LLM
            sql_query = self._generate_sql_from_documents(query, retrieved_docs, query_context)
            
            # Step 3: Execute SQL against real database
            execution_result = self.sql_engine.execute_query(sql_query)
            
            # Step 4: Learn from execution results
            self._learn_from_execution(query, query_context.query_type, sql_query, execution_result.success)
            
            retrieval_time = time.time() - start_time
            
            return ContextualEnhancedResult(
                documents=retrieved_docs,
                sql_query=sql_query,
                execution_result=execution_result,
                query_context=query_context,
                retrieval_time=retrieval_time
            )
            
        except Exception as e:
            logger.error(f"Contextual Enhanced retrieval failed: {e}")
            retrieval_time = time.time() - start_time
            
            # Return error result
            error_result = SQLExecutionResult(
                success=False,
                query="",
                data=[],
                columns=[],
                row_count=0,
                execution_time=0.0,
                formatted_answer=f"Error: {str(e)}",
                error=str(e)
            )
            
            return ContextualEnhancedResult(
                documents=[],
                sql_query="",
                execution_result=error_result,
                query_context=QueryContext("error", [], [], str(e), 0.0),
                retrieval_time=retrieval_time
            )
    
    def _generate_sql_from_documents(self, query: str, documents: List[Document], 
                                   query_context: QueryContext) -> str:
        """
        Generate SQL query using retrieved schema documents and LLM.
        
        Args:
            query: Original natural language query
            documents: Retrieved schema documents
            query_context: Query classification context
            
        Returns:
            Generated SQL query string
        """
        if not self.llm:
            raise Exception("LLM not provided for SQL generation")
        
        # Build context from retrieved documents
        schema_context = "\n\n".join([
            f"SCHEMA INFO: {doc.page_content}" for doc in documents
        ])
        
        # Create enhanced prompt for SQL generation
        sql_generation_prompt = f"""
You are a SQL expert for WINCASA Hausverwaltung database queries. Generate accurate Firebird SQL.

QUERY CONTEXT:
- Query Type: {query_context.query_type}
- Required Tables: {', '.join(query_context.required_tables)}
- Business Context: {query_context.business_context}
- Confidence: {query_context.confidence_score:.2f}

RELEVANT SCHEMA INFORMATION:
{schema_context}

FIREBIRD SQL RULES:
- Use SELECT for all queries
- Use LIKE '%pattern%' for text searches
- Table/column names are case-sensitive
- Use proper JOINs for relationships
- Use FIRST n instead of LIMIT n
- For address searches: BSTR contains 'street number', BPLZORT contains 'postal city'

GENERATE SQL FOR: {query}

Return only the SQL query, no explanations:"""
        
        # Generate SQL using LLM
        messages = [
            {"role": "system", "content": "You are a SQL expert. Generate only valid Firebird SQL queries."},
            {"role": "user", "content": sql_generation_prompt}
        ]
        
        llm_response = self.llm.invoke(messages)
        sql_query = self._extract_sql_from_response(llm_response.content)
        
        logger.info(f"Generated SQL for {query_context.query_type}: {sql_query}")
        return sql_query
    
    def _extract_sql_from_response(self, response: str) -> str:
        """
        Extract clean SQL from LLM response.
        
        Args:
            response: LLM response containing SQL
            
        Returns:
            Clean SQL query
        """
        # Remove markdown code blocks
        if "```sql" in response:
            sql = response.split("```sql")[1].split("```")[0].strip()
        elif "```" in response:
            sql = response.split("```")[1].split("```")[0].strip()
        else:
            sql = response.strip()
        
        # Clean up the SQL
        lines = [line.strip() for line in sql.split('\n') if line.strip()]
        sql = ' '.join(lines)
        
        return sql
    
    def _learn_from_execution(self, query: str, query_type: str, sql: str, success: bool):
        """
        Learn from SQL execution results to improve future retrievals.
        
        Args:
            query: Original query
            query_type: Classified query type
            sql: Generated SQL
            success: Whether execution was successful
        """
        # Feed learning back to TAG classifier
        if hasattr(self.tag_classifier, 'learn_from_success'):
            self.tag_classifier.learn_from_success(query, query_type, sql, success)
            
        logger.info(f"Learning: {query_type} query {'succeeded' if success else 'failed'}")
    
    def get_response(self, query: str) -> str:
        """
        Get formatted response for compatibility with benchmark framework.
        
        Args:
            query: Natural language query
            
        Returns:
            Formatted response string
        """
        result = self.retrieve(query)
        return result.execution_result.formatted_answer
    
    def retrieve_contextual_documents(self, query: str, k: int = 4) -> List[Document]:
        """
        Retrieve contextually relevant schema documents for SQL generation.
        
        This is the baseline document retrieval that feeds the LLM to formulate SQL queries.
        
        Args:
            query: Natural language query
            k: Number of schema documents to retrieve for SQL context
            
        Returns:
            List of most relevant schema documents for SQL generation
        """
        start_time = time.time()
        
        # Classify query
        query_context = self.classifier.classify_query(query)
        
        logger.info("Query classified as: %s (confidence: %.2f)", 
                   query_context.query_type, query_context.confidence_score)
        
        # Get specialized store for query type
        store = self.query_type_stores.get(query_context.query_type)
        
        if not store:
            logger.warning("No specialized store for %s, using general_property", 
                          query_context.query_type)
            store = self.query_type_stores.get("general_property")
        
        if not store:
            logger.error("No stores available for retrieval")
            return []
        
        # Retrieve targeted schema documents for SQL generation
        docs = store.similarity_search(query, k=k)
        
        retrieval_time = time.time() - start_time
        logger.info("Retrieved %d schema documents in %.2fs for SQL generation",
                   len(docs), retrieval_time)
        
        return docs


def create_contextual_enhanced_retriever(documents: List[Document], 
                                       openai_api_key: str,
                                       db_connection_string: str = None,
                                       llm: BaseLanguageModel = None) -> ContextualEnhancedRetriever:
    """
    Factory function to create Contextual Enhanced Retriever.
    
    Args:
        documents: Document collection
        openai_api_key: OpenAI API key
        db_connection_string: Database connection for SQL execution
        llm: Language model for SQL generation
        
    Returns:
        Configured ContextualEnhancedRetriever instance
    """
    return ContextualEnhancedRetriever(documents, openai_api_key, db_connection_string, llm)


if __name__ == "__main__":
    # Quick test of the classifier
    classifier = QueryTypeClassifier()
    
    test_queries = [
        "Wer wohnt in der Marienstr. 26, 45307 Essen",
        "Liste aller Eigentümer", 
        "Durchschnittliche Miete in Essen",
        "Wie viele Wohnungen gibt es insgesamt?"
    ]
    
    print("🧪 Testing Contextual Enhanced Query Classification")
    print("=" * 60)
    
    for query in test_queries:
        context = classifier.classify_query(query)
        print(f"\nQuery: {query}")
        print(f"Type: {context.query_type}")
        print(f"Confidence: {context.confidence_score:.2f}")
        print(f"Tables: {context.required_tables}")
        print(f"Business Context: {context.business_context}")