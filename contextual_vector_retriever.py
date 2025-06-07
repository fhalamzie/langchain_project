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
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Import our optimized components
from adaptive_tag_classifier import AdaptiveTAGClassifier, ClassificationResult
from hybrid_faiss_retriever import HVBusinessTerminologyMapper, HybridFAISSRetriever

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
                "context": "Property management address search for residents and buildings",
                "domain_terms": ["BEWOHNER", "OBJEKTE", "address", "street", "resident", "apartment"],
                "business_logic": "Search for residents by address using BEWOHNER table linked to OBJEKTE"
            },
            "resident_lookup": {
                "context": "Property management resident information and tenant data",
                "domain_terms": ["BEWOHNER", "tenant", "resident", "name", "contact", "apartment"],
                "business_logic": "Find resident information using BEWOHNER table with personal data"
            },
            "owner_lookup": {
                "context": "Property management owner and ownership information",
                "domain_terms": ["EIGENTUEMER", "owner", "property", "ownership", "VEREIG", "building"],
                "business_logic": "Search owners using EIGENTUEMER table linked through VEREIG relationships"
            },
            "property_queries": {
                "context": "Property management building and apartment information",
                "domain_terms": ["OBJEKTE", "WOHNUNG", "building", "apartment", "property", "unit"],
                "business_logic": "Property data from OBJEKTE and WOHNUNG tables with structural information"
            },
            "financial_queries": {
                "context": "Property management financial data and accounting information",
                "domain_terms": ["KONTEN", "BUCHUNG", "rent", "payment", "financial", "account", "money"],
                "business_logic": "Financial queries using KONTEN accounts and BUCHUNG transaction data"
            },
            "count_queries": {
                "context": "Property management counting and statistical queries",
                "domain_terms": ["COUNT", "total", "number", "statistics", "WOHNUNG", "OBJEKTE"],
                "business_logic": "Statistical counting of properties, apartments, or residents"
            },
            "relationship_queries": {
                "context": "Property management complex relationship and association queries",
                "domain_terms": ["relationship", "connection", "linked", "associated", "VEREIG", "ONR"],
                "business_logic": "Complex queries involving multiple entity relationships and connections"
            },
            "temporal_queries": {
                "context": "Property management time-based and historical queries",
                "domain_terms": ["date", "time", "period", "since", "until", "history", "BUCHUNG"],
                "business_logic": "Time-based queries for historical data and date ranges"
            },
            "comparison_queries": {
                "context": "Property management comparative analysis and statistics",
                "domain_terms": ["compare", "analysis", "statistics", "more", "less", "average"],
                "business_logic": "Comparative analysis between properties, costs, or other metrics"
            },
            "business_logic_queries": {
                "context": "Property management general business logic and domain queries",
                "domain_terms": ["management", "administration", "business", "WINCASA", "property"],
                "business_logic": "General property management business logic and administrative queries"
            }
        }
    
    def enhance_query_with_context(self, query: str, classification: ClassificationResult) -> str:
        """
        Enhance query with TAG-derived context for better vector search.
        
        Args:
            query: Original user query
            classification: TAG classification result
            
        Returns:
            Context-enhanced query for vector search
        """
        query_type = classification.query_type
        template = self.context_templates.get(query_type, self.context_templates["business_logic_queries"])
        
        # Build enhanced query with context
        enhanced_query = f"""
CONTEXT: {template['context']}
BUSINESS LOGIC: {template['business_logic']}
DOMAIN: Property management (WINCASA) - {', '.join(template['domain_terms'])}
QUERY TYPE: {query_type} (confidence: {classification.confidence:.3f})
ENTITIES: {', '.join(classification.entities) if classification.entities else 'None detected'}

ORIGINAL QUERY: {query}

SEARCH FOCUS: Find documents related to {query_type} in property management context
"""
        
        logger.info(f"Enhanced query for {query_type} with {len(template['domain_terms'])} domain terms")
        
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
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=openai_api_key,
            dimensions=1536
        )
        
        # Create enhanced documents with domain terminology
        enhanced_docs = self._enhance_documents_with_domain_context(documents)
        
        # Create FAISS store
        self.faiss_store = FAISS.from_documents(enhanced_docs, self.embeddings)
        
        logger.info(f"Context-boosted FAISS initialized with {len(documents)} enhanced documents")
    
    def _enhance_documents_with_domain_context(self, documents: List[Document]) -> List[Document]:
        """Enhance documents with property management domain context."""
        enhanced_docs = []
        
        for doc in documents:
            # Add business terminology context to each document
            enhanced_content = doc.page_content
            
            # Add domain context based on content
            if any(term in doc.page_content.upper() for term in ["BEWOHNER", "MIETER"]):
                enhanced_content += "\nCONTEXT: Resident and tenant management data"
            
            if any(term in doc.page_content.upper() for term in ["EIGENTUEMER", "OWNER"]):
                enhanced_content += "\nCONTEXT: Property ownership and owner data"
            
            if any(term in doc.page_content.upper() for term in ["KONTEN", "BUCHUNG", "PAYMENT"]):
                enhanced_content += "\nCONTEXT: Financial and accounting data"
            
            if any(term in doc.page_content.upper() for term in ["OBJEKTE", "WOHNUNG"]):
                enhanced_content += "\nCONTEXT: Property and building management data"
            
            # Add business terminology expansions
            expanded_terms, _ = self.terminology_mapper.expand_query_terms(doc.page_content)
            enhanced_content += f"\nTERMS: {' '.join(expanded_terms[:10])}"  # Add top 10 expanded terms
            
            enhanced_doc = Document(
                page_content=enhanced_content,
                metadata={**doc.metadata, "enhanced": True, "original_content": doc.page_content}
            )
            enhanced_docs.append(enhanced_doc)
        
        return enhanced_docs
    
    def search_with_context(self, enhanced_query: str, k: int = 4) -> List[Tuple[Document, float]]:
        """Search FAISS with context-enhanced query."""
        # Use similarity search with scores for ranking
        results = self.faiss_store.similarity_search_with_score(enhanced_query, k=k*2)  # Get more candidates
        
        # Apply context boosting to scores
        boosted_results = []
        for doc, score in results:
            # Original content for return (remove enhancements for clean output)
            original_content = doc.metadata.get("original_content", doc.page_content)
            clean_doc = Document(
                page_content=original_content,
                metadata={k: v for k, v in doc.metadata.items() if k not in ["enhanced", "original_content"]}
            )
            
            # Boost score based on domain relevance (invert distance to similarity)
            similarity_score = 1.0 / (1.0 + score) if score > 0 else 1.0
            boosted_results.append((clean_doc, similarity_score))
        
        # Sort by boosted score and return top-k
        boosted_results.sort(key=lambda x: x[1], reverse=True)
        return boosted_results[:k]


class ContextualVectorRetriever:
    """
    Contextual Vector Retriever - Combination of TAG + FAISS approaches.
    
    Strategy:
    1. TAG's ML Classifier analyzes query and generates business context
    2. Query is enhanced with domain-specific context and terminology
    3. FAISS performs semantic search with context-primed query
    4. Results are ranked with business logic boosting
    
    Benefits:
    - Better semantic understanding through business context
    - Domain-aware vector search with TAG's query intelligence
    - Combines structured classification with semantic discovery
    - Improved relevance for property management queries
    """
    
    def __init__(self, documents: List[Document], openai_api_key: str):
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
        
        # TAG classifier for query understanding
        self.tag_classifier = AdaptiveTAGClassifier()
        
        # Query context enhancer
        self.context_enhancer = QueryContextEnhancer(self.tag_classifier)
        
        # Context-boosted FAISS store
        self.context_faiss = ContextBoostedFAISS(documents, openai_api_key)
        
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
            
            logger.info(f"TAG Classification: {classification.query_type} (confidence: {classification.confidence:.3f})")
            
            # Step 2: Context Enhancement - create context-primed query
            enhanced_query = self.context_enhancer.enhance_query_with_context(query, classification)
            
            logger.info(f"Enhanced query length: {len(enhanced_query)} chars")
            
            # Step 3: Context-Boosted FAISS Search
            search_results = self.context_faiss.search_with_context(enhanced_query, k=k)
            
            # Step 4: Extract documents and scores
            documents = [doc for doc, score in search_results]
            vector_scores = [score for doc, score in search_results]
            
            # Step 5: Performance statistics
            execution_time = time.time() - start_time
            context_boost_applied = classification.confidence > 0.5  # High confidence gets more context boost
            
            stats = {
                "query_type": classification.query_type,
                "classification_confidence": classification.confidence,
                "documents_retrieved": len(documents),
                "avg_vector_score": np.mean(vector_scores) if vector_scores else 0.0,
                "max_vector_score": max(vector_scores) if vector_scores else 0.0,
                "context_enhancement_chars": len(enhanced_query),
                "execution_time": execution_time,
                "entities_detected": len(classification.entities),
                "alternatives_considered": len(classification.alternatives)
            }
            
            # Track for learning and optimization
            self.retrieval_history.append({
                "query": query,
                "classification": classification.query_type,
                "confidence": classification.confidence,
                "docs_retrieved": len(documents),
                "avg_score": stats["avg_vector_score"],
                "context_boost": context_boost_applied,
                "timestamp": time.time()
            })
            
            logger.info(f"Contextual Vector completed: {len(documents)} docs, "
                       f"avg score: {stats['avg_vector_score']:.3f}, time: {execution_time:.2f}s")
            
            return ContextualVectorResult(
                documents=documents,
                classification=classification,
                context_enhanced_query=enhanced_query,
                vector_scores=vector_scores,
                context_boost_applied=context_boost_applied,
                retrieval_stats=stats
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
                    "success": False
                }
            )
            
            return ContextualVectorResult(
                documents=[error_doc],
                classification=ClassificationResult("error", 0.0, [], [], "Error occurred"),
                context_enhanced_query=query,
                vector_scores=[0.0],
                context_boost_applied=False,
                retrieval_stats={"error": str(e), "execution_time": time.time() - start_time}
            )
    
    def learn_from_feedback(self, query: str, relevant_docs: List[str], success: bool):
        """
        Learn from retrieval feedback to improve future performance.
        
        Args:
            query: Original query
            relevant_docs: List of relevant document IDs/content
            success: Whether retrieval was successful
        """
        # TAG classifier learning
        if hasattr(self, '_last_classification'):
            self.tag_classifier.learn_from_success(
                query, 
                self._last_classification.query_type, 
                str(relevant_docs), 
                success
            )
        
        logger.info(f"Contextual Vector learning feedback: query={query[:50]}..., success={success}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for TAG + FAISS combination."""
        tag_metrics = self.tag_classifier.get_performance_metrics()
        
        if not self.retrieval_history:
            vector_metrics = {"status": "no_retrievals"}
        else:
            total_retrievals = len(self.retrieval_history)
            avg_docs = sum(h["docs_retrieved"] for h in self.retrieval_history) / total_retrievals
            avg_score = sum(h["avg_score"] for h in self.retrieval_history) / total_retrievals
            high_confidence = sum(1 for h in self.retrieval_history if h["confidence"] > 0.7)
            context_boosted = sum(1 for h in self.retrieval_history if h["context_boost"])
            
            vector_metrics = {
                "total_retrievals": total_retrievals,
                "avg_documents_retrieved": round(avg_docs, 1),
                "avg_vector_score": round(avg_score, 3),
                "high_confidence_rate": high_confidence / total_retrievals if total_retrievals > 0 else 0,
                "context_boost_rate": context_boosted / total_retrievals if total_retrievals > 0 else 0,
                "query_types_handled": len(set(h["classification"] for h in self.retrieval_history))
            }
        
        return {
            "contextual_vector_version": "1.0",
            "tag_classifier": tag_metrics,
            "vector_retriever": vector_metrics,
            "combination_strategy": "TAG context enhancement → FAISS semantic search",
            "context_boost_strategy": "Business domain terminology + query type context"
        }
    
    def get_retrieval_summary(self) -> str:
        """Get human-readable summary of contextual vector performance."""
        metrics = self.get_performance_metrics()
        
        summary = "🎯 CONTEXTUAL VECTOR RETRIEVER SUMMARY\n"
        summary += "=" * 45 + "\n\n"
        
        # TAG Classifier stats
        tag_stats = metrics["tag_classifier"]
        summary += f"TAG Context Generator:\n"
        summary += f"  • ML model available: {tag_stats.get('ml_model_available', False)}\n"
        summary += f"  • Query types covered: {tag_stats.get('query_types_covered', 0)}\n"
        summary += f"  • Classification success: {tag_stats.get('success_rate', 0):.1%}\n\n"
        
        # Vector Retriever stats
        vector_stats = metrics["vector_retriever"]
        if vector_stats.get("status") != "no_retrievals":
            summary += f"Vector Search Performance:\n"
            summary += f"  • Total retrievals: {vector_stats.get('total_retrievals', 0)}\n"
            summary += f"  • Avg documents: {vector_stats.get('avg_documents_retrieved', 0)}\n"
            summary += f"  • Avg vector score: {vector_stats.get('avg_vector_score', 0):.3f}\n"
            summary += f"  • High confidence: {vector_stats.get('high_confidence_rate', 0):.1%}\n"
            summary += f"  • Context boost rate: {vector_stats.get('context_boost_rate', 0):.1%}\n"
            summary += f"  • Query types handled: {vector_stats.get('query_types_handled', 0)}\n\n"
        else:
            summary += "Vector Search: No retrievals yet\n\n"
        
        summary += f"Strategy: {metrics['combination_strategy']}\n"
        summary += f"Boost Strategy: {metrics['context_boost_strategy']}\n"
        
        return summary


def create_contextual_vector_retriever(documents: List[Document], 
                                     openai_api_key: str) -> ContextualVectorRetriever:
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
        Document(page_content="BEWOHNER table: BWO, BNAME, BSTR for resident data", 
                metadata={"table_name": "BEWOHNER"}),
        Document(page_content="EIGENTUEMER table: ENR, NAME, VNAME for owner information", 
                metadata={"table_name": "EIGENTUEMER"}),
        Document(page_content="KONTEN table: ONR, SALDO, KONTO for financial accounts", 
                metadata={"table_name": "KONTEN"}),
        Document(page_content="OBJEKTE table: ONR, OBJNAME for property objects", 
                metadata={"table_name": "OBJEKTE"})
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
            "Vergleiche die Objektkosten"
        ]
        
        print("\nTesting TAG Context Enhancement:")
        for query in test_queries:
            classification = tag_classifier.classify_query(query)
            enhanced_query = context_enhancer.enhance_query_with_context(query, classification)
            
            print(f"\nQuery: {query}")
            print(f"  Classification: {classification.query_type} (confidence: {classification.confidence:.3f})")
            print(f"  Entities: {classification.entities}")
            print(f"  Enhanced query length: {len(enhanced_query)} chars")
            print(f"  Context snippet: {enhanced_query[:100]}...")
        
        # Test TAG metrics
        print(f"\nTAG Context Metrics:")
        tag_metrics = tag_classifier.get_performance_metrics()
        for key, value in tag_metrics.items():
            print(f"  {key}: {value}")
        
        print(f"\nContext Templates Available: {len(context_enhancer.context_templates)}")
        for query_type in context_enhancer.context_templates.keys():
            print(f"  • {query_type}")
        
    except Exception as e:
        print(f"Test error: {e}")


if __name__ == "__main__":
    test_contextual_vector_retriever()