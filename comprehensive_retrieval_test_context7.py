#!/usr/bin/env python3
"""
Comprehensive Retrieval Test with Context7 Integration

This script tests all 4 retrieval modes with Context7 enhancements:
1. Enhanced Mode (Multi-stage RAG)
2. FAISS Mode (Vector similarity) 
3. None Mode (Direct generation with fallback)
4. LangChain Mode (SQL Database Agent)
5. LangChain Mode (SQL Database Agent with Context7)

Features:
- Context7 best practices integration
- Phoenix monitoring support
- Parallel testing capability
- Detailed performance metrics
- Real-world WINCASA queries
"""

import os
import sys
import json
import time
import asyncio
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import WINCASA system components
try:
    from firebird_sql_agent_direct import FirebirdDirectSQLAgent
    from llm_interface import LLMInterface
    from phoenix_monitoring import get_monitor
    from langchain_context7_integration import LangChainContext7Integration
    from langchain_sql_retriever_fixed import LangChainSQLRetriever
    
    SYSTEM_AVAILABLE = True
    logger.info("✅ All WINCASA system components imported successfully")
except ImportError as e:
    SYSTEM_AVAILABLE = False
    logger.error(f"❌ System import failed: {e}")


class ComprehensiveRetrievalTester:
    """
    Comprehensive testing framework for all retrieval modes with Context7 integration.
    """
    
    def __init__(self, model_name: str = "gpt-4", enable_monitoring: bool = True):
        """
        Initialize the comprehensive testing framework.
        
        Args:
            model_name: LLM model to use for testing
            enable_monitoring: Whether to enable Phoenix monitoring
        """
        self.model_name = model_name
        self.enable_monitoring = enable_monitoring
        self.db_connection = "firebird+fdb://sysdba:masterkey@localhost/WINCASA2022.FDB"
        
        # Test configurations
        self.test_queries = [
            {
                "id": "basic_count",
                "query": "Wie viele Wohnungen gibt es insgesamt?",
                "category": "basic",
                "expected_pattern": "517"
            },
            {
                "id": "resident_lookup", 
                "query": "Zeige die ersten 3 Bewohner mit ihren Namen",
                "category": "basic",
                "expected_pattern": "FIRST 3"
            },
            {
                "id": "owner_properties",
                "query": "Welche Eigentümer besitzen mehr als eine Wohnung?",
                "category": "complex",
                "expected_pattern": "COUNT"
            },
            {
                "id": "address_search",
                "query": "Wer wohnt in der Marienstraße?",
                "category": "business",
                "expected_pattern": "Marienstraße"
            },
            {
                "id": "financial_query",
                "query": "Zeige Konten mit Buchungen der letzten Zeit",
                "category": "complex",
                "expected_pattern": "JOIN"
            }
        ]
        
        # Initialize system components
        self.llm_interface = None
        self.monitor = None
        self.agents = {}
        self.test_results = {}
        
        if SYSTEM_AVAILABLE:
            self._initialize_system()
    
    def _initialize_system(self):
        """Initialize all system components"""
        try:
            logger.info("🚀 Initializing comprehensive test system...")
            
            # Initialize LLM
            self.llm_interface = LLMInterface(self.model_name)
            logger.info(f"✅ LLM interface initialized: {self.model_name}")
            
            # Initialize monitoring
            if self.enable_monitoring:
                try:
                    self.monitor = get_monitor(enable_ui=True)
                    logger.info("✅ Phoenix monitoring enabled")
                except Exception as e:
                    logger.warning(f"⚠️ Phoenix monitoring failed: {e}")
                    self.monitor = None
            
            # Initialize all retrieval modes
            self._initialize_retrieval_agents()
            
            logger.info("✅ Comprehensive test system initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            raise
    
    def _initialize_retrieval_agents(self):
        """Initialize all 4 retrieval mode agents"""
        try:
            logger.info("🤖 Initializing all retrieval mode agents...")
            
            # 1. Enhanced Mode Agent
            try:
                self.agents['enhanced'] = FirebirdDirectSQLAgent(
                    db_connection_string=self.db_connection,
                    llm=self.llm_interface.llm,
                    retrieval_mode="enhanced",
                    use_enhanced_knowledge=True,
                    enable_monitoring=self.enable_monitoring
                )
                logger.info("✅ Enhanced mode agent initialized")
            except Exception as e:
                logger.error(f"❌ Enhanced mode failed: {e}")
                self.agents['enhanced'] = None
            
            # 2. FAISS Mode Agent  
            try:
                self.agents['faiss'] = FirebirdDirectSQLAgent(
                    db_connection_string=self.db_connection,
                    llm=self.llm_interface.llm,
                    retrieval_mode="faiss",
                    use_enhanced_knowledge=True,
                    enable_monitoring=self.enable_monitoring
                )
                logger.info("✅ FAISS mode agent initialized")
            except Exception as e:
                logger.error(f"❌ FAISS mode failed: {e}")
                self.agents['faiss'] = None
            
            # 3. None Mode Agent
            try:
                self.agents['none'] = FirebirdDirectSQLAgent(
                    db_connection_string=self.db_connection,
                    llm=self.llm_interface.llm,
                    retrieval_mode="none",
                    use_enhanced_knowledge=True,
                    enable_monitoring=self.enable_monitoring
                )
                logger.info("✅ None mode agent initialized")
            except Exception as e:
                logger.error(f"❌ None mode failed: {e}")
                self.agents['none'] = None
            
            # SQLCoder mode removed - using cloud APIs only
            
            # 5. LangChain Context7 Integration
            try:
                self.agents['langchain_context7'] = LangChainContext7Integration(
                    db_connection_string=self.db_connection,
                    llm=self.llm_interface.llm,
                    enable_monitoring=self.enable_monitoring
                )
                logger.info("✅ LangChain Context7 integration initialized")
            except Exception as e:
                logger.error(f"❌ LangChain Context7 failed: {e}")
                self.agents['langchain_context7'] = None
            
            # 6. Standard LangChain SQL Agent
            try:
                self.agents['langchain'] = LangChainSQLRetriever(
                    db_connection_string=self.db_connection,
                    llm=self.llm_interface.llm,
                    enable_monitoring=self.enable_monitoring
                )
                logger.info("✅ Standard LangChain SQL agent initialized")
            except Exception as e:
                logger.error(f"❌ Standard LangChain failed: {e}")
                self.agents['langchain'] = None
            
            # Count successful initializations
            successful_agents = [k for k, v in self.agents.items() if v is not None]
            logger.info(f"✅ Successfully initialized {len(successful_agents)}/6 retrieval agents")
            logger.info(f"Available agents: {', '.join(successful_agents)}")
            
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {e}")
            raise
    
    def test_single_mode(self, mode: str, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a single retrieval mode with a single query.
        
        Args:
            mode: Retrieval mode name
            query_data: Query information
            
        Returns:
            Test result dictionary
        """
        start_time = time.time()
        agent = self.agents.get(mode)
        
        result = {
            "mode": mode,
            "query_id": query_data["id"],
            "query": query_data["query"],
            "category": query_data["category"],
            "success": False,
            "execution_time": 0,
            "error": None,
            "response": None,
            "sql_generated": None,
            "context_docs": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        if not agent:
            result["error"] = f"Agent not available for mode: {mode}"
            result["execution_time"] = time.time() - start_time
            return result
        
        try:
            logger.info(f"🔍 Testing {mode} mode with query: {query_data['query']}")
            
            # Execute query based on agent type
            if mode == "langchain_context7":
                # Use Context7 integration
                response = agent.query_with_context7_enhancement(query_data["query"])
                result["response"] = response.get("result", "No response")
                result["sql_generated"] = "Context7 enhanced processing"
                result["success"] = response.get("success", False)
                result["execution_time"] = response.get("execution_time", time.time() - start_time)
                
            elif mode in ["langchain"]:
                # Use LangChain SQL retriever
                docs = agent.retrieve_documents(query_data["query"], max_docs=5)
                result["context_docs"] = len(docs)
                result["response"] = docs[0].page_content if docs else "No response"
                result["success"] = len(docs) > 0 and "error" not in docs[0].metadata.get("source", "")
                result["execution_time"] = time.time() - start_time
                
            else:
                # Use standard Firebird agents (enhanced, faiss, none)
                response = agent.query(query_data["query"])
                result["response"] = response.get("answer", "No answer")
                result["sql_generated"] = response.get("sql_query", "No SQL")
                result["success"] = response.get("success", False)
                result["execution_time"] = response.get("execution_time", time.time() - start_time)
            
            if result["success"]:
                logger.info(f"✅ {mode} mode succeeded in {result['execution_time']:.2f}s")
            else:
                logger.warning(f"⚠️ {mode} mode completed with issues in {result['execution_time']:.2f}s")
                
        except Exception as e:
            result["error"] = str(e)
            result["execution_time"] = time.time() - start_time
            logger.error(f"❌ {mode} mode failed: {e}")
        
        return result
    
    def run_comprehensive_test(self, concurrent: bool = True, max_workers: int = 3) -> Dict[str, Any]:
        """
        Run comprehensive test across all modes and queries.
        
        Args:
            concurrent: Whether to run tests concurrently
            max_workers: Maximum number of concurrent workers
            
        Returns:
            Comprehensive test results
        """
        logger.info("🧪 Starting comprehensive retrieval test with Context7 integration")
        logger.info(f"📊 Testing {len(self.test_queries)} queries across {len([k for k, v in self.agents.items() if v])} modes")
        
        start_time = time.time()
        all_results = []
        
        try:
            if concurrent and max_workers > 1:
                # Run tests concurrently
                logger.info(f"🚀 Running concurrent tests with {max_workers} workers")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all test combinations
                    futures = []
                    for mode, agent in self.agents.items():
                        if agent is not None:
                            for query_data in self.test_queries:
                                future = executor.submit(self.test_single_mode, mode, query_data)
                                futures.append(future)
                    
                    # Collect results
                    for future in as_completed(futures):
                        try:
                            result = future.result(timeout=60)  # 60 second timeout per test
                            all_results.append(result)
                        except Exception as e:
                            logger.error(f"❌ Test future failed: {e}")
            
            else:
                # Run tests sequentially
                logger.info("🔄 Running sequential tests")
                
                for mode, agent in self.agents.items():
                    if agent is not None:
                        for query_data in self.test_queries:
                            result = self.test_single_mode(mode, query_data)
                            all_results.append(result)
            
            total_time = time.time() - start_time
            
            # Analyze results
            analysis = self._analyze_results(all_results, total_time)
            
            # Save results
            self._save_results(analysis)
            
            logger.info(f"✅ Comprehensive test completed in {total_time:.2f}s")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Comprehensive test failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e), "results": all_results}
    
    def _analyze_results(self, results: List[Dict], total_time: float) -> Dict[str, Any]:
        """Analyze test results and generate summary"""
        
        # Group by mode
        by_mode = {}
        for result in results:
            mode = result["mode"]
            if mode not in by_mode:
                by_mode[mode] = []
            by_mode[mode].append(result)
        
        # Calculate metrics per mode
        mode_metrics = {}
        for mode, mode_results in by_mode.items():
            successful = [r for r in mode_results if r["success"]]
            failed = [r for r in mode_results if not r["success"]]
            
            mode_metrics[mode] = {
                "total_queries": len(mode_results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / len(mode_results) if mode_results else 0,
                "avg_execution_time": sum(r["execution_time"] for r in mode_results) / len(mode_results) if mode_results else 0,
                "min_execution_time": min(r["execution_time"] for r in mode_results) if mode_results else 0,
                "max_execution_time": max(r["execution_time"] for r in mode_results) if mode_results else 0,
                "errors": [r["error"] for r in failed if r["error"]]
            }
        
        # Overall metrics
        total_tests = len(results)
        successful_tests = len([r for r in results if r["success"]])
        
        analysis = {
            "test_summary": {
                "total_time": total_time,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "overall_success_rate": successful_tests / total_tests if total_tests else 0,
                "modes_tested": list(mode_metrics.keys()),
                "queries_tested": len(self.test_queries)
            },
            "mode_metrics": mode_metrics,
            "detailed_results": results,
            "timestamp": datetime.now().isoformat(),
            "model_used": self.model_name,
            "context7_integration": True
        }
        
        return analysis
    
    def _save_results(self, analysis: Dict[str, Any]):
        """Save test results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_test_context7_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📁 Results saved to: {filename}")
            
            # Also create a summary file
            summary_filename = f"test_summary_context7_{timestamp}.txt"
            with open(summary_filename, 'w', encoding='utf-8') as f:
                f.write("WINCASA Comprehensive Retrieval Test Results (Context7 Enhanced)\n")
                f.write("=" * 80 + "\n\n")
                
                summary = analysis["test_summary"]
                f.write(f"Total Time: {summary['total_time']:.2f}s\n")
                f.write(f"Total Tests: {summary['total_tests']}\n")
                f.write(f"Successful: {summary['successful_tests']}\n")
                f.write(f"Failed: {summary['failed_tests']}\n")
                f.write(f"Success Rate: {summary['overall_success_rate']*100:.1f}%\n\n")
                
                f.write("Mode Performance:\n")
                f.write("-" * 40 + "\n")
                for mode, metrics in analysis["mode_metrics"].items():
                    f.write(f"{mode}: {metrics['success_rate']*100:.1f}% ({metrics['successful']}/{metrics['total_queries']}) - Avg: {metrics['avg_execution_time']:.2f}s\n")
            
            logger.info(f"📄 Summary saved to: {summary_filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")


def main():
    """Main test execution function"""
    print("🧪 WINCASA Comprehensive Retrieval Test with Context7 Integration")
    print("=" * 80)
    
    if not SYSTEM_AVAILABLE:
        print("❌ System components not available. Cannot run tests.")
        return
    
    try:
        # Initialize tester
        tester = ComprehensiveRetrievalTester(
            model_name="gpt-4",
            enable_monitoring=True
        )
        
        # Run comprehensive test
        results = tester.run_comprehensive_test(
            concurrent=True,
            max_workers=3
        )
        
        # Print summary
        if "test_summary" in results:
            summary = results["test_summary"]
            print(f"\n📊 Test Summary:")
            print(f"Total Time: {summary['total_time']:.2f}s")
            print(f"Success Rate: {summary['overall_success_rate']*100:.1f}%")
            print(f"Modes Tested: {', '.join(summary['modes_tested'])}")
            
            print(f"\n🏆 Mode Performance:")
            for mode, metrics in results["mode_metrics"].items():
                status = "✅" if metrics["success_rate"] > 0.8 else "⚠️" if metrics["success_rate"] > 0.5 else "❌"
                print(f"{status} {mode}: {metrics['success_rate']*100:.1f}% - Avg: {metrics['avg_execution_time']:.2f}s")
        
        print(f"\n✅ Comprehensive test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    main()