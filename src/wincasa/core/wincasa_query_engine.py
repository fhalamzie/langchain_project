#!/usr/bin/env python3
"""
WINCASA Phase 2.4 - Unified Query Engine
Hauptklasse die alle Query-Modi intelligent routet und verwaltet
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Import WINCASA Phase 2 Components
from wincasa.core.unified_template_system import UnifiedResponse, UnifiedTemplateSystem
from wincasa.core.wincasa_optimized_search import SearchResponse, WincasaOptimizedSearch

# Legacy Mode Integration
try:
    from wincasa.core.llm_handler import WincasaLLMHandler

    # Create a wrapper function to match expected interface
    def query_wincasa_system(query: str, mode: str) -> Dict[str, Any]:
        handler = WincasaLLMHandler()
        result = handler.query_llm(query, mode=mode)
        return result
    
    LEGACY_SYSTEM_AVAILABLE = True
except ImportError as e:
    LEGACY_SYSTEM_AVAILABLE = False
    print(f"Warning: Could not import WincasaLLMHandler: {e}")
    # Stub for testing
    def query_wincasa_system(query: str, mode: str) -> Dict[str, Any]:
        return {
            "answer": f"Legacy {mode} response for: {query}",
            "result_count": 5,
            "processing_time": 1500,
            "mode": mode
        }

@dataclass
class QueryEngineResult:
    """Einheitliches Ergebnis des Query Engines"""
    query: str
    user_id: Optional[str]
    processing_mode: str  # "template", "structured_search", "semantic_template", "legacy_json"
    engine_version: str  # "unified_v2", "legacy_v1"
    
    # Results
    answer: str
    confidence: float
    result_count: int
    
    # Performance
    processing_time_ms: float
    cost_estimate: float  # USD
    
    # Technical Details
    unified_response: Optional[UnifiedResponse]
    legacy_response: Optional[Dict]
    
    # Monitoring
    timestamp: datetime
    feature_flags: Dict[str, bool]
    error_details: Optional[str]

# Shadow mode removed - dataclass removed

class WincasaQueryEngine:
    """
    WINCASA Unified Query Engine - Phase 2.4
    
    Intelligenter Router zwischen:
    1. Unified Template System (Phase 2.3)
    2. Legacy JSON Modes (JSON_VANILLA, JSON_SYSTEM, etc.)
    3. Feature Flag Management für graduelle Rollouts
    
    Performance-Ziel: <200ms für 95% der Queries
    """
    
    def __init__(self, 
                 config_file: str = "config/query_engine.json",
                 api_key_file: str = "/home/envs/openai.env",
                 debug_mode: bool = False):
        
        self.debug_mode = debug_mode
        self.config = self._load_config(config_file)
        
        import traceback
        print("🚀 Initialisiere WINCASA Unified Query Engine...")
        print("📍 STACK TRACE für neue WincasaQueryEngine Instanz:")
        traceback.print_stack()
        print("=" * 50)
        
        # Initialize Unified Template System (Phase 2.3)
        self.unified_system = UnifiedTemplateSystem(
            api_key_file=api_key_file,
            debug_mode=debug_mode
        )
        
        # Initialize Semantic Template Engine (Phase 2.6 - Mode 6)
        try:
            from wincasa.core.semantic_template_engine import SemanticTemplateEngine
            self.semantic_engine = SemanticTemplateEngine(
                api_key_file=api_key_file,
                debug_mode=debug_mode
            )
            print("🧩 Semantic Template Engine (Mode 6) initialized")
        except ImportError as e:
            print(f"⚠️ Semantic Template Engine not available: {e}")
            self.semantic_engine = None
        
        # Initialize Structured Search (Phase 2.2)
        self.search_system = WincasaOptimizedSearch(
            rag_data_dir="data/exports/rag_data",
            debug_mode=debug_mode
        )
        
        # Initialize Query Intent Recognizer
        try:
            from wincasa.core.query_intent_recognizer import QueryIntentRecognizer
            self.intent_recognizer = QueryIntentRecognizer()
            print("🎯 Query Intent Recognizer initialized")
        except ImportError:
            print("⚠️ Query Intent Recognizer not available")
            self.intent_recognizer = None
        
        # Performance & Monitoring
        self.query_stats = {
            "total_queries": 0,
            "unified_queries": 0,
            "semantic_queries": 0,  # Mode 6 tracking
            "legacy_queries": 0,
            "avg_processing_time": 0.0,
            "avg_cost_per_query": 0.0
        }
        
        # Performance tracking
        self.performance_history = []
        
        if self.debug_mode:
            print(f"✅ Query Engine bereit:")
            print(f"   🎛️  Feature Flags: {self.config['feature_flags']}")
            print(f"   🎯 Unified Rollout: {self.config['rollout']['unified_percentage']}%")
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Lädt Query Engine Konfiguration"""
        config_path = Path(config_file)
        
        # Default configuration
        default_config = {
            "feature_flags": {
                "unified_system_enabled": True,
                "monitoring_enabled": True,
                "cost_tracking_enabled": True
            },
            "rollout": {
                "unified_percentage": 0,  # Start with 0%
                "hash_salt": "wincasa_2024",
                "override_users": []  # Always use unified for these users
            },
            "performance": {
                "max_processing_time_ms": 10000,
                "cost_alert_threshold": 0.10,  # $0.10 per query
                "quality_threshold": 0.7
            },
            "legacy_modes": {
                "default_mode": "JSON_VANILLA",
                "fallback_mode": "JSON_SYSTEM"
            }
        }
        
        # Load from file if exists
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # Merge with defaults
                    for key, value in file_config.items():
                        if isinstance(value, dict) and key in default_config:
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                if self.debug_mode:
                    print(f"⚠️  Config load error: {e}, using defaults")
        
        return default_config
    
    def _should_use_unified(self, user_id: Optional[str] = None) -> bool:
        """Entscheidet ob Unified System verwendet werden soll"""
        
        # Feature flag check
        if not self.config["feature_flags"]["unified_system_enabled"]:
            return False
        
        # Override users always get unified
        if user_id and user_id in self.config["rollout"]["override_users"]:
            return True
        
        # Percentage-based rollout with hash
        rollout_percentage = self.config["rollout"]["unified_percentage"]
        
        if rollout_percentage == 0:
            return False
        elif rollout_percentage >= 100:
            return True
        
        # Hash-based consistent assignment
        if user_id:
            hash_input = f"{user_id}{self.config['rollout']['hash_salt']}"
            hash_value = hashlib.md5(hash_input.encode()).hexdigest()
            hash_percentage = int(hash_value[:2], 16) / 255 * 100
            return hash_percentage < rollout_percentage
        
        return False
    
    def _process_legacy_query(self, query: str, mode: str = None) -> Dict[str, Any]:
        """Verarbeitet Query über Legacy System"""
        
        if mode is None:
            mode = self.config["legacy_modes"]["default_mode"]
        
        start_time = time.time()
        
        try:
            # Call legacy streamlit system
            legacy_result = query_wincasa_system(query, mode)
            
            processing_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "answer": legacy_result.get("answer", "Keine Antwort verfügbar"),
                "mode": mode,
                "processing_time_ms": processing_time,
                "success": True,
                "result_count": legacy_result.get("result_count", 0),
                "cost_estimate": self._estimate_legacy_cost(query, mode),
                "raw_result": legacy_result
            }
            
        except Exception as e:
            processing_time = round((time.time() - start_time) * 1000, 2)
            
            if self.debug_mode:
                print(f"   ❌ Legacy processing error: {e}")
            
            return {
                "answer": f"Legacy-System Fehler: {str(e)}",
                "mode": mode,
                "processing_time_ms": processing_time,
                "success": False,
                "result_count": 0,
                "cost_estimate": 0.0,
                "error": str(e)
            }
    
    def _estimate_legacy_cost(self, query: str, mode: str) -> float:
        """Schätzt Kosten für Legacy-Query"""
        # Simplified cost estimation
        if mode in ["JSON_SYSTEM", "SQL_SYSTEM"]:
            # These use GPT-4o calls
            return 0.05  # Estimate $0.05 per query
        else:
            # JSON_VANILLA uses no LLM
            return 0.0
    
    def _estimate_unified_cost(self, unified_response: UnifiedResponse) -> float:
        """Schätzt Kosten für Unified Query"""
        if unified_response.processing_path == "legacy_fallback":
            return 0.05  # Legacy LLM cost
        elif unified_response.processing_path == "template":
            return 0.01  # Small LLM cost for intent classification
        elif unified_response.processing_path == "semantic_template":
            return 0.01  # Lightweight LLM cost for intent extraction
        else:
            return 0.0   # Pure structured search - no LLM cost
    
    
    def process_query(self, 
                     query: str, 
                     user_id: Optional[str] = None,
                     force_mode: Optional[str] = None) -> QueryEngineResult:
        """
        Hauptfunktion: Intelligente Query-Verarbeitung
        
        Args:
            query: Die Benutzer-Anfrage
            user_id: Optional User ID für Feature Flags
            force_mode: Optional mode override ("unified", "legacy")
        """
        start_time = time.time()
        
        if self.debug_mode:
            print(f"\n🔍 Query Engine: '{query}'")
            if user_id:
                print(f"   👤 User: {user_id}")
        
        # Always log the query start
        print(f"[WincasaQueryEngine] Processing query: '{query[:50]}...' for user: {user_id}")
        
        # Analyze query intent if recognizer is available
        query_analysis = None
        if self.intent_recognizer:
            try:
                query_analysis = self.intent_recognizer.analyze(query)
                if self.debug_mode:
                    print(f"   🎯 Intent: {query_analysis.intent.value} (confidence: {query_analysis.confidence:.2f})")
                    if query_analysis.entities:
                        print(f"   📋 Entities: {query_analysis.entities}")
            except Exception as e:
                if self.debug_mode:
                    print(f"   ⚠️ Intent analysis failed: {e}")
        
        # Determine processing mode
        use_unified = force_mode == "unified" or (
            force_mode != "legacy" and 
            self._should_use_unified(user_id)
        )
        
        # Shadow mode removed
        
        unified_response = None
        legacy_response = None
        
        # Main processing path
        if use_unified:
            # NEW: Check for Semantic Template patterns first (Mode 6)
            semantic_result = None
            if self.semantic_engine:
                can_handle, semantic_confidence = self.semantic_engine.can_handle_query(query)
                if can_handle and semantic_confidence > 0.7:
                    # Process with Semantic Template Engine
                    try:
                        semantic_result = self.semantic_engine.process_query(query)
                        
                        if semantic_result.success:
                            answer = semantic_result.answer
                            confidence = semantic_result.confidence
                            result_count = semantic_result.result_count
                            processing_mode = "semantic_template"
                            engine_version = "unified_v2_mode6"
                            cost_estimate = 0.01  # Lightweight LLM cost for intent extraction
                            
                            self.query_stats["semantic_queries"] += 1
                            
                            if self.debug_mode:
                                print(f"   ✅ Semantic Template successful: {semantic_result.pattern.pattern_id}")
                        
                    except Exception as e:
                        if self.debug_mode:
                            print(f"   ⚠️ Semantic Template failed: {e}")
                        semantic_result = None
            
            # If semantic processing failed or not applicable, use Unified Template System
            if not semantic_result or not semantic_result.success:
                try:
                    unified_response = self.unified_system.process_query(query)
                    
                    answer = unified_response.final_answer
                    confidence = unified_response.confidence
                    result_count = unified_response.result_count
                    processing_mode = unified_response.processing_path
                    engine_version = "unified_v2"
                    cost_estimate = self._estimate_unified_cost(unified_response)
                    
                    self.query_stats["unified_queries"] += 1
                    
                except Exception as e:
                    if self.debug_mode:
                        print(f"   ❌ Unified system error: {e}")
                    
                    # Fallback to legacy
                    legacy_result = self._process_legacy_query(query)
                    answer = legacy_result["answer"]
                    confidence = 0.3  # Low confidence due to fallback
                    result_count = legacy_result["result_count"]
                    processing_mode = "legacy_fallback"
                    engine_version = "legacy_v1"
                    cost_estimate = legacy_result["cost_estimate"]
                    
                    self.query_stats["legacy_queries"] += 1
        
        else:
            # Use Legacy System
            legacy_result = self._process_legacy_query(query)
            legacy_response = legacy_result
            
            answer = legacy_result["answer"]
            confidence = 0.7 if legacy_result["success"] else 0.2
            result_count = legacy_result["result_count"]
            processing_mode = f"legacy_{legacy_result['mode'].lower()}"
            engine_version = "legacy_v1"
            cost_estimate = legacy_result["cost_estimate"]
            
            self.query_stats["legacy_queries"] += 1
        
        # Performance tracking
        if use_unified and unified_response:
            self.performance_history.append({
                "timestamp": datetime.now(),
                "processing_time_ms": unified_response.processing_time_ms,
                "result_count": result_count,
                "confidence": confidence
            })
        
        # Final processing
        total_processing_time = round((time.time() - start_time) * 1000, 2)
        self.query_stats["total_queries"] += 1
        
        # Update running averages
        total_queries = self.query_stats["total_queries"]
        self.query_stats["avg_processing_time"] = (
            (self.query_stats["avg_processing_time"] * (total_queries - 1) + total_processing_time) / total_queries
        )
        self.query_stats["avg_cost_per_query"] = (
            (self.query_stats["avg_cost_per_query"] * (total_queries - 1) + cost_estimate) / total_queries
        )
        
        if self.debug_mode:
            print(f"   🎯 Mode: {processing_mode}")
            print(f"   📊 Results: {result_count}")
            print(f"   ⏱️  Time: {total_processing_time}ms")
            print(f"   💰 Cost: ${cost_estimate:.4f}")
        
        return QueryEngineResult(
            query=query,
            user_id=user_id,
            processing_mode=processing_mode,
            engine_version=engine_version,
            answer=answer,
            confidence=confidence,
            result_count=result_count,
            processing_time_ms=total_processing_time,
            cost_estimate=cost_estimate,
            unified_response=unified_response,
            legacy_response=legacy_response,
            timestamp=datetime.now(),
            feature_flags=self.config["feature_flags"].copy(),
            error_details=None
        )
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """Analysiert Performance History"""
        if not self.performance_history:
            return {"error": "No performance data available"}
        
        history = self.performance_history
        
        # Performance Analysis
        response_times = [h["processing_time_ms"] for h in history]
        avg_response_time = sum(response_times) / len(response_times)
        
        # Success analysis
        successful_queries = sum(1 for h in history if h["result_count"] > 0)
        success_rate = successful_queries / len(history)
        
        # Confidence analysis
        confidences = [h["confidence"] for h in history]
        avg_confidence = sum(confidences) / len(confidences)
        
        return {
            "total_queries": len(history),
            "performance": {
                "avg_response_time_ms": round(avg_response_time, 2),
                "min_response_time_ms": round(min(response_times), 2),
                "max_response_time_ms": round(max(response_times), 2)
            },
            "quality": {
                "success_rate": round(success_rate, 3),
                "avg_confidence": round(avg_confidence, 3)
            },
            "recommendation": self._get_performance_recommendation(avg_response_time, success_rate)
        }
    
    def _get_performance_recommendation(self, avg_response_time: float, success_rate: float) -> str:
        """Gibt Performance-Empfehlung basierend auf aktuellen Daten"""
        
        if avg_response_time < 200 and success_rate > 0.9:
            return "🚀 EXCELLENT: System performing optimally"
        elif avg_response_time < 500 and success_rate > 0.8:
            return "✅ GOOD: Performance within acceptable range"
        elif avg_response_time < 1000 and success_rate > 0.7:
            return "🤔 MODERATE: Consider optimization"
        else:
            return "❌ POOR: Optimization required"
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Umfassende System-Statistiken"""
        
        # Route distribution
        total = self.query_stats["total_queries"]
        if total > 0:
            unified_pct = (self.query_stats["unified_queries"] / total) * 100
            legacy_pct = (self.query_stats["legacy_queries"] / total) * 100
        else:
            unified_pct = legacy_pct = 0
        
        return {
            "query_statistics": self.query_stats,
            "route_distribution": {
                "unified_percentage": round(unified_pct, 1),
                "legacy_percentage": round(legacy_pct, 1)
            },
            "configuration": {
                "rollout_percentage": self.config["rollout"]["unified_percentage"],
                "feature_flags": self.config["feature_flags"]
            },
            "subsystem_stats": {
                "unified_system": self.unified_system.get_system_stats(),
                "search_system": self.search_system.get_stats()
            }
        }
    
    def update_rollout_percentage(self, new_percentage: int):
        """Aktualisiert Rollout-Prozentsatz für Feature Flag"""
        if 0 <= new_percentage <= 100:
            self.config["rollout"]["unified_percentage"] = new_percentage
            print(f"📊 Rollout percentage updated to {new_percentage}%")
        else:
            print(f"❌ Invalid percentage: {new_percentage}. Must be 0-100.")

def test_query_engine():
    """Test des Unified Query Engines"""
    print("🧪 Teste WINCASA Unified Query Engine...")
    
    engine = WincasaQueryEngine(debug_mode=True)
    
    # Test Queries
    test_queries = [
        ("Wer wohnt in der Aachener Str. 71?", "user123"),
        ("Portfolio von Bona Casa GmbH", "user456"),
        ("Freie Wohnungen in Essen", "user789"),
        ("Erstelle einen Bericht über alle Rückstände", "user123")  # Should go to legacy
    ]
    
    print(f"\n📋 Query Engine Tests:")
    
    for query, user_id in test_queries:
        print(f"\n🔍 Query: '{query}' (User: {user_id})")
        
        # Test both modes
        for force_mode in [None, "unified", "legacy"]:
            mode_label = force_mode or "auto"
            result = engine.process_query(query, user_id, force_mode)
            
            print(f"   [{mode_label.upper()}] Engine: {result.engine_version}")
            print(f"   [{mode_label.upper()}] Mode: {result.processing_mode}")
            print(f"   [{mode_label.upper()}] Time: {result.processing_time_ms}ms")
            print(f"   [{mode_label.upper()}] Results: {result.result_count}")
            print(f"   [{mode_label.upper()}] Cost: ${result.cost_estimate:.4f}")
    
    # Performance Analysis
    print(f"\n📊 Performance Analysis:")
    perf_analysis = engine.get_performance_analysis()
    
    if "error" not in perf_analysis:
        print(f"   Total Queries: {perf_analysis['total_queries']}")
        print(f"   Avg Response Time: {perf_analysis['performance']['avg_response_time_ms']:.1f}ms")
        print(f"   Success Rate: {perf_analysis['quality']['success_rate']:.1%}")
        print(f"   Recommendation: {perf_analysis['recommendation']}")
    
    # System Stats
    print(f"\n📋 System Statistics:")
    stats = engine.get_system_stats()
    
    print(f"   Total Queries: {stats['query_statistics']['total_queries']}")
    print(f"   Unified: {stats['route_distribution']['unified_percentage']}%")
    print(f"   Legacy: {stats['route_distribution']['legacy_percentage']}%")
    print(f"   Avg Time: {stats['query_statistics']['avg_processing_time']:.1f}ms")
    print(f"   Avg Cost: ${stats['query_statistics']['avg_cost_per_query']:.4f}")

if __name__ == "__main__":
    test_query_engine()