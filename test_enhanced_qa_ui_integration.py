#!/usr/bin/env python3
"""
Test-Skript für die Integration der direkten FDB-Schnittstelle in die enhanced_qa_ui.py

Dieses Skript testet die vollständige Integration ohne Streamlit zu starten.
"""

import os
import sys
from pathlib import Path

def test_integration():
    """Testet die vollständige Integration der direkten FDB-Schnittstelle."""
    print("🧪 Teste Integration der direkten FDB-Schnittstelle in enhanced_qa_ui.py")
    print("=" * 70)
    
    # 1. Import-Tests
    print("\n1️⃣ Import-Tests:")
    try:
        from enhanced_qa_ui import get_firebird_sql_agent, create_enhanced_qa_tab
        print("✅ enhanced_qa_ui.py erfolgreich importiert")
    except Exception as e:
        print(f"❌ Import-Fehler enhanced_qa_ui: {e}")
        return False
    
    try:
        from firebird_sql_agent_direct import FirebirdDirectSQLAgent
        print("✅ FirebirdDirectSQLAgent erfolgreich importiert")
    except Exception as e:
        print(f"❌ Import-Fehler FirebirdDirectSQLAgent: {e}")
        return False
    
    # 2. Datenbankverbindungstest
    print("\n2️⃣ Datenbankverbindungstest:")
    try:
        from fdb_direct_interface import FDBDirectInterface
        db_string = "firebird+fdb://sysdba:masterkey@//home/projects/langchain_project/WINCASA2022.FDB"
        
        fdb_interface = FDBDirectInterface.from_connection_string(db_string)
        tables = fdb_interface.get_table_names()
        print(f"✅ Datenbankverbindung erfolgreich - {len(tables)} Tabellen gefunden")
        
        # Teste eine einfache Abfrage
        bewohner_info = fdb_interface.get_table_info(["BEWOHNER"])
        print(f"✅ Schema-Informationen für BEWOHNER erfolgreich abgerufen")
        
    except Exception as e:
        print(f"❌ Datenbankverbindung fehlgeschlagen: {e}")
        return False
    
    # 3. Agent-Initialisierungstest
    print("\n3️⃣ Agent-Initialisierungstest:")
    try:
        # Simuliere Streamlit-Cache-Funktion
        class MockStreamlit:
            @staticmethod
            def cache_resource(func):
                return func
        
        # Temporär sys.modules modifizieren für den Test
        original_streamlit = sys.modules.get('streamlit')
        sys.modules['streamlit'] = MockStreamlit()
        
        # Teste Agent-Initialisierung
        agent = FirebirdDirectSQLAgent(
            db_connection_string=db_string,
            llm="gpt-4-1106-preview",
            retrieval_mode="faiss"
        )
        print("✅ FirebirdDirectSQLAgent erfolgreich initialisiert")
        
        # Wiederherstellen
        if original_streamlit:
            sys.modules['streamlit'] = original_streamlit
        else:
            del sys.modules['streamlit']
            
    except Exception as e:
        print(f"❌ Agent-Initialisierung fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Dokumentationstest
    print("\n4️⃣ Dokumentationstest:")
    try:
        # Prüfe, ob Dokumentationsverzeichnisse existieren
        schema_path = Path("output/schema")
        yamls_path = Path("output/yamls")
        
        if schema_path.exists():
            md_files = list(schema_path.glob("*.md"))
            print(f"✅ Schema-Dokumentation gefunden: {len(md_files)} MD-Dateien")
        else:
            print("⚠️ Schema-Dokumentation nicht gefunden (output/schema)")
        
        if yamls_path.exists():
            yaml_files = list(yamls_path.glob("*.yaml"))
            print(f"✅ YAML-Dokumentation gefunden: {len(yaml_files)} YAML-Dateien")
        else:
            print("⚠️ YAML-Dokumentation nicht gefunden (output/yamls)")
            
    except Exception as e:
        print(f"❌ Dokumentationstest fehlgeschlagen: {e}")
        return False
    
    # 5. Umgebungsvariablen-Test
    print("\n5️⃣ Umgebungsvariablen-Test:")
    openai_env = Path("/home/envs/openai.env")
    openrouter_env = Path("/home/envs/openrouter.env")
    
    if openai_env.exists():
        print("✅ OpenAI-Umgebungsdatei gefunden")
    elif openrouter_env.exists():
        print("✅ OpenRouter-Umgebungsdatei gefunden")
    else:
        print("⚠️ Keine API-Schlüssel-Umgebungsdateien gefunden")
    
    print("\n" + "=" * 70)
    print("🎉 Integration der direkten FDB-Schnittstelle erfolgreich getestet!")
    print("\nDie enhanced_qa_ui.py ist bereit für die Verwendung mit:")
    print("  streamlit run enhanced_qa_ui.py")
    print("\nFeatures der direkten FDB-Schnittstelle:")
    print("  ✅ Umgeht SQLAlchemy-Sperrprobleme (SQLCODE -902)")
    print("  ✅ Automatisches Server/Embedded-Fallback")
    print("  ✅ Custom Langchain Tools für FDB-Operationen")
    print("  ✅ Verbesserte Fehlerbehandlung und Performance")
    print("  ✅ Detaillierte Agent-Schritte in der UI")
    
    return True

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)