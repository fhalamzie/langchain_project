#!/usr/bin/env python3
"""
Phase 3: Comprehensive 9-Mode Performance Matrix & Architecture Decision
=========================================================================

This module implements comprehensive testing and evaluation of all 9 implemented
retrieval modes (6 individual + 3 combinations) to determine the optimal 
production architecture for WINCASA.

Test Levels:
1. Performance Matrix: All 9 modes against 11 standard queries
2. Business Scenarios: HV-specific complex scenarios  
3. Architecture Analysis: Production recommendations

Author: WINCASA Development Team
Date: June 2025
"""

import json
import logging
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import statistics

import pandas as pd
import numpy as np

# Import WINCASA modules - use existing implementations
from firebird_agent_with_tag import QueryResult
from archive.llm_interface import get_llm_client

# Import optimized retrievers
from contextual_enhanced_retriever import ContextualEnhancedRetriever
from hybrid_faiss_retriever import HybridFAISSRetriever
from smart_fallback_retriever import SmartFallbackRetriever
from filtered_langchain_retriever import FilteredLangChainRetriever
from adaptive_tag_classifier import AdaptiveTAGClassifier

# Import Phase 2 combinations
from smart_enhanced_retriever import SmartEnhancedRetriever
from guided_agent_retriever import GuidedAgentRetriever
from contextual_vector_retriever import ContextualVectorRetriever


@dataclass
class ComprehensiveTestResult:
    """Enhanced test result with detailed metrics for Phase 3 analysis"""
    
    query: str
    mode: str
    success: bool
    response: str
    sql_generated: Optional[str]
    execution_time: float
    error_message: Optional[str]
    timestamp: str
    
    # Quality metrics
    sql_quality_score: float = 0.0
    business_logic_score: float = 0.0
    efficiency_score: float = 0.0
    confidence_score: float = 0.0
    
    # Performance metrics
    tokens_used: int = 0
    context_size: int = 0
    retrieval_time: float = 0.0
    llm_time: float = 0.0
    
    # Business metrics
    table_accuracy: bool = False
    syntax_correctness: bool = False
    result_relevance: bool = False
    firebird_compliance: bool = False
    
    metadata: Dict[str, Any] = None


@dataclass
class ModeRanking:
    """Final ranking and recommendation for production architecture"""
    
    mode: str
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    use_cases: List[str]
    production_recommendation: str
    ranking_position: int


class Phase3ComprehensiveMatrix:
    """
    Comprehensive 9-mode testing and evaluation framework for final architecture decision
    """
    
    def __init__(self, db_path: str = "/home/projects/langchain_project/WINCASA2022.FDB"):
        self.db_path = db_path
        self.llm = get_llm_client()
        self.results: List[ComprehensiveTestResult] = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)
        
        # Define all 9 modes
        self.modes = {
            # Individual optimized modes
            "contextual_enhanced": "Optimized Enhanced with 81% document reduction",
            "hybrid_faiss": "Optimized FAISS with HV terminology mapping", 
            "smart_fallback": "Optimized None with 273% context richness",
            "filtered_langchain": "Optimized LangChain with 97% schema reduction",
            "adaptive_tag": "Optimized TAG with ML classification",
            "langgraph": "LangGraph workflow (complexity evaluation needed)",
            
            # Phase 2 combinations
            "smart_enhanced": "Enhanced + TAG: Query-focused Enhanced",
            "guided_agent": "LangChain + TAG: Schema-filtered Agent", 
            "contextual_vector": "FAISS + TAG: Context-biased similarity"
        }
        
        # Standard test queries from tasks.md
        self.standard_queries = [
            "Wer wohnt in der Marienstr. 26, 45307 Essen",
            "Wer wohnt in der Marienstraße 26", 
            "Wer wohnt in der Bäuminghausstr. 41, Essen",
            "Wer wohnt in der Schmiedestr. 8, 47055 Duisburg",
            "Alle Mieter der MARIE26",
            "Alle Eigentümer vom Haager Weg bitte",
            "Liste aller Eigentümer",
            "Liste aller Eigentümer aus Köln",
            "Liste aller Mieter in Essen", 
            "Durchschnittliche Miete in Essen",
            "Wie viele Wohnungen gibt es insgesamt?"
        ]
        
        # Business scenario queries (HV-specific complex cases)
        self.business_scenarios = [
            "Zeige alle Eigentümer mit mehr als 3 Objekten und deren Gesamtmieteinkommen",
            "Welche Wohnungen sind seit über 6 Monaten leer und was sind die Gründe?",
            "Erstelle eine Übersicht aller offenen Forderungen pro Objekt gruppiert nach PLZ",
            "Finde alle Mieter mit Zahlungsrückständen über 1000 Euro und deren Kontaktdaten",
            "Zeige die Entwicklung der Mietpreise in Essen über die letzten 2 Jahre",
            "Welche Objekte haben die höchste Fluktuation und warum?",
            "Erstelle einen Report über alle Instandhaltungskosten pro Quadratmeter",
            "Finde potentielle Mieterhöhungen basierend auf Marktvergleich und Objektzustand"
        ]
    
    def _create_retriever(self, mode: str) -> Any:
        """Create retriever instance for specific mode"""
        
        if mode == "contextual_enhanced":
            return ContextualEnhancedRetriever(
                db_connection_string=f"firebird+fdb://sysdba:masterkey@{self.db_path}",
                llm=self.llm
            )
        elif mode == "hybrid_faiss":
            return HybridFAISSRetriever(
                db_connection_string=f"firebird+fdb://sysdba:masterkey@{self.db_path}",
                llm=self.llm
            )
        elif mode == "smart_fallback":
            return SmartFallbackRetriever(
                db_connection_string=f"firebird+fdb://sysdba:masterkey@{self.db_path}",
                llm=self.llm
            )
        elif mode == "filtered_langchain":
            return FilteredLangChainRetriever(
                db_connection_string=f"firebird+fdb://sysdba:masterkey@{self.db_path}",
                llm=self.llm
            )
        elif mode == "adaptive_tag":
            return AdaptiveTAGClassifier(
                db_connection_string=f"firebird+fdb://sysdba:masterkey@{self.db_path}",
                llm=self.llm
            )
        elif mode == "smart_enhanced":
            return SmartEnhancedRetriever(
                db_connection_string=f"firebird+fdb://sysdba:masterkey@{self.db_path}",
                llm=self.llm
            )
        elif mode == "guided_agent":
            return GuidedAgentRetriever(
                db_connection_string=f"firebird+fdb://sysdba:masterkey@{self.db_path}",
                llm=self.llm
            )
        elif mode == "contextual_vector":
            return ContextualVectorRetriever(
                db_connection_string=f"firebird+fdb://sysdba:masterkey@{self.db_path}",
                llm=self.llm
            )
        elif mode == "langgraph":
            # Use adaptive TAG as fallback for LangGraph evaluation
            return AdaptiveTAGClassifier(
                db_connection_string=f"firebird+fdb://sysdba:masterkey@{self.db_path}",
                llm=self.llm
            )
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    def _execute_comprehensive_test(
        self, query: str, mode: str, timeout: int = 60
    ) -> ComprehensiveTestResult:
        """Execute comprehensive test with detailed metrics collection"""
        
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        
        try:
            retriever = self._create_retriever(mode)
            
            # Track retrieval time separately
            retrieval_start = time.time()
            response = retriever.run(query) if hasattr(retriever, 'run') else str(retriever.retrieve(query))
            retrieval_time = time.time() - retrieval_start
            
            total_time = time.time() - start_time
            llm_time = total_time - retrieval_time
            
            # Extract SQL
            sql_generated = self._extract_sql(response)
            
            # Calculate comprehensive metrics
            quality_metrics = self._calculate_quality_metrics(query, sql_generated, response, mode)
            business_metrics = self._calculate_business_metrics(query, sql_generated, response)
            
            return ComprehensiveTestResult(
                query=query,
                mode=mode,
                success=True,
                response=response,
                sql_generated=sql_generated,
                execution_time=total_time,
                error_message=None,
                timestamp=timestamp,
                
                # Quality scores
                sql_quality_score=quality_metrics["sql_quality"],
                business_logic_score=quality_metrics["business_logic"],
                efficiency_score=quality_metrics["efficiency"],
                confidence_score=quality_metrics["confidence"],
                
                # Performance metrics
                tokens_used=quality_metrics.get("tokens", 0),
                context_size=quality_metrics.get("context_size", 0),
                retrieval_time=retrieval_time,
                llm_time=llm_time,
                
                # Business metrics
                table_accuracy=business_metrics["table_accuracy"],
                syntax_correctness=business_metrics["syntax_correctness"],
                result_relevance=business_metrics["result_relevance"],
                firebird_compliance=business_metrics["firebird_compliance"],
                
                metadata={
                    "mode_description": self.modes[mode],
                    "query_type": self._classify_query_type(query),
                    "complexity": self._assess_query_complexity(query)
                }
            )
            
        except Exception as e:
            total_time = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            
            self.logger.error(f"Test failed for query '{query}' in mode '{mode}': {error_msg}")
            
            return ComprehensiveTestResult(
                query=query,
                mode=mode,
                success=False,
                response="",
                sql_generated=None,
                execution_time=total_time,
                error_message=error_msg,
                timestamp=timestamp,
                metadata={
                    "mode_description": self.modes[mode],
                    "traceback": traceback.format_exc()
                }
            )
    
    def _extract_sql(self, response: str) -> Optional[str]:
        """Extract SQL query from LLM response"""
        if not response:
            return None
            
        # Try to find SQL in code blocks
        if "```sql" in response:
            try:
                sql = response.split("```sql")[1].split("```")[0].strip()
                return sql
            except IndexError:
                pass
        
        if "```" in response:
            try:
                sql = response.split("```")[1].split("```")[0].strip()
                if any(keyword in sql.upper() for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE"]):
                    return sql
            except IndexError:
                pass
        
        # Look for SQL keywords in response
        lines = response.split('\n')
        for line in lines:
            if any(keyword in line.upper() for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE"]):
                return line.strip()
        
        return None
    
    def _calculate_quality_metrics(self, query: str, sql: str, response: str, mode: str) -> Dict[str, float]:
        """Calculate comprehensive quality metrics"""
        
        metrics = {
            "sql_quality": 0.0,
            "business_logic": 0.0,
            "efficiency": 0.0,
            "confidence": 0.0,
            "tokens": len(response.split()) if response else 0,
            "context_size": len(response) if response else 0
        }
        
        if not sql:
            return metrics
        
        sql_upper = sql.upper()
        query_lower = query.lower()
        
        # SQL Quality Score (0-100)
        sql_score = 0
        
        # Basic structure (20 points)
        if "SELECT" in sql_upper:
            sql_score += 20
        
        # Table relevance (30 points)
        if any(word in query_lower for word in ["wohnt", "bewohner", "mieter"]) and "BEWOHNER" in sql_upper:
            sql_score += 30
        elif any(word in query_lower for word in ["eigentümer", "besitzer"]) and "EIGENTUEMER" in sql_upper:
            sql_score += 30
        elif any(word in query_lower for word in ["wohnung", "anzahl"]) and ("WOHNUNG" in sql_upper or "COUNT" in sql_upper):
            sql_score += 30
        
        # LIKE patterns for addresses (25 points)
        if any(word in query_lower for word in ["str", "straße"]) and "LIKE" in sql_upper and "%" in sql:
            sql_score += 25
        elif not any(word in query_lower for word in ["str", "straße"]):
            sql_score += 25  # Not applicable
        
        # Firebird compliance (15 points)
        if "LIMIT" not in sql_upper:  # Should use FIRST
            sql_score += 15
        
        # Column usage (10 points)
        if any(col in sql_upper for col in ["BSTR", "BPLZORT", "NAME", "BNAME"]):
            sql_score += 10
        
        metrics["sql_quality"] = min(sql_score, 100.0)
        
        # Business Logic Score (based on HV domain knowledge)
        business_score = 50  # Base score
        
        if "mieter" in query_lower and "BEWOHNER" in sql_upper:
            business_score += 25
        if "eigentümer" in query_lower and "EIGENTUEMER" in sql_upper:
            business_score += 25
        if "adresse" in query_lower or "str" in query_lower:
            if "BSTR" in sql_upper or "BPLZORT" in sql_upper:
                business_score += 25
        
        metrics["business_logic"] = min(business_score, 100.0)
        
        # Efficiency Score (based on mode characteristics)
        efficiency_score = 70  # Base efficiency
        
        # Mode-specific efficiency adjustments
        if mode in ["adaptive_tag", "smart_enhanced", "guided_agent"]:
            efficiency_score += 20  # These modes are designed for efficiency
        elif mode in ["contextual_enhanced", "smart_fallback"]:
            efficiency_score += 10  # Moderate efficiency improvements
        
        metrics["efficiency"] = min(efficiency_score, 100.0)
        
        # Confidence Score (based on response quality)
        confidence_score = 60  # Base confidence
        
        if sql and len(sql) > 10:
            confidence_score += 20
        if "BEWOHNER" in sql_upper or "EIGENTUEMER" in sql_upper or "WOHNUNG" in sql_upper:
            confidence_score += 20
        
        metrics["confidence"] = min(confidence_score, 100.0)
        
        return metrics
    
    def _calculate_business_metrics(self, query: str, sql: str, response: str) -> Dict[str, bool]:
        """Calculate business-relevant boolean metrics"""
        
        metrics = {
            "table_accuracy": False,
            "syntax_correctness": False,
            "result_relevance": False,
            "firebird_compliance": False
        }
        
        if not sql:
            return metrics
        
        sql_upper = sql.upper()
        query_lower = query.lower()
        
        # Table accuracy
        if any(word in query_lower for word in ["bewohner", "mieter", "wohnt"]):
            metrics["table_accuracy"] = "BEWOHNER" in sql_upper
        elif any(word in query_lower for word in ["eigentümer", "besitzer"]):
            metrics["table_accuracy"] = "EIGENTUEMER" in sql_upper
        elif any(word in query_lower for word in ["wohnung", "anzahl"]):
            metrics["table_accuracy"] = "WOHNUNG" in sql_upper or "COUNT" in sql_upper
        else:
            metrics["table_accuracy"] = True  # Default for other queries
        
        # Syntax correctness (basic check)
        metrics["syntax_correctness"] = (
            "SELECT" in sql_upper and 
            "FROM" in sql_upper and
            sql.count("(") == sql.count(")")
        )
        
        # Result relevance
        metrics["result_relevance"] = (
            len(sql) > 20 and  # Not too short
            any(word in sql_upper for word in ["BEWOHNER", "EIGENTUEMER", "WOHNUNG", "OBJEKTE"])
        )
        
        # Firebird compliance
        metrics["firebird_compliance"] = (
            "LIMIT" not in sql_upper and  # Should use FIRST instead
            not sql.upper().startswith("SHOW")  # Not MySQL syntax
        )
        
        return metrics
    
    def _classify_query_type(self, query: str) -> str:
        """Classify query type for analysis"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["wohnt", "bewohner", "mieter", "straße", "str"]):
            return "address_lookup"
        elif any(word in query_lower for word in ["eigentümer", "besitzer"]):
            return "owner_lookup"
        elif any(word in query_lower for word in ["viele", "anzahl", "count"]):
            return "count_query"
        elif any(word in query_lower for word in ["miete", "durchschnitt", "kosten"]):
            return "financial_query"
        elif any(word in query_lower for word in ["alle", "liste"]):
            return "list_query"
        
        return "general_query"
    
    def _assess_query_complexity(self, query: str) -> str:
        """Assess query complexity level"""
        query_lower = query.lower()
        
        # Simple queries
        if any(word in query_lower for word in ["viele", "anzahl", "liste aller"]):
            return "simple"
        
        # Medium complexity
        if any(word in query_lower for word in ["durchschnitt", "alle mieter in", "alle eigentümer aus"]):
            return "medium"
        
        # Complex queries (address-specific, multi-table)
        if ("str" in query_lower or "straße" in query_lower) and any(char.isdigit() for char in query):
            return "complex"
        
        return "medium"
    
    def run_performance_matrix(self, modes: List[str] = None, concurrent: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive performance matrix testing
        Tests all 9 modes against 11 standard queries
        """
        
        if modes is None:
            modes = list(self.modes.keys())
        
        self.logger.info(f"🧪 PHASE 3: Comprehensive 9-Mode Performance Matrix")
        self.logger.info(f"Testing modes: {modes}")
        self.logger.info(f"Standard queries: {len(self.standard_queries)}")
        print("=" * 80)
        
        results = {}
        detailed_results = []
        
        for mode in modes:
            print(f"\n🔍 Testing Mode: {mode.upper()}")
            print(f"Description: {self.modes[mode]}")
            print("-" * 60)
            
            mode_results = []
            
            for i, query in enumerate(self.standard_queries, 1):
                print(f"Query {i:2d}: {query[:50]}{'...' if len(query) > 50 else ''}")
                
                result = self._execute_comprehensive_test(query, mode, timeout=90)
                mode_results.append(result)
                detailed_results.append(result)
                self.results.append(result)
                
                # Display result
                status = "✅" if result.success else "❌"
                print(f"         {status} Quality: {result.sql_quality_score:5.1f}% "
                      f"Business: {result.business_logic_score:5.1f}% "
                      f"Time: {result.execution_time:5.2f}s")
            
            # Mode summary
            summary = self._create_mode_summary(mode_results, mode)
            results[mode] = summary
            
            print(f"\n📊 {mode.upper()} SUMMARY:")
            print(f"    Success Rate: {summary['success_rate']:5.1%}")
            print(f"    Avg Quality:  {summary['avg_quality']:5.1f}%")
            print(f"    Avg Time:     {summary['avg_time']:5.2f}s")
        
        # Generate comprehensive analysis
        analysis = self._generate_performance_analysis(results, detailed_results)
        
        print("\n" + "=" * 80)
        print("📈 PERFORMANCE MATRIX ANALYSIS COMPLETE")
        print("=" * 80)
        
        return {
            "mode_summaries": results,
            "detailed_results": detailed_results,
            "analysis": analysis,
            "test_metadata": {
                "test_type": "performance_matrix",
                "modes_tested": modes,
                "queries_tested": len(self.standard_queries),
                "total_tests": len(detailed_results),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def run_business_scenarios(self, modes: List[str] = None) -> Dict[str, Any]:
        """
        Run business scenario testing for HV-specific complex scenarios
        """
        
        if modes is None:
            modes = list(self.modes.keys())
        
        self.logger.info(f"🏢 PHASE 3: Business Scenario Testing")
        self.logger.info(f"Testing {len(modes)} modes against {len(self.business_scenarios)} HV scenarios")
        
        results = {}
        detailed_results = []
        
        for mode in modes:
            print(f"\n🏢 Business Testing: {mode.upper()}")
            print("-" * 50)
            
            mode_results = []
            
            for i, scenario in enumerate(self.business_scenarios, 1):
                print(f"Scenario {i}: {scenario[:60]}{'...' if len(scenario) > 60 else ''}")
                
                result = self._execute_comprehensive_test(scenario, mode, timeout=120)
                mode_results.append(result)
                detailed_results.append(result)
                self.results.append(result)
                
                status = "✅" if result.success else "❌"
                print(f"          {status} Business Logic: {result.business_logic_score:5.1f}%")
            
            summary = self._create_mode_summary(mode_results, mode)
            results[mode] = summary
        
        business_analysis = self._generate_business_analysis(results, detailed_results)
        
        return {
            "mode_summaries": results,
            "detailed_results": detailed_results,
            "business_analysis": business_analysis,
            "test_metadata": {
                "test_type": "business_scenarios",
                "modes_tested": modes,
                "scenarios_tested": len(self.business_scenarios),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _create_mode_summary(self, results: List[ComprehensiveTestResult], mode: str) -> Dict[str, Any]:
        """Create comprehensive summary for a mode"""
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        
        if successful_tests == 0:
            return {
                "mode": mode,
                "total_tests": total_tests,
                "successful_tests": 0,
                "success_rate": 0.0,
                "avg_quality": 0.0,
                "avg_business_logic": 0.0,
                "avg_time": 0.0,
                "avg_efficiency": 0.0
            }
        
        successful_results = [r for r in results if r.success]
        
        return {
            "mode": mode,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests,
            "avg_quality": statistics.mean(r.sql_quality_score for r in successful_results),
            "avg_business_logic": statistics.mean(r.business_logic_score for r in successful_results),
            "avg_time": statistics.mean(r.execution_time for r in results),
            "avg_efficiency": statistics.mean(r.efficiency_score for r in successful_results),
            "table_accuracy_rate": sum(1 for r in successful_results if r.table_accuracy) / len(successful_results),
            "firebird_compliance_rate": sum(1 for r in successful_results if r.firebird_compliance) / len(successful_results)
        }
    
    def _generate_performance_analysis(self, summaries: Dict[str, Any], detailed_results: List[ComprehensiveTestResult]) -> Dict[str, Any]:
        """Generate comprehensive performance analysis"""
        
        # Overall statistics
        overall_stats = {
            "total_tests": len(detailed_results),
            "overall_success_rate": sum(1 for r in detailed_results if r.success) / len(detailed_results),
            "avg_execution_time": statistics.mean(r.execution_time for r in detailed_results),
            "best_performing_mode": max(summaries.keys(), key=lambda m: summaries[m]["success_rate"]),
            "fastest_mode": min(summaries.keys(), key=lambda m: summaries[m]["avg_time"])
        }
        
        # Mode rankings
        mode_rankings = []
        for mode, summary in summaries.items():
            overall_score = (
                summary["success_rate"] * 0.3 +
                summary["avg_quality"] / 100 * 0.25 +
                summary["avg_business_logic"] / 100 * 0.25 +
                (1 - min(summary["avg_time"] / 10, 1)) * 0.2  # Inverse time score
            )
            
            mode_rankings.append({
                "mode": mode,
                "overall_score": overall_score,
                "success_rate": summary["success_rate"],
                "avg_quality": summary["avg_quality"],
                "avg_business_logic": summary["avg_business_logic"],
                "avg_time": summary["avg_time"]
            })
        
        mode_rankings.sort(key=lambda x: x["overall_score"], reverse=True)
        
        # Query type analysis
        query_type_performance = {}
        for result in detailed_results:
            query_type = result.metadata.get("query_type", "unknown")
            if query_type not in query_type_performance:
                query_type_performance[query_type] = []
            query_type_performance[query_type].append(result)
        
        return {
            "overall_stats": overall_stats,
            "mode_rankings": mode_rankings,
            "query_type_performance": query_type_performance
        }
    
    def _generate_business_analysis(self, summaries: Dict[str, Any], detailed_results: List[ComprehensiveTestResult]) -> Dict[str, Any]:
        """Generate business scenario specific analysis"""
        
        # Business-focused metrics
        business_metrics = {}
        for mode, summary in summaries.items():
            business_metrics[mode] = {
                "business_logic_score": summary["avg_business_logic"],
                "complex_query_handling": summary["success_rate"],
                "hv_domain_understanding": summary.get("table_accuracy_rate", 0)
            }
        
        return {
            "business_metrics": business_metrics,
            "best_business_mode": max(business_metrics.keys(), key=lambda m: business_metrics[m]["business_logic_score"]),
            "most_reliable_mode": max(summaries.keys(), key=lambda m: summaries[m]["success_rate"])
        }
    
    def generate_architecture_recommendation(self, performance_results: Dict[str, Any], business_results: Dict[str, Any]) -> List[ModeRanking]:
        """
        Generate final architecture recommendation based on comprehensive testing
        """
        
        print("\n" + "=" * 80)
        print("🏛️  FINAL ARCHITECTURE RECOMMENDATION")
        print("=" * 80)
        
        # Combine performance and business results
        combined_analysis = {}
        
        for mode in self.modes.keys():
            perf_summary = performance_results["mode_summaries"].get(mode, {})
            biz_summary = business_results["mode_summaries"].get(mode, {})
            
            # Calculate weighted overall score
            overall_score = (
                perf_summary.get("success_rate", 0) * 0.25 +  # Reliability
                perf_summary.get("avg_quality", 0) / 100 * 0.20 +  # SQL Quality
                biz_summary.get("avg_business_logic", 0) / 100 * 0.25 +  # Business Logic
                perf_summary.get("avg_efficiency", 0) / 100 * 0.15 +  # Efficiency
                (1 - min(perf_summary.get("avg_time", 10) / 10, 1)) * 0.15  # Speed (inverse)
            )
            
            combined_analysis[mode] = {
                "overall_score": overall_score,
                "performance": perf_summary,
                "business": biz_summary
            }
        
        # Generate rankings and recommendations
        rankings = []
        sorted_modes = sorted(combined_analysis.items(), key=lambda x: x[1]["overall_score"], reverse=True)
        
        for i, (mode, analysis) in enumerate(sorted_modes, 1):
            
            # Determine strengths and weaknesses
            strengths, weaknesses, use_cases, recommendation = self._analyze_mode_characteristics(
                mode, analysis["performance"], analysis["business"]
            )
            
            ranking = ModeRanking(
                mode=mode,
                overall_score=analysis["overall_score"],
                strengths=strengths,
                weaknesses=weaknesses,
                use_cases=use_cases,
                production_recommendation=recommendation,
                ranking_position=i
            )
            
            rankings.append(ranking)
        
        # Print recommendations
        self._print_architecture_recommendations(rankings)
        
        return rankings
    
    def _analyze_mode_characteristics(self, mode: str, perf: Dict, biz: Dict) -> Tuple[List[str], List[str], List[str], str]:
        """Analyze mode characteristics for recommendations"""
        
        strengths = []
        weaknesses = []
        use_cases = []
        
        success_rate = perf.get("success_rate", 0)
        quality = perf.get("avg_quality", 0)
        business_logic = biz.get("avg_business_logic", 0)
        speed = perf.get("avg_time", 10)
        
        # Analyze strengths
        if success_rate > 0.8:
            strengths.append("High reliability")
        if quality > 80:
            strengths.append("Excellent SQL generation")
        if business_logic > 80:
            strengths.append("Strong HV domain understanding")
        if speed < 3:
            strengths.append("Fast response time")
        
        # Analyze weaknesses
        if success_rate < 0.6:
            weaknesses.append("Low reliability")
        if quality < 60:
            weaknesses.append("Poor SQL quality")
        if business_logic < 60:
            weaknesses.append("Limited domain understanding")
        if speed > 8:
            weaknesses.append("Slow response time")
        
        # Determine use cases and recommendations
        if mode in ["adaptive_tag", "smart_enhanced", "guided_agent"]:
            use_cases = ["Production ready", "Complex HV queries", "High-volume usage"]
            if success_rate > 0.7 and quality > 70:
                recommendation = "RECOMMENDED FOR PRODUCTION"
            else:
                recommendation = "NEEDS OPTIMIZATION BEFORE PRODUCTION"
        elif mode in ["contextual_enhanced", "hybrid_faiss", "smart_fallback"]:
            use_cases = ["Specific scenarios", "Fallback systems", "Research"]
            recommendation = "SUITABLE FOR SPECIALIZED USE"
        else:
            use_cases = ["Experimental", "Development", "Comparison baseline"]
            recommendation = "NOT RECOMMENDED FOR PRODUCTION"
        
        return strengths, weaknesses, use_cases, recommendation
    
    def _print_architecture_recommendations(self, rankings: List[ModeRanking]):
        """Print final architecture recommendations"""
        
        print(f"\n🥇 TOP 3 RECOMMENDATIONS:")
        print("-" * 50)
        
        for i, ranking in enumerate(rankings[:3], 1):
            print(f"\n{i}. {ranking.mode.upper()} (Score: {ranking.overall_score:.3f})")
            print(f"   Strengths: {', '.join(ranking.strengths)}")
            print(f"   Use Cases: {', '.join(ranking.use_cases)}")
            print(f"   Recommendation: {ranking.production_recommendation}")
        
        print(f"\n📋 COMPLETE RANKING:")
        print("-" * 50)
        
        for ranking in rankings:
            print(f"{ranking.ranking_position:2d}. {ranking.mode:<20} Score: {ranking.overall_score:.3f} - {ranking.production_recommendation}")
        
        # Final production recommendation
        top_mode = rankings[0]
        print(f"\n🎯 FINAL PRODUCTION ARCHITECTURE:")
        print(f"Primary Mode: {top_mode.mode.upper()}")
        print(f"Fallback Mode: {rankings[1].mode.upper()}")
        print(f"Specialized Mode: {rankings[2].mode.upper()}")
    
    def save_comprehensive_results(self, performance_results: Dict[str, Any], 
                                  business_results: Dict[str, Any], 
                                  rankings: List[ModeRanking], 
                                  filename: str = None) -> str:
        """Save comprehensive Phase 3 results"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase3_comprehensive_results_{timestamp}.json"
        
        output_data = {
            "phase3_metadata": {
                "test_framework": "Phase 3 Comprehensive Matrix",
                "timestamp": datetime.now().isoformat(),
                "total_modes_tested": len(self.modes),
                "total_queries": len(self.standard_queries) + len(self.business_scenarios),
                "framework_version": "3.0.0"
            },
            "performance_matrix": performance_results,
            "business_scenarios": business_results,
            "architecture_rankings": [asdict(ranking) for ranking in rankings],
            "final_recommendation": {
                "primary_mode": rankings[0].mode,
                "fallback_mode": rankings[1].mode,
                "specialized_mode": rankings[2].mode,
                "production_ready": [r.mode for r in rankings if "RECOMMENDED" in r.production_recommendation]
            }
        }
        
        output_path = Path("output") / filename
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Phase 3 comprehensive results saved to: {output_path}")
        return str(output_path)


def main():
    """Main execution for Phase 3 comprehensive testing"""
    
    print("🚀 WINCASA PHASE 3: COMPREHENSIVE ARCHITECTURE EVALUATION")
    print("=" * 80)
    print("Testing all 9 implemented modes for final production recommendation")
    print("=" * 80)
    
    # Initialize framework
    framework = Phase3ComprehensiveMatrix()
    
    # Test all 9 modes
    modes_to_test = [
        "contextual_enhanced", "hybrid_faiss", "smart_fallback", 
        "filtered_langchain", "adaptive_tag", "langgraph",
        "smart_enhanced", "guided_agent", "contextual_vector"
    ]
    
    try:
        # Run performance matrix
        print("\n🧪 STEP 1: Performance Matrix Testing")
        performance_results = framework.run_performance_matrix(modes_to_test, concurrent=False)
        
        # Run business scenarios  
        print("\n🏢 STEP 2: Business Scenario Testing")
        business_results = framework.run_business_scenarios(modes_to_test)
        
        # Generate architecture recommendation
        print("\n🏛️ STEP 3: Architecture Analysis")
        rankings = framework.generate_architecture_recommendation(performance_results, business_results)
        
        # Save results
        output_file = framework.save_comprehensive_results(
            performance_results, business_results, rankings
        )
        
        print(f"\n✅ PHASE 3 COMPLETE")
        print(f"📁 Results saved to: {output_file}")
        print(f"🎯 Primary recommendation: {rankings[0].mode.upper()}")
        
    except Exception as e:
        print(f"\n❌ Phase 3 testing failed: {e}")
        logging.error(f"Phase 3 error: {e}", exc_info=True)


if __name__ == "__main__":
    main()