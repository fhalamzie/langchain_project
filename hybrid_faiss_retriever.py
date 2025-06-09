#!/usr/bin/env python3
"""
Hybrid FAISS Retriever - Solves FAISS mode's "Semantic Gap" problem

Task 1.2: FAISS → Hybrid FAISS
Problem: Semantic Gap - versteht HV-Business-Logic nicht
Solution: Semantic + Keyword + HV-Terminologie-Mapping

Key improvements:
1. HV-Business-Terminologie-Dictionary für Synonym-Expansion
2. BM25 Keyword Search + FAISS Semantic Search hybrid approach
3. Domain-Enhanced Embeddings mit HV-spezifischen Terms
4. Findet "BEWOHNER" auch bei Query "Mieter"
"""

import logging
import os
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import OpenAIEmbeddings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
class HybridSearchResult:
    """Result from hybrid search combining semantic and keyword matching."""

    document: Document
    semantic_score: float
    keyword_score: float
    combined_score: float
    matched_terms: List[str]
    expansion_terms: List[str]


@dataclass
class HybridFAISSResult:
    """Result from Hybrid FAISS Retriever with SQL execution."""

    documents: List[Document]
    hybrid_results: List[HybridSearchResult]
    sql_query: str
    execution_result: SQLExecutionResult
    retrieval_time: float
    terminology_expansions: Dict[str, List[str]]


class HVBusinessTerminologyMapper:
    """
    Hausverwaltung Business Terminology Dictionary

    Maps common business terms to technical database terms for better retrieval.
    Solves the semantic gap where users say "Mieter" but database uses "BEWOHNER".
    """

    def __init__(self):
        """Initialize with comprehensive HV terminology mappings."""

        # Dynamic business term mappings - no hardcoded table/column names
        # Tables discovered from schema, columns learned during runtime
        self.business_mappings = {
            # Business concepts to general terms (LLM will map to actual schema)
            "mieter": ["bewohner", "tenant", "resident"],
            "bewohner": ["mieter", "tenant", "resident"],
            "mieterin": ["bewohner", "mieter", "tenant"],
            "pächter": ["bewohner", "mieter"],
            "eigentümer": ["owner", "besitzer"],
            "besitzer": ["eigentuemer", "eigentümer", "owner"],
            "hauseigentümer": ["eigentuemer", "eigentümer"],
            "wohnung": ["apartment", "unit"],
            "apartment": ["wohnung", "unit"],
            "immobilie": ["property", "wohnung"],
            "objekt": ["immobilie", "wohnung", "property"],
            "gebäude": ["building", "immobilie"],
            "haus": ["building", "gebäude", "immobilie"],
            "property": ["objekte", "wohnung", "immobilie"],
            "miete": ["rent", "zahlung"],
            "rent": ["miete", "zahlung"],
            "zahlung": ["payment", "miete"],
            "konto": ["account"],
            "buchung": ["transaction"],
            "saldo": ["balance"],
            "geld": ["money", "zahlung"],
            "adresse": ["address"],
            "address": ["adresse"],
            "straße": ["street"],
            "str.": ["straße", "street"],
            "plz": ["postal", "postleitzahl"],
            "postleitzahl": ["plz", "postal"],
            "ort": ["city", "stadt"],
            "stadt": ["ort", "city"],
            "wohnt": ["lives", "resides"],
            "gehört": ["belongs", "owns"],
            "zahlt": ["pays", "payment"],
            "liste": ["list", "all", "alle"],
            "alle": ["all", "list"],
            "anzahl": ["count", "number", "viele"],
            "viele": ["many", "anzahl", "number"],
            "durchschnitt": ["average", "durchschnittlich"],
        }

        # Reverse mapping for quick lookup
        self.reverse_mapping = {}
        for term, expansions in self.business_mappings.items():
            for expansion in expansions:
                if expansion not in self.reverse_mapping:
                    self.reverse_mapping[expansion] = []
                if term not in self.reverse_mapping[expansion]:
                    self.reverse_mapping[expansion].append(term)

    def expand_query_terms(self, query: str) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Expand query with HV business terminology.

        Args:
            query: Original user query

        Returns:
            Tuple of (expanded_terms, expansion_mapping)
        """
        query_lower = query.lower()
        original_terms = query_lower.split()

        expanded_terms = set(original_terms)
        expansion_mapping = {}

        # Expand each term using business mappings
        for term in original_terms:
            if term in self.business_mappings:
                expansions = self.business_mappings[term]
                expanded_terms.update(expansions)
                expansion_mapping[term] = expansions

                logger.debug("Expanded '%s' → %s", term, expansions)

        # Also check for partial matches and common phrases
        for business_term, technical_terms in self.business_mappings.items():
            if business_term in query_lower:
                expanded_terms.update(technical_terms)
                expansion_mapping[business_term] = technical_terms

        expanded_list = list(expanded_terms)
        logger.info(
            "Query expansion: %d original terms → %d expanded terms",
            len(original_terms),
            len(expanded_list),
        )

        return expanded_list, expansion_mapping

    def get_semantic_equivalents(self, database_term: str) -> List[str]:
        """Get business terminology equivalents for a database term."""
        database_term_upper = database_term.upper()
        equivalents = self.reverse_mapping.get(database_term_upper, [])
        return equivalents


class BM25KeywordSearcher:
    """BM25-based keyword searcher for precise term matching."""

    def __init__(self, documents: List[Document]):
        """Initialize BM25 searcher with document collection."""
        self.documents = documents
        self.doc_texts = [doc.page_content.lower() for doc in documents]

        # Initialize TF-IDF vectorizer (approximates BM25)
        self.vectorizer = TfidfVectorizer(
            stop_words=None,  # Keep all words for technical domain
            ngram_range=(1, 2),  # Include bigrams for technical terms
            max_features=10000,
            lowercase=True,
        )

        # Fit vectorizer on all documents
        self.doc_vectors = self.vectorizer.fit_transform(self.doc_texts)

        logger.info("BM25 searcher initialized with %d documents", len(documents))

    def search(
        self, expanded_terms: List[str], k: int = 10
    ) -> List[Tuple[Document, float]]:
        """
        Search documents using BM25-like keyword matching.

        Args:
            expanded_terms: Query terms including expansions
            k: Number of results to return

        Returns:
            List of (document, score) tuples sorted by relevance
        """
        # Create query vector
        query_text = " ".join(expanded_terms)
        query_vector = self.vectorizer.transform([query_text])

        # Calculate cosine similarity scores
        scores = cosine_similarity(query_vector, self.doc_vectors).flatten()

        # Get top-k results
        top_indices = np.argsort(scores)[::-1][:k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include non-zero matches
                results.append((self.documents[idx], float(scores[idx])))

        logger.debug(
            "BM25 search found %d results for query: %s", len(results), query_text[:100]
        )

        return results


class DomainEnhancedEmbeddings:
    """Enhanced embeddings that understand HV domain terminology."""

    def __init__(
        self, openai_api_key: str, terminology_mapper: HVBusinessTerminologyMapper
    ):
        """Initialize domain-enhanced embeddings."""
        self.base_embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=openai_api_key,
            dimensions=1536,
        )
        self.terminology_mapper = terminology_mapper

    def embed_documents(self, documents: List[Document]) -> List[Document]:
        """Embed documents with domain-enhanced content."""
        enhanced_docs = []

        for doc in documents:
            # Enhance document content with domain terminology
            enhanced_content = self._enhance_content_with_domain_terms(doc.page_content)

            enhanced_doc = Document(
                page_content=enhanced_content, metadata=doc.metadata
            )
            enhanced_docs.append(enhanced_doc)

        return enhanced_docs

    def _enhance_content_with_domain_terms(self, content: str) -> str:
        """Enhance content by adding domain-equivalent terms."""
        enhanced_content = content

        # Add business term equivalents for technical terms found in content
        content_upper = content.upper()

        for (
            business_term,
            technical_terms,
        ) in self.terminology_mapper.business_mappings.items():
            for tech_term in technical_terms:
                if tech_term.upper() in content_upper:
                    # Add business equivalent terms to enhance semantic understanding
                    enhanced_content += f" {business_term}"

        return enhanced_content


class HybridFAISSRetriever:
    """
    Hybrid FAISS Retriever combining semantic and keyword search.

    Solves FAISS mode's semantic gap by:
    1. Expanding queries with HV business terminology
    2. Combining FAISS semantic search with BM25 keyword search
    3. Weighted scoring for optimal results
    """

    def __init__(
        self,
        documents: List[Document],
        openai_api_key: str,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4,
        db_connection_string: str = None,
        llm: BaseLanguageModel = None,
    ):
        """
        Initialize Hybrid FAISS Retriever.

        Args:
            documents: Document collection
            openai_api_key: OpenAI API key
            semantic_weight: Weight for semantic similarity (default 0.6)
            keyword_weight: Weight for keyword matching (default 0.4)
            db_connection_string: Database connection for SQL execution
            llm: Language model for SQL generation
        """
        self.documents = documents
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.db_connection_string = (
            db_connection_string
            or "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
        )
        self.llm = llm

        # Initialize components
        self.terminology_mapper = HVBusinessTerminologyMapper()
        self.keyword_searcher = BM25KeywordSearcher(documents)

        # Initialize domain-enhanced embeddings
        self.domain_embeddings = DomainEnhancedEmbeddings(
            openai_api_key, self.terminology_mapper
        )

        # Initialize vector store caching
        from pathlib import Path
        self._vector_cache_dir = Path("vector_cache")
        self._vector_cache_dir.mkdir(exist_ok=True)
        
        # Create enhanced documents and FAISS store with caching
        logger.info("Creating domain-enhanced FAISS store...")
        enhanced_docs = self.domain_embeddings.embed_documents(documents)

        self.base_embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=openai_api_key,
            dimensions=1536,
        )

        self.faiss_store = self._get_or_create_faiss_store("hybrid_enhanced", enhanced_docs)

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

        logger.info(
            "Hybrid FAISS Retriever initialized with %d documents", len(documents)
        )

    def retrieve_hybrid(self, query: str, k: int = 4) -> List[HybridSearchResult]:
        """
        Retrieve documents using hybrid semantic + keyword approach.

        Args:
            query: Natural language query
            k: Number of results to return

        Returns:
            List of HybridSearchResult with combined scoring
        """
        start_time = time.time()

        # Step 1: Expand query with HV terminology
        expanded_terms, expansion_mapping = self.terminology_mapper.expand_query_terms(
            query
        )

        logger.info("Query: '%s' expanded to %d terms", query, len(expanded_terms))

        # Step 2: Semantic search with FAISS (using original query)
        semantic_docs = self.faiss_store.similarity_search_with_score(query, k=k * 2)

        # Step 3: Keyword search with BM25 (using expanded terms)
        keyword_results = self.keyword_searcher.search(expanded_terms, k=k * 2)

        # Step 4: Combine and score results
        combined_results = self._combine_search_results(
            semantic_docs, keyword_results, expansion_mapping, expanded_terms
        )

        # Step 5: Sort by combined score and return top-k
        combined_results.sort(key=lambda x: x.combined_score, reverse=True)
        final_results = combined_results[:k]

        retrieval_time = time.time() - start_time
        logger.info(
            "Hybrid retrieval completed: %d results in %.3fs",
            len(final_results),
            retrieval_time,
        )

        return final_results

    def _combine_search_results(
        self,
        semantic_docs: List[Tuple[Document, float]],
        keyword_results: List[Tuple[Document, float]],
        expansion_mapping: Dict[str, List[str]],
        expanded_terms: List[str],
    ) -> List[HybridSearchResult]:
        """Combine semantic and keyword search results with weighted scoring."""

        # Create lookup for semantic scores
        semantic_scores = {id(doc): score for doc, score in semantic_docs}
        keyword_scores = {id(doc): score for doc, score in keyword_results}

        # Get all unique documents
        all_docs = {}
        for doc, _ in semantic_docs:
            all_docs[id(doc)] = doc
        for doc, _ in keyword_results:
            all_docs[id(doc)] = doc

        # Calculate combined scores
        combined_results = []

        for doc_id, doc in all_docs.items():
            semantic_score = semantic_scores.get(doc_id, 0.0)
            keyword_score = keyword_scores.get(doc_id, 0.0)

            # Ensure scores are floats, not numpy types
            semantic_score = float(semantic_score) if semantic_score is not None else 0.0
            keyword_score = float(keyword_score) if keyword_score is not None else 0.0

            # Normalize scores (semantic scores from FAISS are distances, need to invert)
            normalized_semantic = (
                1.0 / (1.0 + semantic_score) if semantic_score > 0 else 0.0
            )
            normalized_keyword = keyword_score  # TF-IDF scores are already normalized

            # Combined weighted score (ensure all values are Python floats)
            combined_score = (
                float(self.semantic_weight) * float(normalized_semantic)
                + float(self.keyword_weight) * float(normalized_keyword)
            )

            # Find matched terms in document
            matched_terms = self._find_matched_terms(doc.page_content, expanded_terms)
            expansion_terms_used = []

            for original_term, expansions in expansion_mapping.items():
                if any(exp.lower() in doc.page_content.lower() for exp in expansions):
                    expansion_terms_used.extend(expansions)

            result = HybridSearchResult(
                document=doc,
                semantic_score=normalized_semantic,
                keyword_score=normalized_keyword,
                combined_score=combined_score,
                matched_terms=matched_terms,
                expansion_terms=expansion_terms_used,
            )

            combined_results.append(result)

        return combined_results

    def _find_matched_terms(self, content: str, terms: List[str]) -> List[str]:
        """Find which terms matched in the document content."""
        content_lower = content.lower()
        matched = []

        for term in terms:
            if term.lower() in content_lower:
                matched.append(term)

        return matched

    def retrieve_documents(self, query: str, max_docs: int = 10) -> List[Document]:
        """
        Standard retrieve_documents interface for compatibility.

        Args:
            query: Natural language query
            max_docs: Maximum number of documents to return

        Returns:
            List of Document objects
        """
        # Use hybrid retrieval and convert to Document format
        hybrid_results = self.retrieve_hybrid(query, k=max_docs)

        # Extract documents and add hybrid metadata
        documents = []
        for result in hybrid_results:
            doc = result.document
            # Add hybrid scoring metadata
            doc.metadata.update(
                {
                    "hybrid_combined_score": result.combined_score,
                    "hybrid_semantic_score": result.semantic_score,
                    "hybrid_keyword_score": result.keyword_score,
                    "hybrid_matched_terms": result.matched_terms,
                    "hybrid_expansion_terms": result.expansion_terms,
                    "retrieval_mode": "hybrid_faiss",
                }
            )
            documents.append(doc)

        return documents

    def retrieve(self, query: str, k: int = 4) -> HybridFAISSResult:
        """
        Complete retrieval with hybrid search, SQL generation and execution.

        Args:
            query: Natural language query
            k: Number of documents to retrieve

        Returns:
            HybridFAISSResult with hybrid search results, SQL, and database results
        """
        start_time = time.time()

        try:
            # Step 1: Hybrid document retrieval for SQL generation context
            hybrid_results = self.retrieve_hybrid(query, k)
            retrieved_docs = [result.document for result in hybrid_results]

            if not retrieved_docs:
                raise Exception("No relevant documents found for query")

            # Step 2: Extract terminology expansions for context
            expanded_terms, expansion_mapping = (
                self.terminology_mapper.expand_query_terms(query)
            )

            # Step 3: Generate SQL using hybrid-retrieved schema documents and LLM
            sql_query = self._generate_sql_from_hybrid_documents(
                query, hybrid_results, expanded_terms
            )

            # Step 4: Execute SQL against real database
            execution_result = self.sql_engine.execute_query(sql_query)
            
            # Store execution metrics for learning
            self._last_execution_time = execution_result.execution_time
            self._last_result_count = execution_result.row_count

            # Step 5: Learn from execution results
            self._learn_from_execution(
                query, sql_query, execution_result.success, hybrid_results
            )

            retrieval_time = time.time() - start_time

            return HybridFAISSResult(
                documents=retrieved_docs,
                hybrid_results=hybrid_results,
                sql_query=sql_query,
                execution_result=execution_result,
                retrieval_time=retrieval_time,
                terminology_expansions=expansion_mapping,
            )

        except Exception as e:
            logger.error(f"Hybrid FAISS retrieval failed: {e}")
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

            return HybridFAISSResult(
                documents=[],
                hybrid_results=[],
                sql_query="",
                execution_result=error_result,
                retrieval_time=retrieval_time,
                terminology_expansions={},
            )

    def _generate_sql_from_hybrid_documents(
        self,
        query: str,
        hybrid_results: List[HybridSearchResult],
        expanded_terms: List[str],
    ) -> str:
        """
        Generate SQL query using pattern matching first, then hybrid-retrieved schema documents.

        Args:
            query: Original natural language query
            hybrid_results: Hybrid search results with documents and scoring
            expanded_terms: HV terminology expansions

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

        # Build enhanced context from hybrid results
        schema_context = ""
        tables = set()

        for i, result in enumerate(hybrid_results):
            schema_context += (
                f"\nRELEVANT SCHEMA {i+1} (Score: {result.combined_score:.3f}):\n"
            )
            schema_context += f"Content: {result.document.page_content}\n"
            schema_context += f"Matched Terms: {', '.join(result.matched_terms)}\n"
            schema_context += f"HV Expansions: {', '.join(result.expansion_terms)}\n"
            
            # Extract table names from document
            if hasattr(result.document, 'metadata') and 'table_name' in result.document.metadata:
                tables.add(result.document.metadata['table_name'])

        # Build terminology mapping context
        if expanded_terms:
            schema_context += f"\nHV TERMINOLOGY MAPPINGS:\n"
            schema_context += f"Expanded Query Terms: {', '.join(expanded_terms)}\n"

        # Determine query type based on hybrid results
        query_type = self._infer_query_type_from_results(query, hybrid_results)

        # Use retry engine for reliable SQL generation
        result = self.sql_retry_engine.generate_sql_with_retry(
            llm=self.llm,
            query=query,
            query_type=query_type,
            schema_context=schema_context,
            tables=list(tables) if tables else ["BEWOHNER", "EIGENTUEMER", "OBJEKTE"]
        )

        if result.success and result.final_sql:
            logger.info(
                f"Generated SQL using hybrid context after {len(result.attempts)} attempts: {result.final_sql}"
            )
            return result.final_sql
        else:
            # Log failure details
            logger.error(
                f"Failed to generate SQL after {len(result.attempts)} attempts. "
                f"Last error: {result.attempts[-1].validation_error if result.attempts else 'No attempts'}"
            )
            # Return a safe error query
            return "SELECT 'SQL generation failed' AS error FROM RDB$DATABASE;"

    def _infer_query_type_from_results(self, query: str, results: List[HybridSearchResult]) -> str:
        """
        Infer query type from hybrid search results.
        
        Args:
            query: Original query
            results: Hybrid search results
            
        Returns:
            Inferred query type
        """
        query_lower = query.lower()
        
        # Check for count queries
        if any(word in query_lower for word in ["wie viele", "anzahl", "count"]):
            return "count_queries"
        
        # Check for address lookups
        if any(word in query_lower for word in ["wohnt", "bewohner", "straße", "str."]):
            return "address_lookup"
            
        # Check for owner lookups
        if "eigentümer" in query_lower:
            return "owner_lookup"
            
        # Check for financial queries
        if any(word in query_lower for word in ["konto", "miete", "kosten"]):
            return "financial_queries"
            
        # Default to property queries
        return "property_queries"

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
        self,
        query: str,
        sql: str,
        success: bool,
        hybrid_results: List[HybridSearchResult],
    ):
        """
        Learn from SQL execution results to improve future retrievals.

        Args:
            query: Original query
            sql: Generated SQL
            success: Whether execution was successful
            hybrid_results: Hybrid search results used for SQL generation
        """
        # Classify query for learning (simple classification based on terminology)
        query_type = self._classify_query_for_learning(query, hybrid_results)
        
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
                    retrieval_mode="hybrid_faiss",
                    tables_used=tables,
                    pattern_matched=pattern_matched
                )
                
                self.learning_integration.learning_db.record_execution(execution)
            except Exception as e:
                logger.warning(f"Failed to record learning data: {e}")

        # Learn which document combinations worked well for SQL generation
        if success:
            logger.info(
                f"Learning: Hybrid search successfully generated SQL for '{query}'"
            )
            for result in hybrid_results:
                logger.debug(
                    f"Successful hybrid combination: {result.matched_terms} + {result.expansion_terms}"
                )
        else:
            logger.warning(
                f"Learning: Hybrid search failed for '{query}' - may need better terminology mapping"
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

    def _classify_query_for_learning(
        self, query: str, hybrid_results: List[HybridSearchResult]
    ) -> str:
        """
        Simple query classification based on hybrid search results for learning.

        Args:
            query: Original query
            hybrid_results: Hybrid search results

        Returns:
            Query type string
        """
        query_lower = query.lower()

        # Check expansion terms to determine query type
        expansion_terms = []
        for result in hybrid_results:
            expansion_terms.extend(result.expansion_terms)

        expansion_str = " ".join(expansion_terms).lower()

        if any(
            term in query_lower or term in expansion_str
            for term in ["bewohner", "mieter", "wohnt"]
        ):
            return "address_lookup"
        elif any(
            term in query_lower or term in expansion_str
            for term in ["eigentuemer", "eigentümer", "besitzer"]
        ):
            return "owner_lookup"
        elif any(
            term in query_lower or term in expansion_str
            for term in ["konten", "miete", "zahlung", "kosten"]
        ):
            return "financial_queries"
        elif any(
            term in query_lower or term in expansion_str
            for term in ["anzahl", "viele", "count"]
        ):
            return "count_queries"
        else:
            return "general_property"
    
    def _get_or_create_faiss_store(self, store_name: str, docs: List[Document]) -> FAISS:
        """Get cached FAISS store or create new one if needed."""
        import hashlib
        
        # Create cache key based on documents content
        content_hash = hashlib.md5(
            "".join([doc.page_content for doc in docs]).encode()
        ).hexdigest()[:16]
        
        cache_dir = self._vector_cache_dir / f"faiss_{store_name}_{content_hash}"
        
        # Try to load from cache using FAISS native methods
        if cache_dir.exists():
            try:
                store = FAISS.load_local(str(cache_dir), self.base_embeddings, allow_dangerous_deserialization=True)
                logger.info(f"✅ CACHE HIT: Loaded cached FAISS store for {store_name} ({len(docs)} docs) - SAVED {len(docs)} API calls")
                return store
            except Exception as e:
                logger.warning(f"Failed to load cached store: {e}")
        
        # Create new store and cache it
        logger.info(f"🔨 CACHE MISS: Creating new FAISS store for {store_name} ({len(docs)} docs) - MAKING {len(docs)} API calls")
        store = FAISS.from_documents(docs, self.base_embeddings)
        
        # Save to cache using FAISS native method
        try:
            store.save_local(str(cache_dir))
            logger.info(f"💾 Cached FAISS store for {store_name}")
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

    def retrieve_documents(self, query: str, max_docs: int = 10) -> List[Document]:
        """
        Standard retrieve_documents interface for compatibility.

        Args:
            query: Natural language query
            max_docs: Maximum number of documents to return

        Returns:
            List of Document objects from hybrid search (for SQL generation context)
        """
        # Use hybrid retrieval and convert to Document format
        hybrid_results = self.retrieve_hybrid(query, k=max_docs)

        # Extract documents and add hybrid metadata
        documents = []
        for result in hybrid_results:
            doc = result.document
            # Add hybrid scoring metadata
            doc.metadata.update(
                {
                    "hybrid_combined_score": result.combined_score,
                    "hybrid_semantic_score": result.semantic_score,
                    "hybrid_keyword_score": result.keyword_score,
                    "hybrid_matched_terms": result.matched_terms,
                    "hybrid_expansion_terms": result.expansion_terms,
                    "retrieval_mode": "hybrid_faiss",
                }
            )
            documents.append(doc)

        return documents

    def get_retriever_info(self) -> Dict[str, Any]:
        """Get information about this retriever."""
        return {
            "mode": "hybrid_faiss",
            "type": "Hybrid FAISS Retriever",
            "description": (
                "Combines semantic search (FAISS) with keyword search (BM25) and HV business terminology mapping"
            ),
            "documents_available": len(self.documents),
            "features": [
                "HV Business Terminology Dictionary",
                "Semantic search via FAISS",
                "Keyword search via BM25",
                "Domain-enhanced embeddings",
                "Weighted hybrid scoring",
            ],
            "weights": {
                "semantic": self.semantic_weight,
                "keyword": self.keyword_weight,
            },
            "status": "active",
        }


def create_hybrid_faiss_retriever(
    documents: List[Document],
    openai_api_key: str,
    db_connection_string: str = None,
    llm: BaseLanguageModel = None,
) -> HybridFAISSRetriever:
    """
    Factory function to create Hybrid FAISS Retriever.

    Args:
        documents: Document collection
        openai_api_key: OpenAI API key
        db_connection_string: Database connection for SQL execution
        llm: Language model for SQL generation

    Returns:
        Configured HybridFAISSRetriever instance
    """
    return HybridFAISSRetriever(
        documents, openai_api_key, db_connection_string=db_connection_string, llm=llm
    )


if __name__ == "__main__":
    # Test the HV terminology mapper
    mapper = HVBusinessTerminologyMapper()

    test_queries = [
        "Wer sind die Mieter in der Marienstraße?",
        "Liste aller Eigentümer aus Köln",
        "Durchschnittliche Miete in Essen",
        "Wie viele Wohnungen gibt es?",
    ]

    print("🔍 Testing HV Business Terminology Mapping")
    print("=" * 60)

    for query in test_queries:
        expanded_terms, mapping = mapper.expand_query_terms(query)
        print(f"\nQuery: {query}")
        print(f"Expanded Terms: {expanded_terms[:10]}...")  # Show first 10
        print(f"Key Mappings: {mapping}")
