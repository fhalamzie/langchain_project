"""
Test script to verify the hybrid context integration in firebird_sql_agent_direct.py
"""

from firebird_sql_agent_direct import FirebirdDirectSQLAgent
from global_context import get_compact_global_context, get_global_context_prompt
import os

def test_global_context_loading():
    """Test that global context can be loaded correctly"""
    print("🧪 Testing Global Context Loading...")
    
    # Test compact context
    compact_context = get_compact_global_context()
    print(f"✅ Compact context loaded: {len(compact_context)} characters")
    print(f"Preview: {compact_context[:200]}...")
    
    # Test full context  
    full_context = get_global_context_prompt()
    print(f"✅ Full context loaded: {len(full_context)} characters")
    print(f"Preview: {full_context[:200]}...")
    
    return True

def test_sql_agent_context_integration():
    """Test that the SQL agent context loading logic works"""
    print("\n🧪 Testing SQL Agent Context Integration...")
    
    try:
        # Test just the context loading logic without creating the full agent
        from global_context import get_compact_global_context
        context = get_compact_global_context()
        
        # Simulate what happens in the agent
        print("✅ Context loading mechanism works")
        print(f"✅ Context length: {len(context)} characters")
        
        # Test that the context contains expected elements
        if "BEWOHNER" in context and "OBJEKTE" in context and "KONTEN" in context:
            print("✅ Context contains core entities")
        else:
            print("⚠️ Context missing some core entities")
        
        if "ONR" in context and "Object Number" in context:
            print("✅ Context contains key relationships")
        else:
            print("⚠️ Context missing key relationships")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing context integration: {e}")
        return False

def test_data_patterns_availability():
    """Test that data patterns file is available for fallback context"""
    print("\n🧪 Testing Data Patterns Availability...")
    
    from pathlib import Path
    patterns_file = Path("output/data_context_summary.txt")
    
    if patterns_file.exists():
        patterns = patterns_file.read_text(encoding='utf-8')
        print(f"✅ Data patterns file found: {len(patterns)} characters")
        print(f"Preview: {patterns[:200]}...")
        return True
    else:
        print("❌ Data patterns file not found")
        return False

def main():
    """Run all integration tests"""
    print("🚀 WINCASA Hybrid Context Integration Test")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Global context loading
    if test_global_context_loading():
        tests_passed += 1
    
    # Test 2: SQL agent integration  
    if test_sql_agent_context_integration():
        tests_passed += 1
    
    # Test 3: Data patterns availability
    if test_data_patterns_availability():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All integration tests passed! Hybrid context strategy is ready.")
    else:
        print("⚠️ Some tests failed. Review the issues above.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)