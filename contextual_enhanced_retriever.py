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
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import OpenAIEmbeddings

from adaptive_tag_classifier import AdaptiveTAGClassifier

# Import SQL execution components
from sql_execution_engine import SQLExecutionEngine, SQLExecutionResult

# Import SQL reliability improvements
from sql_generation_retry import SQLGenerationRetryEngine
from sql_prompt_templates import SQLPromptTemplates
from sql_response_processor import SQLResponseProcessor

# Import pattern matching and learning integration
from wincasa_full_pattern_matcher import WINCASAFullPatternMatcher
from learning_integration import LearningIntegration

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
            "keywords": [
                "wohnt",
                "bewohner",
                "mieter",
                "straße",
                "str.",
                "adresse",
                "plz",
            ],
            "tables": ["BEWOHNER", "BEWADR"],
            "business_context": (
                "Suche nach Bewohnern/Mietern basierend auf Adressinformationen"
            ),
        },
        "owner_lookup": {
            "keywords": ["eigentümer", "besitzer", "verwalter", "hauseigentümer"],
            "tables": ["EIGENTUEMER", "EIGADR", "VEREIG"],
            "business_context": (
                "Suche nach Eigentümern und deren Verwaltungsbeziehungen"
            ),
        },
        "financial_query": {
            "keywords": [
                "miete",
                "kosten",
                "buchung",
                "zahlung",
                "saldo",
                "konto",
                "durchschnitt",
            ],
            "tables": ["KONTEN", "BUCHUNG", "SOLLSTELLUNG"],
            "business_context": "Finanzielle Abfragen zu Mieten, Kosten und Zahlungen",
        },
        "property_count": {
            "keywords": ["anzahl", "viele", "count", "wohnungen", "objekte"],
            "tables": ["WOHNUNG", "OBJEKTE"],
            "business_context": "Zählung und Statistiken zu Immobilien und Wohnungen",
        },
        "general_property": {
            "keywords": ["objekt", "gebäude", "haus", "wohnung", "immobilie"],
            "tables": ["OBJEKTE", "WOHNUNG", "BEWOHNER"],
            "business_context": "Allgemeine Immobilien- und Objektinformationen",
        },
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
                    "business_context": pattern["business_context"],
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
            confidence_score=confidence,
        )


class HVDomainChunkEnricher:
    """Creates HV-domain contextual chunks with business purpose and relationships."""

    def __init__(self):
        """Initialize with Hausverwaltung domain knowledge."""
        # Top-10 Tabellen mit Geschäftskontext anreichern
        self.table_business_contexts = {
            "BEWOHNER": {
                "business_purpose": (
                    "Zentrale Mieterdatenbank - enthält alle aktuellen und ehemaligen Bewohner"
                ),
                "key_relationships": [
                    "BEWADR (Adressen)",
                    "OBJEKTE (über ONR)",
                    "KONTEN (Mietzahlungen)",
                ],
                "critical_columns": (
                    "Street/address columns, postal/city columns, name columns - discovered dynamically"
                ),
                "business_rules": "IMMER LIKE-Pattern für Adressen verwenden",
            },
            "EIGENTUEMER": {
                "business_purpose": (
                    "Eigentümerdatenbank - rechtliche Besitzverhältnisse und Kontaktdaten"
                ),
                "key_relationships": [
                    "EIGADR (Adressen)",
                    "VEREIG (Besitzverhältnisse)",
                    "OBJEKTE",
                ],
                "critical_columns": "NAME, VNAME für Eigentümeridentifikation",
                "business_rules": "Verbindung zu Objekten über VEREIG-Tabelle",
            },
            "OBJEKTE": {
                "business_purpose": "Immobilienobjekte - Gebäude und deren Grunddaten",
                "key_relationships": [
                    "WOHNUNG (Einzelwohnungen)",
                    "BEWOHNER (über ONR)",
                    "EIGENTUEMER",
                ],
                "critical_columns": "ONR (Objektnummer) ist zentrale Verknüpfung",
                "business_rules": (
                    "ONR verknüpft Objekte mit Bewohnern, Eigentümern und Konten"
                ),
            },
            "WOHNUNG": {
                "business_purpose": "Einzelne Wohneinheiten innerhalb der Objekte",
                "key_relationships": [
                    "OBJEKTE (Gebäudezuordnung)",
                    "BEWOHNER (Mietverhältnisse)",
                ],
                "critical_columns": "Wohnungsnummer, Größe, Ausstattungsmerkmale",
                "business_rules": "Für Zählungen und Statistiken verwenden",
            },
            "KONTEN": {
                "business_purpose": "Finanzkonten für Mietzahlungen und Hausgeld",
                "key_relationships": [
                    "BUCHUNG (Kontobewegungen)",
                    "OBJEKTE (über ONR)",
                ],
                "critical_columns": "ONR für Objektzuordnung, Kontosaldo",
                "business_rules": "Zentral für alle finanziellen Abfragen",
            },
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
        business_info = self.table_business_contexts.get(
            table_name,
            {
                "business_purpose": f"Database table: {table_name}",
                "key_relationships": [],
                "critical_columns": "Standard database columns",
                "business_rules": "Standard SQL operations",
            },
        )

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
            business_purpose=business_info["business_purpose"],
            technical_details=doc.page_content,
            relationships=business_info["key_relationships"],
            query_types=relevant_query_types,
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

    def __init__(
        self,
        documents: List[Document],
        openai_api_key: str,
        db_connection_string: str = None,
        llm: BaseLanguageModel = None,
    ):
        """
        Initialize Contextual Enhanced Retriever.

        Args:
            documents: Original document collection
            openai_api_key: OpenAI API key for embeddings
            db_connection_string: Database connection for SQL execution
            llm: Language model for SQL generation
        """
        self.openai_api_key = openai_api_key
        self.db_connection_string = (
            db_connection_string
            or "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
        )
        self.llm = llm

        self.classifier = QueryTypeClassifier()
        self.enricher = HVDomainChunkEnricher()

        # Initialize SQL execution engine
        self.sql_engine = SQLExecutionEngine(self.db_connection_string)
        
        # Initialize SQL generation retry engine for reliability
        self.sql_retry_engine = SQLGenerationRetryEngine(max_retries=3)

        # Initialize pattern matching for SQL generation
        self.pattern_matcher = WINCASAFullPatternMatcher()
        logger.info(f"Loaded {len(self.pattern_matcher.working_queries)} SQL patterns")
        
        # Initialize learning integration for adaptive optimization
        self.learning_integration = LearningIntegration()
        logger.info("Learning integration enabled for adaptive pattern selection")

        # Initialize learning components
        self.tag_classifier = AdaptiveTAGClassifier()

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=openai_api_key,
            dimensions=1536,  # Optimized for performance
        )
        
        # Vector store caching
        self._vector_cache_dir = Path("vector_cache")
        self._vector_cache_dir.mkdir(exist_ok=True)

        # Process and enrich documents
        logger.info("Processing %d documents for contextual enrichment", len(documents))
        self.contextual_chunks = self._process_documents(documents)

        # Create query-type-specific vector stores
        self._create_specialized_stores()

        logger.info(
            "Contextual Enhanced Retriever initialized with %d enriched chunks",
            len(self.contextual_chunks),
        )

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
        if hasattr(doc, "metadata") and "table_name" in doc.metadata:
            return doc.metadata["table_name"]

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
                chunk
                for chunk in self.contextual_chunks
                if query_type in chunk.query_types
            ]

            if relevant_chunks:
                # Create documents for FAISS
                docs = [
                    Document(
                        page_content=chunk.content,
                        metadata={
                            "table_name": chunk.table_name,
                            "query_type": query_type,
                            "business_purpose": chunk.business_purpose,
                        },
                    )
                    for chunk in relevant_chunks
                ]

                # Create FAISS store with caching
                store = self._get_or_create_faiss_store(query_type, docs)
                self.query_type_stores[query_type] = store

                logger.info(
                    "Created store for %s with %d documents", query_type, len(docs)
                )

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

        logger.info(
            "Query classified as: %s (confidence: %.2f)",
            query_context.query_type,
            query_context.confidence_score,
        )

        # Get specialized store for query type
        store = self.query_type_stores.get(query_context.query_type)

        if not store:
            logger.warning(
                "No specialized store for %s, using general_property",
                query_context.query_type,
            )
            store = self.query_type_stores.get("general_property")

        if not store:
            logger.error("No stores available for retrieval")
            return []

        # Retrieve targeted documents (much fewer than Enhanced's 9)
        docs = store.similarity_search(query, k=k)

        retrieval_time = time.time() - start_time
        logger.info(
            "Contextual retrieval completed: %d docs in %.2fs for %s queries",
            len(docs),
            retrieval_time,
            query_context.query_type,
        )

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
            sql_query = self._generate_sql_from_documents(
                query, retrieved_docs, query_context
            )

            # Step 3: Execute SQL against real database
            execution_result = self.sql_engine.execute_query(sql_query)
            
            # Store execution metrics for learning
            self._last_execution_time = execution_result.execution_time
            self._last_result_count = execution_result.row_count

            # Step 4: Learn from execution results
            self._learn_from_execution(
                query, query_context.query_type, sql_query, execution_result.success
            )

            retrieval_time = time.time() - start_time

            return ContextualEnhancedResult(
                documents=retrieved_docs,
                sql_query=sql_query,
                execution_result=execution_result,
                query_context=query_context,
                retrieval_time=retrieval_time,
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
                error=str(e),
            )

            return ContextualEnhancedResult(
                documents=[],
                sql_query="",
                execution_result=error_result,
                query_context=QueryContext("error", [], [], str(e), 0.0),
                retrieval_time=retrieval_time,
            )

    def _generate_sql_from_documents(
        self, query: str, documents: List[Document], query_context: QueryContext
    ) -> str:
        """
        Generate SQL query using pattern matching first, then LLM with retry mechanism.

        Args:
            query: Original natural language query
            documents: Retrieved schema documents
            query_context: Query classification context

        Returns:
            Generated SQL query string
        """
        # Step 1: Try pattern matching first
        if hasattr(self, 'pattern_matcher'):
            pattern_result = self.pattern_matcher.get_pattern_for_llm(query)
            
            if pattern_result['status'] == 'success':
                # Pattern matcher doesn't provide confidence, so we use 0.9 for successful matches
                pattern_confidence = 0.9
                
                logger.info(
                    f"Pattern match successful: {pattern_result['pattern_name']} "
                    f"(purpose: {pattern_result['pattern_purpose']})"
                )
                
                # Use the adapted SQL from pattern
                adapted_sql = pattern_result['adapted_sql']
                
                # If we have learning integration, get adaptive scores
                if hasattr(self, 'learning_integration'):
                    recommendations = self.learning_integration.get_pattern_recommendations(query)
                    adaptive_score = recommendations.get('adaptive_score', 0.5)
                    
                    # Use pattern if high confidence or good adaptive score
                    if pattern_confidence > 0.7 or adaptive_score > 0.6:
                        logger.info(f"Using pattern-based SQL (adaptive score: {adaptive_score:.2f})")
                        self._last_pattern_used = pattern_result['pattern_name']
                        return adapted_sql
                else:
                    # No learning, use pattern if high confidence
                    if pattern_confidence > 0.7:
                        logger.info("Using pattern-based SQL")
                        self._last_pattern_used = pattern_result['pattern_name']
                        return adapted_sql
                
                logger.info("Pattern confidence too low, falling back to LLM generation")
        
        # Step 2: Fall back to LLM generation if no pattern or low confidence
        self._last_pattern_used = None  # Clear pattern tracking when using LLM
        
        if not self.llm:
            raise Exception("LLM not provided for SQL generation")

        # Build context from retrieved documents
        schema_context = "\n\n".join(
            [f"SCHEMA INFO: {doc.page_content}" for doc in documents]
        )

        # Use retry engine for reliable SQL generation
        result = self.sql_retry_engine.generate_sql_with_retry(
            llm=self.llm,
            query=query,
            query_type=query_context.query_type,
            schema_context=schema_context,
            tables=query_context.required_tables
        )

        if result.success and result.final_sql:
            logger.info(
                f"Generated SQL for {query_context.query_type} after {len(result.attempts)} attempts: {result.final_sql}"
            )
            return result.final_sql
        else:
            # Log failure details
            logger.error(
                f"Failed to generate SQL after {len(result.attempts)} attempts. "
                f"Last error: {result.attempts[-1]['validation_error'] if result.attempts else 'No attempts'}"
            )
            # Return a safe error query
            return "SELECT 'SQL generation failed' AS error FROM RDB$DATABASE;"

    def _extract_sql_from_response(self, response: str) -> str:
        """
        Extract clean SQL from LLM response using enhanced processor.

        Args:
            response: LLM response containing SQL

        Returns:
            Clean SQL query
        """
        # Use the enhanced SQL response processor
        processor = SQLResponseProcessor()
        extracted_sql = processor.extract_clean_sql(response)
        
        if extracted_sql:
            return extracted_sql
        else:
            # Fallback to basic extraction
            logger.warning("Enhanced SQL extraction failed, using basic extraction")
            if "```sql" in response:
                sql = response.split("```sql")[1].split("```")[0].strip()
            elif "```" in response:
                sql = response.split("```")[1].split("```")[0].strip()
            else:
                sql = response.strip()

            # Clean up the SQL
            lines = [line.strip() for line in sql.split("\n") if line.strip()]
            sql = " ".join(lines)

            return sql

    def _learn_from_execution(
        self, query: str, query_type: str, sql: str, success: bool
    ):
        """
        Learn from SQL execution results to improve future retrievals.

        Args:
            query: Original query
            query_type: Classified query type
            sql: Generated SQL
            success: Whether execution was successful
        """
        # Feed learning back to TAG classifier
        if hasattr(self.tag_classifier, "learn_from_success"):
            self.tag_classifier.learn_from_success(query, query_type, sql, success)

        # Record in learning database if available
        if hasattr(self, 'learning_integration'):
            try:
                from query_learning_database import QueryExecution
                
                # Extract tables from SQL
                tables = self._extract_tables_from_sql(sql)
                
                # Find which pattern was used (if any)
                pattern_matched = None
                if hasattr(self, '_last_pattern_used'):
                    pattern_matched = self._last_pattern_used
                
                execution = QueryExecution(
                    query_text=query,
                    generated_sql=sql,
                    execution_time=getattr(self, '_last_execution_time', 0.0),
                    result_count=getattr(self, '_last_result_count', 0),
                    success=success,
                    retrieval_mode="contextual_enhanced",
                    tables_used=tables,
                    pattern_matched=pattern_matched
                )
                
                self.learning_integration.learning_db.record_execution(execution)
            except Exception as e:
                logger.warning(f"Failed to record learning data: {e}")

        logger.info(
            f"Learning: {query_type} query {'succeeded' if success else 'failed'}"
        )
    
    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        """Extract table names from SQL query."""
        import re
        
        tables = []
        
        # Find tables after FROM
        from_match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        if from_match:
            tables.append(from_match.group(1).upper())
        
        # Find tables after JOIN
        join_matches = re.findall(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
        tables.extend([match.upper() for match in join_matches])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tables = []
        for table in tables:
            if table not in seen:
                seen.add(table)
                unique_tables.append(table)
        
        return unique_tables
    
    def _get_or_create_faiss_store(self, query_type: str, docs: List[Document]) -> FAISS:
        """Get cached FAISS store or create new one if needed."""
        import hashlib
        
        # Create cache key based on documents content
        content_hash = hashlib.md5(
            "".join([doc.page_content for doc in docs]).encode()
        ).hexdigest()[:16]
        
        cache_dir = self._vector_cache_dir / f"faiss_{query_type}_{content_hash}"
        
        # Try to load from cache using FAISS native methods
        if cache_dir.exists():
            try:
                store = FAISS.load_local(str(cache_dir), self.embeddings, allow_dangerous_deserialization=True)
                logger.info(f"✅ CACHE HIT: Loaded cached FAISS store for {query_type} ({len(docs)} docs) - SAVED {len(docs)} API calls")
                return store
            except Exception as e:
                logger.warning(f"Failed to load cached store: {e}")
        
        # Create new store and cache it
        logger.info(f"🔨 CACHE MISS: Creating new FAISS store for {query_type} ({len(docs)} docs) - MAKING {len(docs)} API calls")
        store = FAISS.from_documents(docs, self.embeddings)
        
        # Save to cache using FAISS native method
        try:
            store.save_local(str(cache_dir))
            logger.info(f"💾 Cached FAISS store for {query_type}")
        except Exception as e:
            logger.warning(f"Failed to cache store: {e}")
        
        return store

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

        logger.info(
            "Query classified as: %s (confidence: %.2f)",
            query_context.query_type,
            query_context.confidence_score,
        )

        # Get specialized store for query type
        store = self.query_type_stores.get(query_context.query_type)

        if not store:
            logger.warning(
                "No specialized store for %s, using general_property",
                query_context.query_type,
            )
            store = self.query_type_stores.get("general_property")

        if not store:
            logger.error("No stores available for retrieval")
            return []

        # Retrieve targeted schema documents for SQL generation
        docs = store.similarity_search(query, k=k)

        retrieval_time = time.time() - start_time
        logger.info(
            "Retrieved %d schema documents in %.2fs for SQL generation",
            len(docs),
            retrieval_time,
        )

        return docs


def create_contextual_enhanced_retriever(
    documents: List[Document],
    openai_api_key: str,
    db_connection_string: str = None,
    llm: BaseLanguageModel = None,
) -> ContextualEnhancedRetriever:
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
    return ContextualEnhancedRetriever(
        documents, openai_api_key, db_connection_string, llm
    )


if __name__ == "__main__":
    # Quick test of the classifier
    classifier = QueryTypeClassifier()

    test_queries = [
        "Wer wohnt in der Marienstr. 26, 45307 Essen",
        "Liste aller Eigentümer",
        "Durchschnittliche Miete in Essen",
        "Wie viele Wohnungen gibt es insgesamt?",
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
