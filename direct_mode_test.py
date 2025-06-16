#!/usr/bin/env python3
"""
Direct test of schema fixes using the handler interfaces
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from wincasa.core.llm_handler import WincasaLLMHandler
from wincasa.core.wincasa_query_engine import WincasaQueryEngine

def test_query(query, mode, model="gpt-4o-mini"):
    """Test a single query"""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"Mode: {mode}, Model: {model}")
    print(f"{'='*60}")
    
    try:
        if mode == "unified":
            engine = WincasaQueryEngine()
            result = engine.process_query(query)
            answer = result.answer
            success = True
        else:
            handler = WincasaLLMHandler()
            os.environ['OPENAI_MODEL'] = model
            result = handler.query_llm(query, mode)
            answer = result.get('answer', 'No answer')
            success = result.get('success', False)
        
        # Check for wrong terms
        wrong_terms = ["OWNERS", "TENANTS", "BEWNAME", "KALTMIETE FROM", "EORT"]
        
        issues = []
        answer_upper = answer.upper()
        
        for wrong in wrong_terms:
            if wrong in answer_upper:
                issues.append(f"Wrong term found: {wrong}")
        
        # Check for wrong field names (not just content)
        if "STRASSE AS" in answer_upper or "FROM STRASSE" in answer_upper or "JOIN STRASSE" in answer_upper:
            issues.append("Wrong table/field name: STRASSE")
        if "STADT AS" in answer_upper or "FROM STADT" in answer_upper or "JOIN STADT" in answer_upper:
            issues.append("Wrong table/field name: STADT")
        
        # Check for correct terms based on query
        if "EIGENTÜMER" in query.upper():
            if "EIGADR" not in answer_upper and "ENAME" not in answer_upper:
                issues.append("Missing EIGADR table or ENAME field")
                
        if "MIETER" in query.upper() or "WOHNT" in query.upper():
            if "BEWOHNER" not in answer_upper and "BNAME" not in answer_upper:
                issues.append("Missing BEWOHNER table or BNAME field")
                
        if "KALTMIETE" in query.upper():
            if "Z1" not in answer_upper:
                issues.append("Missing Z1 field for Kaltmiete")
                
        if "LEERSTAND" in query.upper():
            if "LEFT JOIN" not in answer_upper:
                issues.append("Wrong vacancy detection (should use LEFT JOIN)")
        
        print(f"\nSuccess: {success}")
        
        if issues:
            print("\n❌ ISSUES FOUND:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("\n✅ LOOKS CORRECT!")
        
        print(f"\nAnswer preview:")
        print(answer[:500] + "..." if len(answer) > 500 else answer)
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def main():
    """Run critical tests"""
    
    test_queries = [
        ("Zeige alle Eigentümer", "sql_vanilla"),
        ("Liste aller aktiven Mieter", "sql_standard"),
        ("Summe der Kaltmiete", "sql_vanilla"),
        ("Finde Leerstand", "sql_standard"),
        ("Wer wohnt in der Marienstr. 26", "json_vanilla"),
        ("Eigentümer mit Kontaktdaten", "json_standard"),
        ("Zeige alle Mieter", "unified"),
    ]
    
    passed = 0
    failed = 0
    
    for query, mode in test_queries:
        if test_query(query, mode):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print(f"Success rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")

if __name__ == "__main__":
    main()