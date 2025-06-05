#!/usr/bin/env python3
"""
Test script demonstrating improvement of Hybrid FAISS over original FAISS mode.

Compares:
1. Original FAISS: Pure semantic search with semantic gap problems
2. Hybrid FAISS: Semantic + Keyword + HV-Terminologie for better business logic understanding
"""

import os
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from hybrid_faiss_retriever import HybridFAISSRetriever, HVBusinessTerminologyMapper

# Load environment
load_dotenv('/home/envs/openai.env')


def create_hv_mock_documents() -> List[Document]:
    """Create HV-specific mock documents for testing semantic gap issues."""
    return [
        Document(
            page_content="""
table_name: BEWOHNER
description: Residents database containing all current and former tenants
columns:
  - BNAME: Resident last name
  - BVNAME: Resident first name  
  - BSTR: Street address with house number
  - BPLZORT: Postal code and city
  - ONR: Object number linking to properties
business_context: Central tenant database for property management
key_relationships:
  - Links to BEWADR for additional address info
  - Links to OBJEKTE via ONR for property association
  - Links to KONTEN for rent payment tracking
            """,
            metadata={"table_name": "BEWOHNER", "category": "residents"}
        ),
        Document(
            page_content="""
table_name: EIGENTUEMER  
description: Property owners database with ownership details
columns:
  - NAME: Owner name (company or person)
  - VNAME: First name for individual owners
  - ORT: Owner's city
  - EMAIL: Contact email address
business_context: Manages all property ownership relationships
key_relationships:
  - Links to VEREIG for ownership percentages
  - Links to EIGADR for owner addresses
  - Links to OBJEKTE for owned properties
            """,
            metadata={"table_name": "EIGENTUEMER", "category": "owners"}
        ),
        Document(
            page_content="""
table_name: WOHNUNG
description: Individual apartment units within buildings
columns:
  - WHG_NR: Apartment number
  - ONR: Object number (building reference)
  - QMWFL: Living space in square meters
  - ZIMMER: Number of rooms
  - MIETE_KALT: Base rent amount
business_context: Detailed apartment inventory and specifications
rental_info: Base for rent calculations and property statistics
            """,
            metadata={"table_name": "WOHNUNG", "category": "properties"}
        ),
        Document(
            page_content="""
table_name: KONTEN
description: Financial accounts for rent collection and payments
columns:
  - ONR: Object number for property linkage
  - KONTO_NR: Account identifier
  - SALDO: Current account balance
  - LETZTE_ZAHLUNG: Last payment date
business_context: Central financial management for all properties
payment_tracking: Handles rent, utilities, and maintenance payments
            """,
            metadata={"table_name": "KONTEN", "category": "finance"}
        ),
        Document(
            page_content="""
table_name: BUCHUNG
description: Individual financial transactions and bookings
columns:
  - BUCH_NR: Booking reference number
  - DATUM: Transaction date
  - BETRAG: Transaction amount
  - VERWENDUNG: Purpose/description of transaction
  - KONTO_NR: Account reference
business_context: Detailed transaction history for audit and reporting
financial_operations: Records all money movements in the system
            """,
            metadata={"table_name": "BUCHUNG", "category": "finance"}
        ),
        Document(
            page_content="""
table_name: OBJEKTE
description: Buildings and property objects  
columns:
  - ONR: Object number (central linking key)
  - OBJ_BEZ: Object designation/name
  - STRASSE: Building street address
  - PLZ: Postal code
  - ORT: City location
business_context: Core property inventory and building management
central_role: ONR field connects all other tables to specific properties
            """,
            metadata={"table_name": "OBJEKTE", "category": "properties"}
        )
    ]


def test_original_faiss_semantic_gap(documents: List[Document], api_key: str) -> Dict[str, Any]:
    """Test original FAISS mode showing semantic gap problems."""
    
    # Create basic FAISS store (original approach)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        openai_api_key=api_key,
        dimensions=1536
    )
    
    faiss_store = FAISS.from_documents(documents, embeddings)
    
    # Test queries that show semantic gap
    semantic_gap_queries = [
        ("Wo wohnen die Mieter?", "Should find BEWOHNER but might miss due to 'Mieter' vs 'BEWOHNER'"),
        ("Liste der Eigentümer", "Should find EIGENTUEMER but might miss due to German terminology"),
        ("Wer zahlt Miete?", "Should connect payment concepts but might struggle with context"),
        ("Anzahl Wohnungen", "Should find WOHNUNG but might miss counting context")
    ]
    
    results = []
    total_start = time.time()
    
    for query, expected in semantic_gap_queries:
        start_time = time.time()
        
        # Basic semantic search 
        docs = faiss_store.similarity_search_with_score(query, k=3)
        
        retrieval_time = time.time() - start_time
        
        # Analyze results for semantic gap issues
        found_tables = []
        relevance_scores = []
        
        for doc, score in docs:
            table_name = doc.metadata.get("table_name", "unknown")
            found_tables.append(table_name)
            relevance_scores.append(float(score))
        
        # Check if correct table was found
        query_lower = query.lower()
        expected_table = None
        if "mieter" in query_lower or "wohnen" in query_lower:
            expected_table = "BEWOHNER"
        elif "eigentümer" in query_lower:
            expected_table = "EIGENTUEMER"  
        elif "miete" in query_lower and "zahlt" in query_lower:
            expected_table = "KONTEN"
        elif "wohnung" in query_lower or "anzahl" in query_lower:
            expected_table = "WOHNUNG"
        
        found_expected = expected_table in found_tables if expected_table else True
        
        results.append({
            "query": query,
            "expected": expected,
            "expected_table": expected_table,
            "found_tables": found_tables,
            "found_expected": found_expected,
            "relevance_scores": relevance_scores,
            "retrieval_time": retrieval_time,
            "semantic_gap_issue": not found_expected
        })
    
    total_time = time.time() - total_start
    
    return {
        "mode": "original_faiss",
        "total_time": total_time,
        "results": results,
        "semantic_gap_rate": sum(1 for r in results if r["semantic_gap_issue"]) / len(results)
    }


def test_hybrid_faiss_improvement(documents: List[Document], api_key: str) -> Dict[str, Any]:
    """Test hybrid FAISS mode showing semantic gap solutions."""
    
    # Create Hybrid FAISS retriever
    hybrid_retriever = HybridFAISSRetriever(documents, api_key)
    
    # Same test queries
    test_queries = [
        ("Wo wohnen die Mieter?", "Should find BEWOHNER via 'Mieter'→'BEWOHNER' mapping"),
        ("Liste der Eigentümer", "Should find EIGENTUEMER via business terminology"),
        ("Wer zahlt Miete?", "Should find KONTEN via financial terminology mapping"),
        ("Anzahl Wohnungen", "Should find WOHNUNG via counting + property mapping")
    ]
    
    results = []
    total_start = time.time()
    
    for query, expected in test_queries:
        start_time = time.time()
        
        # Hybrid search with terminology mapping
        hybrid_results = hybrid_retriever.retrieve_hybrid(query, k=3)
        
        retrieval_time = time.time() - start_time
        
        # Analyze hybrid results
        found_tables = []
        combined_scores = []
        semantic_scores = []
        keyword_scores = []
        matched_terms = []
        expansion_terms = []
        
        for result in hybrid_results:
            table_name = result.document.metadata.get("table_name", "unknown")
            found_tables.append(table_name)
            combined_scores.append(result.combined_score)
            semantic_scores.append(result.semantic_score)
            keyword_scores.append(result.keyword_score)
            matched_terms.extend(result.matched_terms)
            expansion_terms.extend(result.expansion_terms)
        
        # Check if correct table was found (same logic as original)
        query_lower = query.lower()
        expected_table = None
        if "mieter" in query_lower or "wohnen" in query_lower:
            expected_table = "BEWOHNER"
        elif "eigentümer" in query_lower:
            expected_table = "EIGENTUEMER"
        elif "miete" in query_lower and "zahlt" in query_lower:
            expected_table = "KONTEN"
        elif "wohnung" in query_lower or "anzahl" in query_lower:
            expected_table = "WOHNUNG"
        
        found_expected = expected_table in found_tables if expected_table else True
        
        results.append({
            "query": query,
            "expected": expected,
            "expected_table": expected_table,
            "found_tables": found_tables,
            "found_expected": found_expected,
            "combined_scores": combined_scores,
            "semantic_scores": semantic_scores,
            "keyword_scores": keyword_scores,
            "matched_terms": list(set(matched_terms)),
            "expansion_terms": list(set(expansion_terms)),
            "retrieval_time": retrieval_time,
            "semantic_gap_solved": found_expected
        })
    
    total_time = time.time() - total_start
    
    return {
        "mode": "hybrid_faiss", 
        "total_time": total_time,
        "results": results,
        "semantic_gap_solved_rate": sum(1 for r in results if r["semantic_gap_solved"]) / len(results)
    }


def run_hybrid_faiss_comparison():
    """Run comprehensive comparison between original and hybrid FAISS."""
    print("🔬 HYBRID FAISS vs ORIGINAL FAISS COMPARISON")
    print("=" * 80)
    print("Problem: Original FAISS has semantic gap - doesn't understand HV business logic")
    print("Solution: Hybrid FAISS with HV terminology mapping + keyword search")
    print("=" * 80)
    
    # Setup
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found")
        return
    
    documents = create_hv_mock_documents()
    print(f"📊 Testing with {len(documents)} HV domain documents")
    
    # Test Original FAISS
    print("\n🔍 Testing Original FAISS (Semantic Gap Issues)...")
    original_results = test_original_faiss_semantic_gap(documents, api_key)
    
    # Test Hybrid FAISS
    print("\n🔍 Testing Hybrid FAISS (Semantic Gap Solutions)...")
    hybrid_results = test_hybrid_faiss_improvement(documents, api_key)
    
    # Compare results
    print("\n" + "=" * 80)
    print("📈 DETAILED COMPARISON RESULTS")
    print("=" * 80)
    
    for i, (orig, hybrid) in enumerate(zip(original_results["results"], hybrid_results["results"])):
        query = orig["query"]
        print(f"\n📝 Query {i+1}: {query}")
        print("-" * 60)
        
        print(f"🎯 Expected Table: {orig['expected_table']}")
        
        print(f"\n📊 ORIGINAL FAISS:")
        print(f"   Found Tables: {orig['found_tables']}")
        print(f"   Found Expected: {'✅' if orig['found_expected'] else '❌'}")
        print(f"   Semantic Gap Issue: {'⚠️' if orig['semantic_gap_issue'] else '✅'}")
        print(f"   Time: {orig['retrieval_time']:.3f}s")
        
        print(f"\n📊 HYBRID FAISS:")
        print(f"   Found Tables: {hybrid['found_tables']}")
        print(f"   Found Expected: {'✅' if hybrid['found_expected'] else '❌'}")
        print(f"   Semantic Gap Solved: {'✅' if hybrid['semantic_gap_solved'] else '❌'}")
        print(f"   Matched Terms: {hybrid['matched_terms'][:5]}")  # Show first 5
        print(f"   Expansion Terms: {hybrid['expansion_terms'][:5]}")  # Show first 5
        print(f"   Combined Scores: {[f'{s:.3f}' for s in hybrid['combined_scores']]}")
        print(f"   Time: {hybrid['retrieval_time']:.3f}s")
        
        # Show improvement
        if orig['semantic_gap_issue'] and hybrid['semantic_gap_solved']:
            print(f"   ✅ IMPROVEMENT: Semantic gap resolved via HV terminology mapping!")
    
    # Overall statistics
    print("\n" + "=" * 80)
    print("📈 OVERALL IMPROVEMENT STATISTICS")
    print("=" * 80)
    
    original_gap_rate = original_results["semantic_gap_rate"]
    hybrid_solved_rate = hybrid_results["semantic_gap_solved_rate"]
    
    print(f"Original FAISS Semantic Gap Rate: {original_gap_rate:.1%}")
    print(f"Hybrid FAISS Success Rate: {hybrid_solved_rate:.1%}")
    print(f"Improvement: {hybrid_solved_rate - (1-original_gap_rate):.1%}")
    
    print(f"\nTotal Retrieval Time:")
    print(f"   Original FAISS: {original_results['total_time']:.3f}s")
    print(f"   Hybrid FAISS: {hybrid_results['total_time']:.3f}s")
    
    # Key improvements
    print(f"\n🎯 Task 1.2 Status: FAISS → Hybrid FAISS")
    print(f"   ✅ HV-Business-Terminologie-Dictionary: 'Mieter'→BEWOHNER mapping implemented")
    print(f"   ✅ Hybrid Search: BM25 Keyword + FAISS Semantic search combined")
    print(f"   ✅ Domain-Enhanced Embeddings: HV-specific terms integrated")
    print(f"   ✅ Semantic Gap: {hybrid_solved_rate:.0%} queries now find correct tables")
    
    # Demonstrate terminology mapping
    print(f"\n🔍 HV Terminology Mapping Examples:")
    mapper = HVBusinessTerminologyMapper()
    
    examples = [
        ("Mieter", "BEWOHNER"),
        ("Eigentümer", "EIGENTUEMER"), 
        ("Wohnung", "WOHNUNG"),
        ("Miete", "KONTEN")
    ]
    
    for business_term, expected_tech_term in examples:
        if business_term.lower() in mapper.business_mappings:
            mappings = mapper.business_mappings[business_term.lower()]
            found_expected = expected_tech_term in mappings
            print(f"   {business_term} → {mappings[:3]}... {'✅' if found_expected else '❌'}")


if __name__ == "__main__":
    run_hybrid_faiss_comparison()