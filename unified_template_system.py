#!/usr/bin/env python3
"""
WINCASA Phase 2.3 - Unified Template System
Integriert Intent Router + Template Engine + Optimized Search
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import WINCASA components
from hierarchical_intent_router import HierarchicalIntentRouter, RouterResult

from sql_template_engine import SQLTemplateEngine, TemplateResult
from wincasa_optimized_search import SearchResponse, WincasaOptimizedSearch


@dataclass
class UnifiedResponse:
    """Einheitliche Antwort des Template Systems"""
    query: str
    processing_path: str  # "template", "structured_search", "legacy_fallback"
    intent_result: RouterResult
    template_result: Optional[TemplateResult]
    search_result: Optional[SearchResponse]
    final_answer: str
    confidence: float
    processing_time_ms: float
    result_count: int
    performance_metrics: Dict[str, Any]

class UnifiedTemplateSystem:
    """
    WINCASA Unified Template System - Phase 2.3 Integration
    
    Intelligenter Query-Router der entscheidet:
    1. Template-System (für strukturierte 80% der Queries)
    2. Optimized Search (für flexible Suchen)
    3. Legacy Fallback (für komplexe Analysen)
    
    Performance-Ziel: <100ms für Template-Queries
    """
    
    def __init__(self, 
                 api_key_file="/home/envs/openai.env",
                 debug_mode=False):
        
        self.debug_mode = debug_mode
        
        # Initialize all subsystems
        print("🚀 Initialisiere Unified Template System...")
        
        # Level 1: Intent Router
        self.intent_router = HierarchicalIntentRouter(
            api_key_file=api_key_file,
            debug_mode=debug_mode
        )
        
        # Level 2: Template Engine  
        self.template_engine = SQLTemplateEngine(debug_mode=debug_mode)
        
        # Level 3: Optimized Search (Fallback)
        self.search_system = WincasaOptimizedSearch(debug_mode=debug_mode)
        
        # Performance tracking
        self.query_stats = {
            "total_queries": 0,
            "template_queries": 0,
            "search_queries": 0,
            "legacy_queries": 0,
            "avg_processing_time": 0.0
        }
        
        if self.debug_mode:
            print(f"✅ Unified Template System bereit:")
            print(f"   🎯 Intent Router: {len(self.intent_router.regex_patterns)} Patterns")
            print(f"   📝 Template Engine: {len(self.template_engine.templates)} Templates")
            search_stats = self.search_system.get_stats()
            total_entities = search_stats.get('total_entities', search_stats.get('entities', {}).get('mieter', 0) + search_stats.get('entities', {}).get('eigentuemer', 0) + search_stats.get('entities', {}).get('objekte', 0))
            print(f"   🔍 Search System: {total_entities} Entities")
    
    def process_query(self, query: str) -> UnifiedResponse:
        """
        Hauptfunktion: Intelligente Query-Verarbeitung
        
        Flow:
        1. Intent Classification (Router)
        2. Route zu Template/Search/Legacy
        3. Verarbeitung & Response Generation
        """
        start_time = time.time()
        
        if self.debug_mode:
            print(f"\n🔍 Unified Query: '{query}'")
        
        # Step 1: Intent Classification
        intent_result = self.intent_router.route_intent(query)
        
        # Step 2: Route based on suggested mode
        processing_path = intent_result.suggested_mode
        template_result = None
        search_result = None
        
        if processing_path == "template" and intent_result.template_available:
            # Template-basierte Verarbeitung
            template_result = self._process_template_query(intent_result)
            if template_result and template_result.validation_passed and template_result.result_count > 0:
                final_answer = self._format_template_response(template_result)
                confidence = 0.9
                result_count = template_result.result_count
                self.query_stats["template_queries"] += 1
            else:
                # Template failed → Fallback to Search
                processing_path = "structured_search"
                search_result = self._process_search_query(query)
                final_answer = search_result.answer
                confidence = search_result.confidence
                result_count = len(search_result.search_results)
                self.query_stats["search_queries"] += 1
        
        elif processing_path == "structured_search":
            # Optimized Search
            search_result = self._process_search_query(query)
            final_answer = search_result.answer
            confidence = search_result.confidence
            result_count = len(search_result.search_results)
            self.query_stats["search_queries"] += 1
        
        else:
            # Legacy Fallback (JSON_SYSTEM mode)
            final_answer = f"Komplexe Anfrage - wird an Legacy-System weitergeleitet: '{query}'"
            confidence = 0.4
            result_count = 0
            processing_path = "legacy_fallback"
            self.query_stats["legacy_queries"] += 1
        
        # Step 3: Performance Metrics
        processing_time = round((time.time() - start_time) * 1000, 2)
        self.query_stats["total_queries"] += 1
        
        # Update running average
        total_time = self.query_stats["avg_processing_time"] * (self.query_stats["total_queries"] - 1)
        self.query_stats["avg_processing_time"] = (total_time + processing_time) / self.query_stats["total_queries"]
        
        performance_metrics = {
            "intent_confidence": intent_result.confidence,
            "intent_time_ms": intent_result.processing_time_ms,
            "template_time_ms": template_result.processing_time_ms if template_result else 0,
            "search_time_ms": search_result.processing_time_ms if search_result else 0,
            "total_time_ms": processing_time
        }
        
        if self.debug_mode:
            print(f"   🎯 Path: {processing_path}")
            print(f"   📊 Results: {result_count}")
            print(f"   ⏱️  Total Time: {processing_time}ms")
            print(f"   🎭 Confidence: {confidence:.1%}")
        
        return UnifiedResponse(
            query=query,
            processing_path=processing_path,
            intent_result=intent_result,
            template_result=template_result,
            search_result=search_result,
            final_answer=final_answer,
            confidence=confidence,
            processing_time_ms=processing_time,
            result_count=result_count,
            performance_metrics=performance_metrics
        )
    
    def _process_template_query(self, intent_result: RouterResult) -> Optional[TemplateResult]:
        """Verarbeitet Query über Template Engine"""
        
        # Map intent to template ID
        template_mapping = {
            "mieter_search_location": "mieter_by_location",
            "mieter_contact_lookup": "mieter_contact",
            "owner_search": "owner_by_property", 
            "portfolio_query": "owner_portfolio",
            "vacancy_status": "vacancy_by_location",
            "property_details": "property_details",
            "account_balance": "account_balance"
        }
        
        template_id = template_mapping.get(intent_result.intent_id)
        if not template_id:
            return None
        
        # Prepare template parameters
        parameters = {}
        
        # Map extracted entities to template parameters
        if "location" in intent_result.extracted_entities:
            parameters["location"] = intent_result.extracted_entities["location"]
        
        if "person_name" in intent_result.extracted_entities:
            parameters["person_name"] = intent_result.extracted_entities["person_name"]
        
        # Default parameters
        parameters.setdefault("limit", 10)
        
        # Template-specific parameters
        if template_id == "mieter_contact":
            parameters["partner_search"] = True
        elif template_id == "owner_portfolio":
            parameters["include_companies"] = True
        elif template_id == "vacancy_by_location":
            parameters["only_vacant"] = False  # Show all by default
        elif template_id == "account_balance":
            parameters["include_partners"] = True
            parameters["only_balances"] = False
        
        # Render template
        return self.template_engine.render_template(template_id, parameters)
    
    def _process_search_query(self, query: str) -> SearchResponse:
        """Verarbeitet Query über Optimized Search"""
        return self.search_system.query(query, max_results=10)
    
    def _format_template_response(self, template_result: TemplateResult) -> str:
        """Formatiert Template-Ergebnisse für Benutzer"""
        
        if not template_result.query_results:
            return "Keine Ergebnisse für Ihre Anfrage gefunden."
        
        results = template_result.query_results
        count = len(results)
        
        # Build response based on template type
        if template_result.template_id == "mieter_by_location":
            response = f"Gefunden: {count} Mieter\n\n"
            for i, row in enumerate(results[:5], 1):
                response += f"{i}. {row[0]}"  # MIETER_NAME
                if row[1]:  # PARTNER_NAME
                    response += f" & {row[1]}"
                response += f"\n   📍 {row[2]}\n"  # VOLLSTAENDIGE_ADRESSE
                if row[4]:  # EMAIL
                    response += f"   📧 {row[4]}\n"
                if row[3]:  # TELEFON
                    response += f"   📞 {row[3]}\n"
                response += "\n"
        
        elif template_result.template_id == "owner_portfolio":
            response = f"Gefunden: {count} Eigentümer-Portfolio\n\n"
            for i, row in enumerate(results[:5], 1):
                response += f"{i}. {row[0]}"  # EIGENTUEMER_NAME
                if row[2]:  # FIRMENNAME
                    response += f" ({row[2]})"
                response += f"\n   🏢 {row[3]} Objekte, {row[4]} Einheiten\n"  # ANZAHL_OBJEKTE, ANZAHL_EINHEITEN
                response += f"   📊 Kategorie: {row[5]}\n\n"  # PORTFOLIO_KATEGORIE
        
        elif template_result.template_id == "vacancy_by_location":
            response = f"Gefunden: {count} Objekte\n\n"
            for i, row in enumerate(results[:5], 1):
                response += f"{i}. {row[0]} ({row[1]})\n"  # GEBAEUDE_ADRESSE, STADT
                response += f"   🏠 {row[2]} Einheiten total\n"  # ANZAHL_EINHEITEN_TOTAL
                response += f"   📊 Vermietungsgrad: {row[5]}%\n"  # VERMIETUNGSGRAD_PROZENT
                response += f"   🔄 Status: {row[6]}\n\n"  # VERMIETUNGSSTATUS
        
        else:
            # Generic formatting
            response = f"Gefunden: {count} Ergebnisse\n\n"
            for i, row in enumerate(results[:3], 1):
                response += f"{i}. {row[0] if row else 'N/A'}\n"
        
        if count > 5:
            response += f"... und {count-5} weitere Ergebnisse"
        
        return response
    
    def process_batch(self, queries: List[str]) -> List[UnifiedResponse]:
        """Batch-Verarbeitung für Performance-Tests"""
        results = []
        for query in queries:
            result = self.process_query(query)
            results.append(result)
        return results
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Umfassende System-Statistiken"""
        
        # Route distribution
        total = self.query_stats["total_queries"]
        if total > 0:
            template_pct = (self.query_stats["template_queries"] / total) * 100
            search_pct = (self.query_stats["search_queries"] / total) * 100
            legacy_pct = (self.query_stats["legacy_queries"] / total) * 100
        else:
            template_pct = search_pct = legacy_pct = 0
        
        return {
            "query_statistics": self.query_stats,
            "route_distribution": {
                "template_percentage": round(template_pct, 1),
                "search_percentage": round(search_pct, 1), 
                "legacy_percentage": round(legacy_pct, 1)
            },
            "subsystem_stats": {
                "intent_router": {
                    "regex_patterns": len(self.intent_router.regex_patterns),
                    "llm_available": self.intent_router.client is not None
                },
                "template_engine": {
                    "total_templates": len(self.template_engine.templates),
                    "security_patterns": len(self.template_engine.dangerous_sql_patterns)
                },
                "search_system": self.search_system.get_stats()
            }
        }
    
    def benchmark_with_realistic_queries(self, golden_set_path: str = "realistic_golden_set.json") -> Dict[str, Any]:
        """Benchmark mit realistischen Queries"""
        
        # Load realistic golden set
        try:
            with open(golden_set_path, 'r', encoding='utf-8') as f:
                golden_data = json.load(f)
                test_queries = [q["query"] for q in golden_data["queries"][:20]]  # First 20
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️  Golden Set Load Error: {e}")
            # Fallback test queries
            test_queries = [
                "Wer wohnt in der Aachener Str. 71?",
                "Kontaktdaten von Sundeki Immobilien",
                "Portfolio von Bona Casa GmbH",
                "Freie Wohnungen in Essen",
                "Kontostand von Weber"
            ]
        
        print(f"🧪 Benchmark mit {len(test_queries)} realistischen Queries...")
        
        # Process queries
        results = self.process_batch(test_queries)
        
        # Analyze results
        template_success = sum(1 for r in results if r.processing_path == "template" and r.result_count > 0)
        search_success = sum(1 for r in results if r.processing_path == "structured_search" and r.result_count > 0)
        
        avg_time = sum(r.processing_time_ms for r in results) / len(results)
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        return {
            "benchmark_results": {
                "total_queries": len(results),
                "template_successes": template_success,
                "search_successes": search_success,
                "avg_processing_time_ms": round(avg_time, 2),
                "avg_confidence": round(avg_confidence, 3),
                "success_rate": round((template_success + search_success) / len(results), 3)
            },
            "performance_details": [
                {
                    "query": r.query,
                    "path": r.processing_path,
                    "time_ms": r.processing_time_ms,
                    "results": r.result_count,
                    "confidence": r.confidence
                }
                for r in results
            ]
        }

def test_unified_template_system():
    """Comprehensive Test des Unified Template Systems"""
    print("🚀 Teste Unified Template System...")
    
    system = UnifiedTemplateSystem(debug_mode=True)
    
    # Test mit realistischen Queries (aus Realistic Golden Set)
    realistic_queries = [
        "Wer wohnt in der Aachener Str. 71?",        # Template: mieter_by_location
        "Kontaktdaten von Sundeki Immobilien",       # Template: mieter_contact  
        "Portfolio von Bona Casa GmbH",              # Template: owner_portfolio
        "Freie Wohnungen in Essen",                 # Template: vacancy_by_location
        "Kontostand von Weber",                      # Template: account_balance
        "Mieter ohne Email-Adresse",                # Search: complex analysis
        "GmbH in Köln",                            # Search: flexible search
        "Erstelle einen Bericht über Rückstände"    # Legacy: complex report
    ]
    
    print(f"\n📋 Individual Query Tests:")
    for query in realistic_queries:
        response = system.process_query(query)
        print(f"\n🔍 '{query}'")
        print(f"   🎯 Path: {response.processing_path}")
        print(f"   📊 Results: {response.result_count}")
        print(f"   ⏱️  Time: {response.processing_time_ms}ms")
        print(f"   🎭 Confidence: {response.confidence:.1%}")
        if response.result_count > 0:
            print(f"   💬 Response: {response.final_answer[:100]}...")
    
    # Benchmark Performance
    print(f"\n📊 Realistic Benchmark:")
    benchmark_results = system.benchmark_with_realistic_queries()
    
    for key, value in benchmark_results["benchmark_results"].items():
        print(f"   {key}: {value}")
    
    # System Statistics
    print(f"\n📋 System Statistics:")
    stats = system.get_system_stats()
    
    print(f"   Query Distribution:")
    for key, value in stats["route_distribution"].items():
        print(f"     {key}: {value}%")
    
    print(f"   Average Processing Time: {stats['query_statistics']['avg_processing_time']:.1f}ms")
    
    # Performance Target Check
    template_coverage = stats["route_distribution"]["template_percentage"]
    avg_time = stats["query_statistics"]["avg_processing_time"]
    
    print(f"\n🎯 Performance Targets:")
    print(f"   Template Coverage: {template_coverage}% (Target: >60%)")
    print(f"   Avg Response Time: {avg_time:.1f}ms (Target: <100ms)")
    
    if template_coverage > 60:
        print(f"   ✅ Template Coverage ACHIEVED")
    else:
        print(f"   ⚠️  Template Coverage below target")
    
    if avg_time < 100:
        print(f"   ✅ Performance Target ACHIEVED")
    else:
        print(f"   ⚠️  Performance target missed")

if __name__ == "__main__":
    test_unified_template_system()