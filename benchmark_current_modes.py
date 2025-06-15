#!/usr/bin/env python3
"""
WINCASA Phase 2.1 - Baseline Performance Benchmark
Testet alle 4 Modi gegen das Golden Set für Baseline-Metriken
"""

import json
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import sys

# Import WINCASA modules
sys.path.append('.')
import os

def setup_logging():
    """Setup Logging für Benchmark"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/benchmark.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def load_golden_set() -> List[Dict]:
    """Lädt das Golden Set"""
    try:
        with open("golden_set/queries.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data["queries"]
    except Exception as e:
        print(f"❌ Fehler beim Laden des Golden Sets: {e}")
        return []

def test_streamlit_mode(query: str, mode: str) -> Dict[str, Any]:
    """Testet eine Query gegen einen echten Streamlit Mode"""
    try:
        start_time = time.time()
        
        # Echte LLM-Handler Implementierung
        from llm_handler import WincasaLLMHandler
        
        # Temporär SYSTEM_MODE für diesen Test setzen
        original_mode = os.environ.get('SYSTEM_MODE')
        
        mode_mapping = {
            "VERSION_A_JSON_SYSTEM": "json_standard",
            "VERSION_A_JSON_VANILLA": "json_vanilla", 
            "VERSION_B_SQL_SYSTEM": "sql_standard",
            "VERSION_B_SQL_VANILLA": "sql_vanilla"
        }
        
        if mode not in mode_mapping:
            raise ValueError(f"Unbekannter Mode: {mode}")
        
        # Setze SYSTEM_MODE für diesen Test
        os.environ['SYSTEM_MODE'] = mode_mapping[mode]
        
        try:
            # Initialisiere LLM Handler für diesen Mode
            llm_handler = WincasaLLMHandler()
            
            # Führe echte Query aus
            response_data = llm_handler.query_llm(query, mode_mapping[mode])
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "response": response_data.get("answer", ""),
                "sql_generated": response_data.get("sql", None),
                "execution_time_ms": round(execution_time * 1000, 2),
                "error": None,
                "tokens_used": response_data.get("tokens_used", 0),
                "mode": mode,
                "raw_response": response_data
            }
            
        finally:
            # SYSTEM_MODE zurücksetzen
            if original_mode:
                os.environ['SYSTEM_MODE'] = original_mode
            elif 'SYSTEM_MODE' in os.environ:
                del os.environ['SYSTEM_MODE']
        
    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "success": False,
            "response": None,
            "sql_generated": None,
            "execution_time_ms": round(execution_time * 1000, 2),
            "error": str(e),
            "tokens_used": 0,
            "mode": mode,
            "raw_response": None
        }

def evaluate_response_quality(query: Dict, response: str, expected_data: str) -> Dict[str, float]:
    """Bewertet die Qualität der Response (vereinfacht für Baseline)"""
    
    # Basis-Metriken (für echte Implementierung später erweitern)
    metrics = {
        "relevance_score": 0.0,
        "completeness_score": 0.0,
        "accuracy_score": 0.0,
        "overall_score": 0.0
    }
    
    if not response:
        return metrics
    
    query_text = query["query"].lower()
    response_lower = response.lower()
    
    # Einfache Keyword-basierte Bewertung
    keywords = query_text.split()
    keyword_matches = sum(1 for kw in keywords if kw in response_lower)
    
    if keywords:
        metrics["relevance_score"] = min(keyword_matches / len(keywords), 1.0)
    
    # Vollständigkeit basierend auf Response-Länge
    if len(response) > 50:
        metrics["completeness_score"] = 0.8
    elif len(response) > 20:
        metrics["completeness_score"] = 0.5
    else:
        metrics["completeness_score"] = 0.2
    
    # Genauigkeit (Mock - später durch echte Validierung)
    if "error" not in response_lower and "nicht verfügbar" not in response_lower:
        metrics["accuracy_score"] = 0.7
    else:
        metrics["accuracy_score"] = 0.3
    
    # Gesamt-Score
    metrics["overall_score"] = (
        metrics["relevance_score"] * 0.4 +
        metrics["completeness_score"] * 0.3 +
        metrics["accuracy_score"] * 0.3
    )
    
    return metrics

def benchmark_all_modes(sample_size: int = 10):
    """Führt Benchmark gegen alle 4 Modi aus"""
    
    logger = setup_logging()
    logger.info("🚀 Starting WINCASA Baseline Benchmark")
    
    # Golden Set laden
    golden_queries = load_golden_set()
    if not golden_queries:
        logger.error("❌ Kein Golden Set gefunden!")
        return
    
    # Für schnellen Test: nur Sample der Queries verwenden
    if sample_size and sample_size < len(golden_queries):
        golden_queries = golden_queries[:sample_size]
        logger.info(f"📊 Using sample of {sample_size} queries for faster testing")
    
    # Modi definieren
    modes = [
        "VERSION_A_JSON_SYSTEM",
        "VERSION_A_JSON_VANILLA", 
        "VERSION_B_SQL_SYSTEM",
        "VERSION_B_SQL_VANILLA"
    ]
    
    # Benchmark-Ergebnisse
    results = {
        "benchmark_info": {
            "timestamp": datetime.now().isoformat(),
            "total_queries": len(golden_queries),
            "modes_tested": modes,
            "version": "baseline_v1.0"
        },
        "mode_results": {},
        "summary": {}
    }
    
    # Für jeden Mode testen
    for mode in modes:
        logger.info(f"📊 Testing Mode: {mode}")
        
        mode_results = {
            "mode": mode,
            "total_queries": len(golden_queries),
            "successful_queries": 0,
            "failed_queries": 0,
            "total_execution_time_ms": 0,
            "avg_execution_time_ms": 0,
            "total_tokens_used": 0,
            "avg_tokens_per_query": 0,
            "quality_metrics": {
                "avg_relevance_score": 0.0,
                "avg_completeness_score": 0.0,
                "avg_accuracy_score": 0.0,
                "avg_overall_score": 0.0
            },
            "query_results": []
        }
        
        # Jede Query testen
        for i, query in enumerate(golden_queries):
            if i % 10 == 0:
                logger.info(f"  Progress: {i}/{len(golden_queries)} queries")
            
            # Query ausführen
            response_data = test_streamlit_mode(query["query"], mode)
            
            # Quality bewerten
            if response_data["success"]:
                quality_metrics = evaluate_response_quality(
                    query, 
                    response_data["response"], 
                    query["expected_data"]
                )
                mode_results["successful_queries"] += 1
            else:
                quality_metrics = {
                    "relevance_score": 0.0,
                    "completeness_score": 0.0,
                    "accuracy_score": 0.0,
                    "overall_score": 0.0
                }
                mode_results["failed_queries"] += 1
            
            # Query-Result sammeln
            query_result = {
                "query_id": query["id"],
                "query_text": query["query"],
                "category": query["category"],
                "intent": query["intent"],
                "response_data": response_data,
                "quality_metrics": quality_metrics
            }
            
            mode_results["query_results"].append(query_result)
            mode_results["total_execution_time_ms"] += response_data["execution_time_ms"]
            mode_results["total_tokens_used"] += response_data["tokens_used"]
        
        # Mode-Statistiken berechnen
        if mode_results["successful_queries"] > 0:
            mode_results["avg_execution_time_ms"] = round(
                mode_results["total_execution_time_ms"] / len(golden_queries), 2
            )
            mode_results["avg_tokens_per_query"] = round(
                mode_results["total_tokens_used"] / len(golden_queries), 2
            )
            
            # Quality-Metriken aggregieren
            successful_results = [r for r in mode_results["query_results"] 
                                if r["response_data"]["success"]]
            
            if successful_results:
                mode_results["quality_metrics"]["avg_relevance_score"] = round(
                    sum(r["quality_metrics"]["relevance_score"] for r in successful_results) / len(successful_results), 3
                )
                mode_results["quality_metrics"]["avg_completeness_score"] = round(
                    sum(r["quality_metrics"]["completeness_score"] for r in successful_results) / len(successful_results), 3
                )
                mode_results["quality_metrics"]["avg_accuracy_score"] = round(
                    sum(r["quality_metrics"]["accuracy_score"] for r in successful_results) / len(successful_results), 3
                )
                mode_results["quality_metrics"]["avg_overall_score"] = round(
                    sum(r["quality_metrics"]["overall_score"] for r in successful_results) / len(successful_results), 3
                )
        
        results["mode_results"][mode] = mode_results
        logger.info(f"✅ Mode {mode} completed: {mode_results['successful_queries']}/{len(golden_queries)} successful")
    
    # Summary erstellen
    summary = {
        "best_mode_by_success_rate": "",
        "best_mode_by_speed": "",
        "best_mode_by_quality": "",
        "overall_statistics": {
            "total_queries_tested": len(golden_queries) * len(modes),
            "global_success_rate": 0.0,
            "avg_response_time_ms": 0.0,
            "total_tokens_used": sum(mr["total_tokens_used"] for mr in results["mode_results"].values())
        }
    }
    
    # Beste Modi ermitteln
    best_success_rate = 0
    best_speed = float('inf')
    best_quality = 0
    
    total_successful = 0
    total_time = 0
    
    for mode, mode_data in results["mode_results"].items():
        success_rate = mode_data["successful_queries"] / mode_data["total_queries"]
        avg_time = mode_data["avg_execution_time_ms"]
        quality = mode_data["quality_metrics"]["avg_overall_score"]
        
        total_successful += mode_data["successful_queries"]
        total_time += mode_data["total_execution_time_ms"]
        
        if success_rate > best_success_rate:
            best_success_rate = success_rate
            summary["best_mode_by_success_rate"] = mode
        
        if avg_time < best_speed:
            best_speed = avg_time
            summary["best_mode_by_speed"] = mode
        
        if quality > best_quality:
            best_quality = quality
            summary["best_mode_by_quality"] = mode
    
    summary["overall_statistics"]["global_success_rate"] = round(
        total_successful / (len(golden_queries) * len(modes)), 3
    )
    summary["overall_statistics"]["avg_response_time_ms"] = round(
        total_time / (len(golden_queries) * len(modes)), 2
    )
    
    results["summary"] = summary
    
    # Ergebnisse speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Vollständige Ergebnisse
    with open(f"golden_set/baseline_results_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Kompakte Summary
    compact_summary = {
        "timestamp": results["benchmark_info"]["timestamp"],
        "modes": {mode: {
            "success_rate": f"{mr['successful_queries']}/{mr['total_queries']}",
            "avg_time_ms": mr["avg_execution_time_ms"],
            "avg_quality": mr["quality_metrics"]["avg_overall_score"]
        } for mode, mr in results["mode_results"].items()},
        "best_modes": summary
    }
    
    with open("golden_set/baseline_summary.json", "w", encoding="utf-8") as f:
        json.dump(compact_summary, f, indent=2, ensure_ascii=False)
    
    # Ergebnisse ausgeben
    logger.info("🎯 Baseline Benchmark abgeschlossen!")
    logger.info(f"📊 Beste Modi:")
    logger.info(f"  Success Rate: {summary['best_mode_by_success_rate']}")
    logger.info(f"  Speed: {summary['best_mode_by_speed']}")
    logger.info(f"  Quality: {summary['best_mode_by_quality']}")
    logger.info(f"📈 Global Success Rate: {summary['overall_statistics']['global_success_rate']}")
    logger.info(f"⏱️  Avg Response Time: {summary['overall_statistics']['avg_response_time_ms']}ms")
    
    return results

if __name__ == "__main__":
    # Starte mit kleinem Sample für schnellen Test
    benchmark_all_modes(sample_size=5)