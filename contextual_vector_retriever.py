#!/usr/bin/env python3
"""
Contextual Vector Retriever - Phase 2 Modi-Kombination #3
FAISS + TAG = "Contextual Vector"

Combines TAG's query understanding with FAISS's vector similarity:
- TAG's ML-based Query Classification provides query-type-specific context as "priming"
- FAISS searches with this context-enhanced query for better semantic matching
- Result: Structured knowledge + Semantic discovery

This implements Phase 2, Kombination 3: FAISS + TAG = "Contextual Vector"
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import OpenAIEmbeddings

# Import our optimized components
from adaptive_tag_classifier import AdaptiveTAGClassifier, ClassificationResult
from hybrid_faiss_retriever import HVBusinessTerminologyMapper, HybridFAISSRetriever

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
class ContextualVectorResult:
    """Result from Contextual Vector search combining TAG + FAISS."""

    documents: List[Document]
    classification: ClassificationResult
    context_enhanced_query: str
    vector_scores: List[float]
    context_boost_applied: bool
    retrieval_stats: Dict[str, Any]
    sql_query: str = ""
    execution_result: Optional[SQLExecutionResult] = None


class QueryContextEnhancer:
    """
    Enhances queries with TAG-derived context for better vector search.

    Uses TAG's classification to add relevant business context and domain knowledge
    to the original query, improving FAISS's semantic understanding.
    """

    def __init__(self, tag_classifier: AdaptiveTAGClassifier):
        """Initialize with TAG classifier for context generation."""
        self.tag_classifier = tag_classifier

        # Context templates for each query type
        self.context_templates = {
            "address_lookup": {
                "context": (
                    "Property management address search for residents and buildings"
                ),
                "domain_terms": [
                    "BEWOHNER",
                    "OBJEKTE",
                    "address",
                    "street",
                    "resident",
                    "apartment",
                ],
                "business_logic": (
                    "Search for residents by address using BEWOHNER table linked to OBJEKTE"
                ),
            },
            "resident_lookup": {
                "context": "Property management resident information and tenant data",
                "domain_terms": [
                    "BEWOHNER",
                    "tenant",
                    "resident",
                    "name",
                    "contact",
                    "apartment",
                ],
                "business_logic": (
                    "Find resident information using BEWOHNER table with personal data"
                ),
            },
            "owner_lookup": {
                "context": "Property management owner and ownership information",
                "domain_terms": [
                    "EIGENTUEMER",
                    "owner",
                    "property",
                    "ownership",
                    "VEREIG",
                    "building",
                ],
                "business_logic": (
                    "Search owners using EIGENTUEMER table linked through VEREIG relationships"
                ),
            },
            "property_queries": {
                "context": "Property management building and apartment information",
                "domain_terms": [
                    "OBJEKTE",
                    "WOHNUNG",
                    "building",
                    "apartment",
                    "property",
                    "unit",
                ],
                "business_logic": (
                    "Property data from OBJEKTE and WOHNUNG tables with structural information"
                ),
            },
            "financial_queries": {
                "context": (
                    "Property management financial data and accounting information"
                ),
                "domain_terms": [
                    "KONTEN",
                    "BUCHUNG",
                    "rent",
                    "payment",
                    "financial",
                    "account",
                    "money",
                ],
                "business_logic": (
                    "Financial queries using KONTEN accounts and BUCHUNG transaction data"
                ),
            },
            "count_queries": {
                "context": "Property management counting and statistical queries",
                "domain_terms": [
                    "COUNT",
                    "total",
                    "number",
                    "statistics",
                    "WOHNUNG",
                    "OBJEKTE",
                ],
                "business_logic": (
                    "Statistical counting of properties, apartments, or residents"
                ),
            },
            "relationship_queries": {
                "context": (
                    "Property management complex relationship and association queries"
                ),
                "domain_terms": [
                    "relationship",
                    "connection",
                    "linked",
                    "associated",
                    "VEREIG",
                    "ONR",
                ],
                "business_logic": (
                    "Complex queries involving multiple entity relationships and connections"
                ),
            },
            "temporal_queries": {
                "context": "Property management time-based and historical queries",
                "domain_terms": [
                    "date",
                    "time",
                    "period",
                    "since",
                    "until",
                    "history",
                    "BUCHUNG",
                ],
                "business_logic": (
                    "Time-based queries for historical data and date ranges"
                ),
            },
            "comparison_queries": {
                "context": "Property management comparative analysis and statistics",
                "domain_terms": [
                    "compare",
                    "analysis",
                    "statistics",
                    "more",
                    "less",
                    "average",
                ],
                "business_logic": (
                    "Comparative analysis between properties, costs, or other metrics"
                ),
            },
            "business_logic_queries": {
                "context": (
                    "Property management general business logic and domain queries"
                ),
                "domain_terms": [
                    "management",
                    "administration",
                    "business",
                    "WINCASA",
                    "property",
                ],
                "business_logic": (
                    "General property management business logic and administrative queries"
                ),
            },
        }

    def enhance_query_with_context(
        self, query: str, classification: ClassificationResult
    ) -> str:
        """
        Enhance query with TAG-derived context for better vector search.

        Args:
            query: Original user query
            classification: TAG classification result

        Returns:
            Context-enhanced query for vector search
        """
        query_type = classification.query_type
        template = self.context_templates.get(
            query_type, self.context_templates["business_logic_queries"]
        )

        # Build enhanced query with context
        enhanced_query = f"""
CONTEXT: {template['context']}
BUSINESS LOGIC: {template['business_logic']}
DOMAIN: Property management (WINCASA) - {', '.join(template['domain_terms'])}
QUERY TYPE: {query_type} (confidence: {classification.confidence:.3f})
ENTITIES: {', '.join(classification.entities)
                     if classification.entities else 'None detected'}

ORIGINAL QUERY: {query}

SEARCH FOCUS: Find documents related to {query_type} in property management context
"""

        logger.info(
            f"Enhanced query for {query_type} with {len(template['domain_terms'])} domain terms"
        )

        return enhanced_query.strip()


class ContextBoostedFAISS:
    """
    FAISS vector store with context-boosted search capabilities.

    Uses TAG-enhanced queries and applies business logic boosting to improve
    semantic search accuracy for property management domain.
    """

    def __init__(self, documents: List[Document], openai_api_key: str):
        """Initialize context-boosted FAISS store."""
        self.documents = documents
        self.terminology_mapper = HVBusinessTerminologyMapper()

        # Initialize vector store caching
        from pathlib import Path
        self._vector_cache_dir = Path("vector_cache")
        self._vector_cache_dir.mkdir(exist_ok=True)

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=openai_api_key,
            dimensions=1536,
        )

        # Create enhanced documents with domain terminology
        enhanced_docs = self._enhance_documents_with_domain_context(documents)

        # Create FAISS store with caching
        self.faiss_store = self._get_or_create_faiss_store("contextual_vector", enhanced_docs)

        logger.info(
            f"Context-boosted FAISS initialized with {len(documents)} enhanced documents"
        )

    def _enhance_documents_with_domain_context(
        self, documents: List[Document]
    ) -> List[Document]:
        """Enhance documents with property management domain context."""
        enhanced_docs = []

        for doc in documents:
            # Add business terminology context to each document
            enhanced_content = doc.page_content

            # Add domain context based on content
            if any(term in doc.page_content.upper() for term in ["BEWOHNER", "MIETER"]):
                enhanced_content += "\nCONTEXT: Resident and tenant management data"

            if any(
                term in doc.page_content.upper() for term in ["EIGENTUEMER", "OWNER"]
            ):
                enhanced_content += "\nCONTEXT: Property ownership and owner data"

            if any(
                term in doc.page_content.upper()
                for term in ["KONTEN", "BUCHUNG", "PAYMENT"]
            ):
                enhanced_content += "\nCONTEXT: Financial and accounting data"

            if any(term in doc.page_content.upper() for term in ["OBJEKTE", "WOHNUNG"]):
                enhanced_content += "\nCONTEXT: Property and building management data"

            # Add business terminology expansions
            expanded_terms, _ = self.terminology_mapper.expand_query_terms(
                doc.page_content
            )
            # Add top 10 expanded terms
            enhanced_content += f"\nTERMS: {' '.join(expanded_terms[:10])}"

            enhanced_doc = Document(
                page_content=enhanced_content,
                metadata={
                    **doc.metadata,
                    "enhanced": True,
                    "original_content": doc.page_content,
                },
            )
            enhanced_docs.append(enhanced_doc)

        return enhanced_docs

    def search_with_context(
        self, enhanced_query: str, k: int = 4
    ) -> List[Tuple[Document, float]]:
        """Search FAISS with context-enhanced query."""
        # Use similarity search with scores for ranking
        results = self.faiss_store.similarity_search_with_score(
            enhanced_query, k=k * 2
        )  # Get more candidates

        # Apply context boosting to scores
        boosted_results = []
        for doc, score in results:
            # Original content for return (remove enhancements for clean
            # output)
            original_content = doc.metadata.get("original_content", doc.page_content)
            clean_doc = Document(
                page_content=original_content,
                metadata={
                    k: v
                    for k, v in doc.metadata.items()
                    if k not in ["enhanced", "original_content"]
                },
            )

            # Boost score based on domain relevance (invert distance to
            # similarity)
            similarity_score = 1.0 / (1.0 + score) if score > 0 else 1.0
            boosted_results.append((clean_doc, similarity_score))

        # Sort by boosted score and return top-k
        boosted_results.sort(key=lambda x: x[1], reverse=True)
        return boosted_results[:k]
    
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
                store = FAISS.load_local(str(cache_dir), self.embeddings, allow_dangerous_deserialization=True)
                logger.info(f"✅ CACHE HIT: Loaded cached FAISS store for {store_name} ({len(docs)} docs) - SAVED {len(docs)} API calls")
                return store
            except Exception as e:
                logger.warning(f"Failed to load cached store: {e}")
        
        # Create new store and cache it
        logger.info(f"🔨 CACHE MISS: Creating new FAISS store for {store_name} ({len(docs)} docs) - MAKING {len(docs)} API calls")
        store = FAISS.from_documents(docs, self.embeddings)
        
        # Save to cache using FAISS native method
        try:
            store.save_local(str(cache_dir))
            logger.info(f"💾 Cached FAISS store for {store_name}")
        except Exception as e:
            logger.warning(f"Failed to cache store: {e}")
        
        return store


class ContextualVectorRetriever:
    """
    Contextual Vector Retriever - Combination of TAG + FAISS approaches.

    Strategy:
    1. TAG's ML Classifier analyzes query and generates business context
    2. Query is enhanced with domain-specific context and terminology
    3. FAISS performs semantic search with context-primed query
    4. LLM generates SQL using contextual documents
    5. SQL is executed against real database
    6. Results are ranked with business logic boosting

    Benefits:
    - Better semantic understanding through business context
    - Domain-aware vector search with TAG's query intelligence
    - Combines structured classification with semantic discovery
    - Real database execution with contextual SQL generation
    - Improved relevance for property management queries
    """

    def __init__(
        self,
        documents: List[Document],
        openai_api_key: str,
        db_connection_string: str = None,
        llm: BaseLanguageModel = None,
    ):
        """
        Initialize Contextual Vector Retriever.

        Args:
            documents: Document collection
            openai_api_key: OpenAI API key for embeddings
        """
        logger.info("Initializing Contextual Vector Retriever (TAG + FAISS)")

        # Core components
        self.documents = documents
        self.openai_api_key = openai_api_key
        self.db_connection_string = (
            db_connection_string
            or "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB"
        )
        self.llm = llm

        # TAG classifier for query understanding
        self.tag_classifier = AdaptiveTAGClassifier()

        # Query context enhancer
        self.context_enhancer = QueryContextEnhancer(self.tag_classifier)

        # Context-boosted FAISS store
        self.context_faiss = ContextBoostedFAISS(documents, openai_api_key)

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

        # Performance tracking
        self.retrieval_history: List[Dict[str, Any]] = []

        logger.info("Contextual Vector Retriever initialized successfully")

    def retrieve(self, query: str, k: int = 4) -> ContextualVectorResult:
        """
        Contextual Vector retrieval combining TAG context + FAISS similarity.

        Args:
            query: Natural language query
            k: Number of documents to retrieve

        Returns:
            ContextualVectorResult with context-enhanced results
        """
        start_time = time.time()

        logger.info(f"Contextual Vector retrieval for: {query}")

        try:
            # Step 1: TAG Classification - understand query intent and context
            classification = self.tag_classifier.classify_query(query)

            logger.info(
                f"TAG Classification: {classification.query_type} (confidence: {classification.confidence:.3f})"
            )

            # Step 2: Context Enhancement - create context-primed query
            enhanced_query = self.context_enhancer.enhance_query_with_context(
                query, classification
            )

            logger.info(f"Enhanced query length: {len(enhanced_query)} chars")

            # Step 3: Context-Boosted FAISS Search
            search_results = self.context_faiss.search_with_context(enhanced_query, k=k)

            # Step 4: Extract documents and scores
            documents = [doc for doc, score in search_results]
            vector_scores = [score for doc, score in search_results]

            # Step 5: Generate SQL using contextual documents and LLM
            sql_query = ""
            execution_result = None
            
            if self.llm and documents:
                try:
                    sql_query = self._generate_sql_from_contextual_documents(
                        query, documents, classification, enhanced_query
                    )
                    
                    # Step 6: Execute SQL against real database
                    execution_result = self.sql_engine.execute_query(sql_query)
                    
                    # Store execution metrics for learning
                    self._last_execution_time = execution_result.execution_time
                    self._last_result_count = execution_result.row_count
                    
                    # Step 7: Learn from execution results
                    self._learn_from_execution(
                        query, classification.query_type, sql_query, execution_result.success
                    )
                    
                except Exception as e:
                    logger.error(f"SQL generation/execution failed: {e}")
                    execution_result = SQLExecutionResult(
                        success=False,
                        query="",
                        data=[],
                        columns=[],
                        row_count=0,
                        execution_time=0.0,
                        formatted_answer=f"Error: {str(e)}",
                        error=str(e),
                    )

            # Step 8: Performance statistics
            execution_time = time.time() - start_time
            # High confidence gets more context boost
            context_boost_applied = classification.confidence > 0.5

            stats = {
                "query_type": classification.query_type,
                "classification_confidence": classification.confidence,
                "documents_retrieved": len(documents),
                "avg_vector_score": np.mean(vector_scores) if vector_scores else 0.0,
                "max_vector_score": max(vector_scores) if vector_scores else 0.0,
                "context_enhancement_chars": len(enhanced_query),
                "execution_time": execution_time,
                "entities_detected": len(classification.entities),
                "alternatives_considered": len(classification.alternatives),
            }

            # Track for learning and optimization
            self.retrieval_history.append(
                {
                    "query": query,
                    "classification": classification.query_type,
                    "confidence": classification.confidence,
                    "docs_retrieved": len(documents),
                    "avg_score": stats["avg_vector_score"],
                    "context_boost": context_boost_applied,
                    "timestamp": time.time(),
                }
            )

            logger.info(
                f"Contextual Vector completed: {len(documents)} docs, "
                f"avg score: {stats['avg_vector_score']:.3f}, time: {execution_time:.2f}s"
            )

            return ContextualVectorResult(
                documents=documents,
                classification=classification,
                context_enhanced_query=enhanced_query,
                vector_scores=vector_scores,
                context_boost_applied=context_boost_applied,
                retrieval_stats=stats,
                sql_query=sql_query,
                execution_result=execution_result,
            )

        except Exception as e:
            logger.error(f"Contextual Vector error: {e}")

            # Create error result
            error_doc = Document(
                page_content=f"Query: {query}\n\nError: {str(e)}\n\nThe Contextual Vector Retriever encountered an error.",
                metadata={
                    "source": "contextual_vector_error",
                    "query": query,
                    "error": str(e),
                    "success": False,
                },
            )

            return ContextualVectorResult(
                documents=[error_doc],
                classification=ClassificationResult(
                    "error", 0.0, [], [], "Error occurred"
                ),
                context_enhanced_query=query,
                vector_scores=[0.0],
                context_boost_applied=False,
                retrieval_stats={
                    "error": str(e),
                    "execution_time": time.time() - start_time,
                },
                sql_query="",
                execution_result=SQLExecutionResult(
                    success=False,
                    query="",
                    data=[],
                    columns=[],
                    row_count=0,
                    execution_time=0.0,
                    formatted_answer=f"Error: {str(e)}",
                    error=str(e),
                ),
            )

    def _generate_sql_from_contextual_documents(
        self,
        query: str,
        documents: List[Document],
        classification: ClassificationResult,
        enhanced_query: str,
    ) -> str:
        """
        Generate SQL query using pattern matching first, then contextual documents and TAG classification.

        Args:
            query: Original natural language query
            documents: Contextual documents from FAISS search
            classification: TAG classification result
            enhanced_query: Context-enhanced query used for search

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

        # Build contextual context from retrieved documents
        contextual_context = ""
        tables = set()
        
        for i, doc in enumerate(documents):
            contextual_context += f"\nCONTEXTUAL SCHEMA {i+1}:\n"
            contextual_context += f"Content: {doc.page_content}\n"
            if doc.metadata:
                contextual_context += f"Metadata: {doc.metadata}\n"
                # Extract table names from metadata
                if 'table_name' in doc.metadata:
                    tables.add(doc.metadata['table_name'])

        # Create enhanced prompt for SQL generation
        sql_generation_prompt = f"""
You are a SQL expert for WINCASA Hausverwaltung database queries. Generate accurate Firebird SQL.

CONTEXTUAL VECTOR ANALYSIS:
- Original Query: {query}
- Enhanced Query: {enhanced_query}
- TAG Classification: {classification.query_type} (confidence: {classification.confidence:.3f})
- Entities Detected: {', '.join(classification.entities)}
- Classification Reasoning: {classification.reasoning}

CONTEXTUAL SCHEMA INFORMATION:
{contextual_context}

HV BUSINESS LOGIC:
- \"Mieter\" maps to BEWOHNER table (residents)
- \"Eigentümer\" maps to EIGENTUEMER table (owners)
- \"Wohnung\" maps to WOHNUNG table (apartments)
- Address searches use street and postal/city columns (discovered dynamically)
- Use LIKE '%pattern%' for flexible text matching

FIREBIRD SQL RULES:
- Use SELECT for all queries
- Use LIKE '%pattern%' for text searches
- Table/column names are case-sensitive
- Use proper JOINs for relationships
- Use FIRST n instead of LIMIT n
- For address searches: use street columns for 'street number', postal columns for 'postal city'

GENERATE SQL FOR: {query}

Return only the SQL query, no explanations:"""

        # Generate SQL using LLM
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a SQL expert. Generate only valid Firebird SQL queries."
                ),
            },
            {"role": "user", "content": sql_generation_prompt},
        ]

        # Add TAG classification context
        contextual_context += f"\nTAG CLASSIFICATION:\n"
        contextual_context += f"- Query Type: {classification.query_type}\n"
        contextual_context += f"- Confidence: {classification.confidence:.3f}\n"
        contextual_context += f"- Entities: {', '.join(classification.entities)}\n"
        contextual_context += f"- Reasoning: {classification.reasoning}\n"

        # Determine tables from classification if not found in documents
        if not tables:
            tables = self._get_tables_for_query_type(classification.query_type)

        # Use retry engine for reliable SQL generation
        result = self.sql_retry_engine.generate_sql_with_retry(
            llm=self.llm,
            query=query,
            query_type=classification.query_type,
            schema_context=contextual_context,
            tables=list(tables)
        )

        if result.success and result.final_sql:
            logger.info(
                f"Generated SQL with contextual vectors after {len(result.attempts)} attempts: {result.final_sql}"
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
    
    def _get_tables_for_query_type(self, query_type: str) -> List[str]:
        """
        Get relevant tables for a query type.
        
        Args:
            query_type: TAG classification query type
            
        Returns:
            List of table names
        """
        table_mapping = {
            "address_lookup": ["BEWOHNER", "BEWADR"],
            "resident_lookup": ["BEWOHNER", "BEWADR"], 
            "owner_lookup": ["EIGENTUEMER", "EIGADR", "VEREIG"],
            "property_queries": ["OBJEKTE", "WOHNUNG"],
            "financial_queries": ["KONTEN", "BUCHUNG"],
            "count_queries": ["WOHNUNG", "BEWOHNER", "EIGENTUEMER", "OBJEKTE"],
            "relationship_queries": ["BEWOHNER", "EIGENTUEMER", "OBJEKTE", "VEREIG"],
            "temporal_queries": ["BEWOHNER", "BUCHUNG"],
            "comparison_queries": ["OBJEKTE", "WOHNUNG", "KONTEN"],
            "business_logic_queries": ["BEWOHNER", "EIGENTUEMER", "OBJEKTE", "WOHNUNG"],
        }
        
        return table_mapping.get(query_type, ["BEWOHNER", "EIGENTUEMER", "OBJEKTE"])

    def _learn_from_execution(
        self, query: str, query_type: str, sql: str, success: bool
    ):
        """
        Learn from SQL execution results to improve future retrievals.

        Args:
            query: Original query
            query_type: TAG classified query type
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
                    retrieval_mode="contextual_vector",
                    tables_used=tables,
                    pattern_matched=pattern_matched
                )
                
                self.learning_integration.learning_db.record_execution(execution)
            except Exception as e:
                logger.warning(f"Failed to record learning data: {e}")

        logger.info(
            f"Learning: Contextual Vector {query_type} query {'succeeded' if success else 'failed'}"
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

    def get_response(self, query: str) -> str:
        """
        Get formatted response for compatibility with benchmark framework.

        Args:
            query: Natural language query

        Returns:
            Formatted response string
        """
        result = self.retrieve(query)
        if result.execution_result:
            return result.execution_result.formatted_answer
        else:
            return "Error: No execution result available"

    def learn_from_feedback(self, query: str, relevant_docs: List[str], success: bool):
        """
        Learn from retrieval feedback to improve future performance.

        Args:
            query: Original query
            relevant_docs: List of relevant document IDs / content
            success: Whether retrieval was successful
        """
        # TAG classifier learning
        if hasattr(self, "_last_classification"):
            self.tag_classifier.learn_from_success(
                query, self._last_classification.query_type, str(relevant_docs), success
            )

        logger.info(
            f"Contextual Vector learning feedback: query={query[:50]}..., success={success}"
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for TAG + FAISS combination."""
        tag_metrics = self.tag_classifier.get_performance_metrics()

        if not self.retrieval_history:
            vector_metrics = {"status": "no_retrievals"}
        else:
            total_retrievals = len(self.retrieval_history)
            avg_docs = (
                sum(h["docs_retrieved"] for h in self.retrieval_history)
                / total_retrievals
            )
            avg_score = (
                sum(h["avg_score"] for h in self.retrieval_history) / total_retrievals
            )
            high_confidence = sum(
                1 for h in self.retrieval_history if h["confidence"] > 0.7
            )
            context_boosted = sum(
                1 for h in self.retrieval_history if h["context_boost"]
            )

            vector_metrics = {
                "total_retrievals": total_retrievals,
                "avg_documents_retrieved": round(avg_docs, 1),
                "avg_vector_score": round(avg_score, 3),
                "high_confidence_rate": (
                    high_confidence / total_retrievals if total_retrievals > 0 else 0
                ),
                "context_boost_rate": (
                    context_boosted / total_retrievals if total_retrievals > 0 else 0
                ),
                "query_types_handled": len(
                    set(h["classification"] for h in self.retrieval_history)
                ),
            }

        return {
            "contextual_vector_version": "1.0",
            "tag_classifier": tag_metrics,
            "vector_retriever": vector_metrics,
            "combination_strategy": "TAG context enhancement → FAISS semantic search",
            "context_boost_strategy": (
                "Business domain terminology + query type context"
            ),
        }

    def get_retrieval_summary(self) -> str:
        """Get human - readable summary of contextual vector performance."""
        metrics = self.get_performance_metrics()

        summary = "🎯 CONTEXTUAL VECTOR RETRIEVER SUMMARY\n"
        summary += "=" * 45 + "\n\n"

        # TAG Classifier stats
        tag_stats = metrics["tag_classifier"]
        summary += f"TAG Context Generator:\n"
        summary += (
            f"  • ML model available: {tag_stats.get('ml_model_available', False)}\n"
        )
        summary += (
            f"  • Query types covered: {tag_stats.get('query_types_covered', 0)}\n"
        )
        summary += (
            f"  • Classification success: {tag_stats.get('success_rate', 0):.1%}\n\n"
        )

        # Vector Retriever stats
        vector_stats = metrics["vector_retriever"]
        if vector_stats.get("status") != "no_retrievals":
            summary += f"Vector Search Performance:\n"
            summary += (
                f"  • Total retrievals: {vector_stats.get('total_retrievals', 0)}\n"
            )
            summary += (
                f"  • Avg documents: {vector_stats.get('avg_documents_retrieved', 0)}\n"
            )
            summary += (
                f"  • Avg vector score: {vector_stats.get('avg_vector_score', 0):.3f}\n"
            )
            summary += f"  • High confidence: {vector_stats.get('high_confidence_rate', 0):.1%}\n"
            summary += f"  • Context boost rate: {vector_stats.get('context_boost_rate', 0):.1%}\n"
            summary += f"  • Query types handled: {vector_stats.get('query_types_handled', 0)}\n\n"
        else:
            summary += "Vector Search: No retrievals yet\n\n"

        summary += f"Strategy: {metrics['combination_strategy']}\n"
        summary += f"Boost Strategy: {metrics['context_boost_strategy']}\n"

        return summary


def create_contextual_vector_retriever(
    documents: List[Document], openai_api_key: str
) -> ContextualVectorRetriever:
    """
    Factory function to create Contextual Vector Retriever.

    Args:
        documents: Document collection
        openai_api_key: OpenAI API key

    Returns:
        Configured ContextualVectorRetriever instance
    """
    return ContextualVectorRetriever(documents, openai_api_key)


def test_contextual_vector_retriever():
    """Test Contextual Vector Retriever with sample queries."""
    print("🧪 Testing Contextual Vector Retriever (TAG + FAISS)")
    print("=" * 60)

    # Mock documents for testing
    test_docs = [
        Document(
            page_content="BEWOHNER table: resident data with name and address columns",
            metadata={"table_name": "BEWOHNER"},
        ),
        Document(
            page_content="EIGENTUEMER table: ENR, NAME, VNAME for owner information",
            metadata={"table_name": "EIGENTUEMER"},
        ),
        Document(
            page_content="KONTEN table: ONR, SALDO, KONTO for financial accounts",
            metadata={"table_name": "KONTEN"},
        ),
        Document(
            page_content="OBJEKTE table: ONR, OBJNAME for property objects",
            metadata={"table_name": "OBJEKTE"},
        ),
    ]

    try:
        # Test just the TAG context enhancement
        from adaptive_tag_classifier import AdaptiveTAGClassifier

        tag_classifier = AdaptiveTAGClassifier()
        context_enhancer = QueryContextEnhancer(tag_classifier)

        test_queries = [
            "Wer wohnt in der Marienstraße 26?",
            "Alle Eigentümer aus Köln",
            "Durchschnittliche Miete in Essen",
            "Wie viele Wohnungen gibt es?",
            "Zeige mir alle Finanzdaten",
            "Vergleiche die Objektkosten",
        ]

        print("\nTesting TAG Context Enhancement:")
        for query in test_queries:
            classification = tag_classifier.classify_query(query)
            enhanced_query = context_enhancer.enhance_query_with_context(
                query, classification
            )

            print(f"\nQuery: {query}")
            print(
                f"  Classification: {classification.query_type} (confidence: {classification.confidence:.3f})"
            )
            print(f"  Entities: {classification.entities}")
            print(f"  Enhanced query length: {len(enhanced_query)} chars")
            print(f"  Context snippet: {enhanced_query[:100]}...")

        # Test TAG metrics
        print(f"\nTAG Context Metrics:")
        tag_metrics = tag_classifier.get_performance_metrics()
        for key, value in tag_metrics.items():
            print(f"  {key}: {value}")

        print(
            f"\nContext Templates Available: {len(context_enhancer.context_templates)}"
        )
        for query_type in context_enhancer.context_templates.keys():
            print(f"  • {query_type}")

    except Exception as e:
        print(f"Test error: {e}")


if __name__ == "__main__":
    test_contextual_vector_retriever()
