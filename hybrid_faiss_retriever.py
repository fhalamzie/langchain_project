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

import os
import logging
import time
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

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


class HVBusinessTerminologyMapper:
    """
    Hausverwaltung Business Terminology Dictionary
    
    Maps common business terms to technical database terms for better retrieval.
    Solves the semantic gap where users say "Mieter" but database uses "BEWOHNER".
    """
    
    def __init__(self):
        """Initialize with comprehensive HV terminology mappings."""
        
        # Core HV business term mappings  
        self.business_mappings = {
            # Residents/Tenants
            "mieter": ["BEWOHNER", "bewohner", "tenant", "resident", "BEWADR"],
            "bewohner": ["BEWOHNER", "mieter", "tenant", "resident", "BEWADR"],
            "mieterin": ["BEWOHNER", "bewohner", "mieter", "tenant"],
            "pächter": ["BEWOHNER", "bewohner", "mieter"],
            "haus bewohner": ["BEWOHNER", "mieter"],
            
            # Owners
            "eigentümer": ["EIGENTUEMER", "eigentuemer", "owner", "besitzer", "EIGADR", "VEREIG"],
            "besitzer": ["EIGENTUEMER", "eigentuemer", "eigentümer", "owner", "VEREIG"], 
            "hauseigentümer": ["EIGENTUEMER", "eigentuemer", "eigentümer"],
            "immobilieneigentümer": ["EIGENTUEMER", "eigentuemer"],
            "wohnungseigentümer": ["EIGENTUEMER", "eigentuemer", "VEREIG"],
            
            # Properties
            "wohnung": ["WOHNUNG", "wohnung", "apartment", "unit", "ONR"],
            "apartment": ["WOHNUNG", "wohnung", "apartment", "unit"],
            "immobilie": ["OBJEKTE", "objekte", "wohnung", "property", "ONR"],
            "objekt": ["OBJEKTE", "objekte", "immobilie", "wohnung", "ONR"],
            "gebäude": ["OBJEKTE", "objekte", "building", "immobilie"],
            "haus": ["OBJEKTE", "objekte", "building", "gebäude", "immobilie"],
            "property": ["OBJEKTE", "objekte", "wohnung", "immobilie"],
            
            # Financial  
            "miete": ["KONTEN", "konten", "buchung", "BUCHUNG", "rent", "zahlung"],
            "rent": ["KONTEN", "konten", "miete", "BUCHUNG", "zahlung"],
            "zahlung": ["BUCHUNG", "buchung", "konten", "KONTEN", "payment"],
            "konto": ["KONTEN", "konten", "account", "buchung"],
            "buchung": ["BUCHUNG", "buchung", "konten", "KONTEN", "transaction"],
            "saldo": ["KONTEN", "konten", "balance", "BUCHUNG"],
            "geld": ["KONTEN", "konten", "BUCHUNG", "buchung", "zahlung"],
            
            # Addresses
            "adresse": ["BEWADR", "bewadr", "EIGADR", "eigadr", "address", "BSTR", "BPLZORT"],
            "address": ["BEWADR", "bewadr", "EIGADR", "eigadr", "adresse", "BSTR"],
            "straße": ["BSTR", "bstr", "street", "adresse", "address"],
            "str.": ["BSTR", "bstr", "straße", "street"],
            "plz": ["BPLZORT", "bplzort", "postal", "postleitzahl"],
            "postleitzahl": ["BPLZORT", "bplzort", "plz", "postal"],
            "ort": ["BPLZORT", "bplzort", "city", "stadt", "ORT"],
            "stadt": ["BPLZORT", "bplzort", "ort", "city"],
            
            # Common actions
            "wohnt": ["BEWOHNER", "bewohner", "BEWADR", "bewadr", "lives", "resides"],
            "gehört": ["EIGENTUEMER", "eigentuemer", "VEREIG", "vereig", "belongs", "owns"],
            "zahlt": ["BUCHUNG", "buchung", "KONTEN", "konten", "pays", "payment"],
            "liste": ["SELECT", "select", "list", "all", "alle"],
            "alle": ["SELECT", "select", "list", "alle", "*"],
            "anzahl": ["COUNT", "count", "number", "viele", "wie viele"],
            "viele": ["COUNT", "count", "anzahl", "number", "how many"],
            "durchschnitt": ["AVG", "avg", "average", "durchschnittlich"]
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
        logger.info("Query expansion: %d original terms → %d expanded terms", 
                   len(original_terms), len(expanded_list))
        
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
            lowercase=True
        )
        
        # Fit vectorizer on all documents
        self.doc_vectors = self.vectorizer.fit_transform(self.doc_texts)
        
        logger.info("BM25 searcher initialized with %d documents", len(documents))
    
    def search(self, expanded_terms: List[str], k: int = 10) -> List[Tuple[Document, float]]:
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
        
        logger.debug("BM25 search found %d results for query: %s", 
                    len(results), query_text[:100])
        
        return results


class DomainEnhancedEmbeddings:
    """Enhanced embeddings that understand HV domain terminology."""
    
    def __init__(self, openai_api_key: str, terminology_mapper: HVBusinessTerminologyMapper):
        """Initialize domain-enhanced embeddings."""
        self.base_embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=openai_api_key,
            dimensions=1536
        )
        self.terminology_mapper = terminology_mapper
    
    def embed_documents(self, documents: List[Document]) -> List[Document]:
        """Embed documents with domain-enhanced content."""
        enhanced_docs = []
        
        for doc in documents:
            # Enhance document content with domain terminology
            enhanced_content = self._enhance_content_with_domain_terms(doc.page_content)
            
            enhanced_doc = Document(
                page_content=enhanced_content,
                metadata=doc.metadata
            )
            enhanced_docs.append(enhanced_doc)
        
        return enhanced_docs
    
    def _enhance_content_with_domain_terms(self, content: str) -> str:
        """Enhance content by adding domain-equivalent terms."""
        enhanced_content = content
        
        # Add business term equivalents for technical terms found in content
        content_upper = content.upper()
        
        for business_term, technical_terms in self.terminology_mapper.business_mappings.items():
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
    
    def __init__(self, documents: List[Document], openai_api_key: str, 
                 semantic_weight: float = 0.6, keyword_weight: float = 0.4):
        """
        Initialize Hybrid FAISS Retriever.
        
        Args:
            documents: Document collection
            openai_api_key: OpenAI API key
            semantic_weight: Weight for semantic similarity (default 0.6)
            keyword_weight: Weight for keyword matching (default 0.4)
        """
        self.documents = documents
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        
        # Initialize components
        self.terminology_mapper = HVBusinessTerminologyMapper()
        self.keyword_searcher = BM25KeywordSearcher(documents)
        
        # Initialize domain-enhanced embeddings
        self.domain_embeddings = DomainEnhancedEmbeddings(
            openai_api_key, self.terminology_mapper
        )
        
        # Create enhanced documents and FAISS store
        logger.info("Creating domain-enhanced FAISS store...")
        enhanced_docs = self.domain_embeddings.embed_documents(documents)
        
        base_embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large", 
            openai_api_key=openai_api_key,
            dimensions=1536
        )
        
        self.faiss_store = FAISS.from_documents(enhanced_docs, base_embeddings)
        
        logger.info("Hybrid FAISS Retriever initialized with %d documents", 
                   len(documents))
    
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
        expanded_terms, expansion_mapping = self.terminology_mapper.expand_query_terms(query)
        
        logger.info("Query: '%s' expanded to %d terms", query, len(expanded_terms))
        
        # Step 2: Semantic search with FAISS (using original query)
        semantic_docs = self.faiss_store.similarity_search_with_score(query, k=k*2)
        
        # Step 3: Keyword search with BM25 (using expanded terms)  
        keyword_results = self.keyword_searcher.search(expanded_terms, k=k*2)
        
        # Step 4: Combine and score results
        combined_results = self._combine_search_results(
            semantic_docs, keyword_results, expansion_mapping, expanded_terms
        )
        
        # Step 5: Sort by combined score and return top-k
        combined_results.sort(key=lambda x: x.combined_score, reverse=True)
        final_results = combined_results[:k]
        
        retrieval_time = time.time() - start_time
        logger.info("Hybrid retrieval completed: %d results in %.3fs", 
                   len(final_results), retrieval_time)
        
        return final_results
    
    def _combine_search_results(self, semantic_docs: List[Tuple[Document, float]], 
                              keyword_results: List[Tuple[Document, float]],
                              expansion_mapping: Dict[str, List[str]],
                              expanded_terms: List[str]) -> List[HybridSearchResult]:
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
            
            # Normalize scores (semantic scores from FAISS are distances, need to invert)
            normalized_semantic = 1.0 / (1.0 + semantic_score) if semantic_score > 0 else 0.0
            normalized_keyword = keyword_score  # TF-IDF scores are already normalized
            
            # Combined weighted score
            combined_score = (self.semantic_weight * normalized_semantic + 
                            self.keyword_weight * normalized_keyword)
            
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
                expansion_terms=expansion_terms_used
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


def create_hybrid_faiss_retriever(documents: List[Document], 
                                 openai_api_key: str) -> HybridFAISSRetriever:
    """
    Factory function to create Hybrid FAISS Retriever.
    
    Args:
        documents: Document collection
        openai_api_key: OpenAI API key
        
    Returns:
        Configured HybridFAISSRetriever instance
    """
    return HybridFAISSRetriever(documents, openai_api_key)


if __name__ == "__main__":
    # Test the HV terminology mapper
    mapper = HVBusinessTerminologyMapper()
    
    test_queries = [
        "Wer sind die Mieter in der Marienstraße?",
        "Liste aller Eigentümer aus Köln",
        "Durchschnittliche Miete in Essen", 
        "Wie viele Wohnungen gibt es?"
    ]
    
    print("🔍 Testing HV Business Terminology Mapping")
    print("=" * 60)
    
    for query in test_queries:
        expanded_terms, mapping = mapper.expand_query_terms(query)
        print(f"\nQuery: {query}")
        print(f"Expanded Terms: {expanded_terms[:10]}...")  # Show first 10
        print(f"Key Mappings: {mapping}")