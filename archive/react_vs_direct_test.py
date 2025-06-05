#!/usr/bin/env python3
"""
Test ReAct vs Direct SQL generation
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_react_vs_direct():
    """Compare ReAct agent approach vs direct SQL generation"""

    from llm_interface import LLMInterface

    print("🧪 REACT VS DIRECT SQL GENERATION TEST")
    print("=" * 60)

    llm_interface = LLMInterface("gpt-4o-mini")
    llm = llm_interface.llm

    # Test 1: ReAct format (current system)
    react_prompt = """Du bist ein Experte für das WINCASA Property Management Firebird SQL-Datenbanksystem.

Du hast Zugriff auf folgende Tools:
1. fdb_query: Führt SQL-SELECT-Abfragen direkt auf der Firebird-Datenbank aus
2. fdb_schema: Gibt Schema-Informationen für Tabellen zurück

WICHTIGE ADRESSABFRAGE-HINWEISE für BEWOHNER-Tabelle:
- BSTR-Spalte enthält: "Straßenname Hausnummer" (z.B. "Marienstraße 26")
- BPLZORT-Spalte enthält: "PLZ Ort" (z.B. "45307 Essen")
- VERWENDE NIEMALS EXACT MATCH für Adressen! Verwende IMMER LIKE-Muster!
- Korrekte Syntax: WHERE BSTR LIKE 'Marienstraße%' AND BPLZORT LIKE '%45307%'

Vorgehen:
1. Analysiere die Anfrage und identifiziere relevante Geschäftsentitäten
2. Erstelle eine syntaktisch korrekte Firebird SQL-Abfrage
3. Führe die Abfrage aus und analysiere die Ergebnisse

Antworte im ReAct-Format (Thought/Action/Action Input/Observation).

Frage: Wer wohnt in der Marienstr. 26, 45307 Essen"""

    print("📝 Testing ReAct format (current system approach)...")

    response_react = llm.invoke(react_prompt)
    react_result = response_react.content.strip()

    print("🤖 LLM Response (ReAct):")
    print(react_result[:500] + "..." if len(react_result) > 500 else react_result)
    print()

    # Test 2: Direct SQL format (our working approach)
    direct_prompt = """Du bist ein Experte für das WINCASA Property Management Firebird SQL-Datenbanksystem.

WICHTIGE ADRESSABFRAGE-HINWEISE für BEWOHNER-Tabelle:
- BSTR-Spalte enthält: "Straßenname Hausnummer" (z.B. "Marienstraße 26")
- BPLZORT-Spalte enthält: "PLZ Ort" (z.B. "45307 Essen")
- VERWENDE NIEMALS EXACT MATCH für Adressen! Verwende IMMER LIKE-Muster!
- Korrekte Syntax: WHERE BSTR LIKE 'Marienstraße%' AND BPLZORT LIKE '%45307%'

Frage: Wer wohnt in der Marienstr. 26, 45307 Essen
Generiere NUR die SQL-Abfrage. Keine Erklärung, kein ReAct, nur SQL."""

    print("📝 Testing direct SQL format...")

    response_direct = llm.invoke(direct_prompt)
    direct_result = response_direct.content.strip()

    print("🤖 LLM Response (Direct):")
    print(direct_result)
    print()

    print("=" * 60)
    print("🎯 COMPARISON:")
    print(f"   ReAct length: {len(react_result)} chars")
    print(f"   Direct length: {len(direct_result)} chars")

    # Check if ReAct includes SQL
    if "SELECT" in react_result.upper():
        print("   ✅ ReAct includes SQL")
    else:
        print("   ❌ ReAct missing SQL")

    if "SELECT" in direct_result.upper():
        print("   ✅ Direct includes SQL")
    else:
        print("   ❌ Direct missing SQL")


if __name__ == "__main__":
    test_react_vs_direct()
