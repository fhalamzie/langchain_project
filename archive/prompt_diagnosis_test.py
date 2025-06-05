#!/usr/bin/env python3
"""
Minimal prompt test to diagnose why LLM ignores system prompts
CRITICAL: Test LLM with ONLY system prompt + query (no retrieval noise)
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_minimal_prompt_compliance():
    """Test if LLM follows system prompts without context interference"""

    try:
        from llm_interface import LLMInterface

        print("🔬 MINIMAL PROMPT COMPLIANCE TEST")
        print("=" * 60)
        print(
            "Goal: Test if LLM follows system prompts WITHOUT retrieval context noise"
        )
        print("Issue: 80%+ wrong SQL generation - is LLM ignoring system instructions?")
        print()

        # Initialize LLM
        llm_interface = LLMInterface("gpt-4o-mini")
        llm = llm_interface.llm

        # Minimal system prompt with CRITICAL rules
        system_prompt = """
CRITICAL RULES FOR SQL GENERATION:
- Table BEWOHNER contains residents
- Column BSTR contains: "Straßenname Hausnummer" (e.g. "Marienstraße 26")  
- Column BPLZORT contains: "PLZ Ort" (e.g. "45307 Essen")
- ALWAYS use LIKE patterns for addresses, NEVER exact match
- Example: WHERE BSTR LIKE '%Marienstraße%' AND BPLZORT LIKE '%45307%'

You MUST follow these rules exactly. Generate ONLY the SQL query.
"""

        # Test query
        test_query = "Wer wohnt in der Marienstr. 26, 45307 Essen"

        print(f"🎯 System Prompt (NO RETRIEVAL CONTEXT):")
        print(system_prompt)
        print(f"📝 Query: {test_query}")
        print()

        # Test 1: Minimal prompt only
        print("TEST 1: System Prompt + Query Only (No Context)")
        print("-" * 50)

        from langchain.schema import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=test_query),
        ]

        response = llm.invoke(messages)
        sql_result = response.content.strip()

        print(f"Generated SQL: {sql_result}")
        print()

        # Analyze compliance
        analysis = analyze_sql_compliance(sql_result, test_query)
        print("📊 COMPLIANCE ANALYSIS:")
        for key, value in analysis.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}")
        print()

        # Test 2: With overwhelming context (simulating current problem)
        print("TEST 2: System Prompt + Query + Overwhelming Context")
        print("-" * 50)

        # Simulate overwhelming context like current system
        overwhelming_context = """
CONTEXT (498 YAML documents):
Table definitions, relationships, business rules, examples...
[This simulates the 498 YAML documents that might be overwhelming the LLM]
Table OBJEKTE: Properties and buildings
Table WOHNUNG: Individual apartments  
Table MIETER: Tenants (old structure)
Table VERTRAEGE: Contracts
... hundreds more lines of context ...
"""

        messages_with_context = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"{overwhelming_context}\n\nQuery: {test_query}"),
        ]

        response_with_context = llm.invoke(messages_with_context)
        sql_result_with_context = response_with_context.content.strip()

        print(f"Generated SQL: {sql_result_with_context}")
        print()

        # Analyze compliance with context
        analysis_with_context = analyze_sql_compliance(
            sql_result_with_context, test_query
        )
        print("📊 COMPLIANCE ANALYSIS (WITH CONTEXT):")
        for key, value in analysis_with_context.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}")
        print()

        # Summary
        print("🎯 DIAGNOSIS SUMMARY:")
        print("-" * 50)

        simple_compliance = sum(analysis.values()) / len(analysis)
        context_compliance = sum(analysis_with_context.values()) / len(
            analysis_with_context
        )

        print(f"Simple Prompt Compliance: {simple_compliance:.1%}")
        print(f"With Context Compliance: {context_compliance:.1%}")

        if simple_compliance > context_compliance:
            print(
                "❌ CONTEXT INTERFERENCE CONFIRMED: LLM follows rules better without context"
            )
            print(
                "   Solution: Implement TAG model with focused, query-specific context"
            )
        elif simple_compliance < 0.8:
            print(
                "❌ FUNDAMENTAL PROMPT ISSUE: LLM doesn't follow basic rules even without context"
            )
            print("   Solution: Improve system prompt structure and rule clarity")
        else:
            print(
                "✅ SYSTEM PROMPT WORKING: Issue is context delivery, not prompt structure"
            )

        return {
            "simple_sql": sql_result,
            "context_sql": sql_result_with_context,
            "simple_compliance": simple_compliance,
            "context_compliance": context_compliance,
        }

    except Exception as e:
        print(f"❌ Error in minimal prompt test: {e}")
        import traceback

        traceback.print_exc()
        return None


def analyze_sql_compliance(sql: str, query: str) -> dict:
    """Analyze if SQL follows critical rules"""

    sql_upper = sql.upper()

    return {
        "uses_bewohner_table": "BEWOHNER" in sql_upper,
        "uses_like_pattern": "LIKE" in sql_upper and "%" in sql,
        "targets_bstr_column": "BSTR" in sql_upper,
        "targets_bplzort_column": "BPLZORT" in sql_upper,
        "includes_marienstr": "MARIEN" in sql_upper,
        "includes_postal_code": "45307" in sql,
        "avoids_exact_match": not ("=" in sql and "Marienstr" in sql),
        "is_valid_sql_structure": sql.strip().upper().startswith("SELECT"),
    }


if __name__ == "__main__":
    test_minimal_prompt_compliance()
