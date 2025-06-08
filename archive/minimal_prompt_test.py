#!/usr/bin/env python3
"""
Minimal prompt test to check LLM SQL rules compliance without retrieval noise.
Tests if LLM can follow basic SQL generation rules with focused prompts.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv('/home/envs/openai.env')

def test_minimal_prompt():
    """Test LLM with minimal, focused system prompt to check SQL generation"""
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Critical SQL generation rules
    system_prompt = """
KRITISCHE REGELN FÜR SQL-GENERIERUNG:
- Tabelle BEWOHNER enthält Bewohner
- Spalte BSTR enthält: "Straßenname Hausnummer" (z.B. "Marienstraße 26")  
- Spalte BPLZORT enthält: "PLZ Ort" (z.B. "45307 Essen")
- IMMER LIKE-Muster für Adressen verwenden, NIE exakte Übereinstimmung
- Beispiel: WHERE BSTR LIKE '%Marienstraße%' AND BPLZORT LIKE '%45307%'

Generiere NUR die SQL-Abfrage, keine Erklärung.
"""
    
    # Test queries
    test_queries = [
        "Wer wohnt in der Marienstr. 26, 45307 Essen",
        "Wer wohnt in der Marienstraße 26",
        "Wer wohnt in der Bäuminghausstr. 41, Essen",
        "Alle Mieter der MARIE26",
        "Liste aller Eigentümer",
        "Wie viele Wohnungen gibt es insgesamt?"
    ]
    
    print("🧪 MINIMAL PROMPT TEST - Checking LLM SQL Rule Compliance")
    print("=" * 80)
    
    results = []
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        
        try:
            # Get SQL from LLM
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Abfrage: {query}"}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            sql = response.choices[0].message.content.strip()
            print(f"Generated SQL: {sql}")
            
            # Check for key patterns
            checks = {
                "uses_LIKE": "LIKE" in sql.upper(),
                "has_wildcard": "%" in sql,
                "uses_BEWOHNER": "BEWOHNER" in sql.upper() if "wohnt" in query.lower() else True,
                "uses_EIGENTUEMER": "EIGENTUEMER" in sql.upper() if "eigentümer" in query.lower() else True,
                "uses_WOHNUNG": "WOHNUNG" in sql.upper() if "wohnung" in query.lower() else True,
                "no_exact_match": "=" not in sql or "LIKE" in sql.upper()
            }
            
            # Evaluate
            passed = all(checks.values())
            status = "✅ PASS" if passed else "❌ FAIL"
            
            print(f"Status: {status}")
            print(f"Checks: {checks}")
            
            results.append({
                "query": query,
                "sql": sql,
                "checks": checks,
                "passed": passed
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "query": query,
                "error": str(e),
                "passed": False
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)
    success_rate = (passed_count / total_count * 100) if total_count > 0 else 0
    
    print(f"Passed: {passed_count}/{total_count} ({success_rate:.1f}%)")
    
    print("\nKey Findings:")
    for result in results:
        if not result.get("passed", False) and "checks" in result:
            print(f"\n❌ Query: {result['query']}")
            for check, value in result["checks"].items():
                if not value:
                    print(f"   - Failed: {check}")
    
    return results


def test_with_overwhelming_context():
    """Test LLM with overwhelming context to see if it still follows rules"""
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Simulate overwhelming context (like 498 YAML files)
    overwhelming_context = """
    YAML Document 1 of 498:
    table_name: ABRPOS
    description: Abrechnungspositionen
    columns:
      - name: ID
        type: INTEGER
        description: Eindeutige ID
      - name: ABRNR
        type: INTEGER
        description: Abrechnungsnummer
    ... (imagine 500+ more lines of technical details)
    
    YAML Document 2 of 498:
    table_name: ADRESSE
    description: Adressen
    columns:
      - name: ID
        type: INTEGER
      - name: STRASSE
        type: VARCHAR(50)
    ... (and so on for 498 documents)
    
    Business Examples:
    - Complex JOIN examples with 10+ tables
    - Detailed financial calculations
    - Historical migration notes
    - Internal conventions
    - Edge cases and exceptions
    """
    
    # Add critical rules at the end (might get lost)
    system_prompt = overwhelming_context + """
    
    CRITICAL: For address queries, ALWAYS use LIKE patterns:
    - BSTR contains "Straßenname Hausnummer"
    - BPLZORT contains "PLZ Ort"
    - Example: WHERE BSTR LIKE '%Marienstraße%'
    """
    
    test_query = "Wer wohnt in der Marienstr. 26, 45307 Essen"
    
    print("\n\n🧪 CONTEXT INTERFERENCE TEST")
    print("=" * 80)
    print(f"Testing with overwhelming context ({len(system_prompt)} characters)")
    print(f"Query: {test_query}")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate SQL for: {test_query}"}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        sql = response.choices[0].message.content.strip()
        print(f"\nGenerated SQL: {sql}")
        
        # Check if it still follows the critical rules
        uses_like = "LIKE" in sql.upper()
        has_wildcard = "%" in sql
        
        if uses_like and has_wildcard:
            print("✅ Still follows LIKE pattern rules despite overwhelming context")
        else:
            print("❌ Lost critical rules in overwhelming context")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    # Test 1: Minimal focused prompt
    test_minimal_prompt()
    
    # Test 2: Context interference
    test_with_overwhelming_context()