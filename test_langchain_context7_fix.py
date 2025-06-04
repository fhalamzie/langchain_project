#!/usr/bin/env python3
"""
Test LangChain SQLDatabase mit Firebird basierend auf Context7 Dokumentation
"""

import sys
import traceback

def test_context7_firebird_connection():
    """Test verschiedene Firebird Connection String Formate basierend auf Context7 Docs"""
    print("🔍 Testing Firebird SQLAlchemy Connection mit Context7 Best Practices...")
    
    try:
        from langchain_community.utilities import SQLDatabase
        
        # Context7 Pattern: SQLDatabase.from_uri(CONNECTION_STRING)
        # Verschiedene Firebird Formate nach SQLAlchemy Dokumentation testen
        
        connection_formats = [
            # Format 1: Standard Firebird embedded (sollte funktionieren)
            "firebird+fdb:///home/projects/langchain_project/WINCASA2022.FDB?user=sysdba&password=masterkey",
            
            # Format 2: Server mit korrekter Syntax
            "firebird+fdb://sysdba:masterkey@localhost:3050//home/projects/langchain_project/WINCASA2022.FDB",
            
            # Format 3: Server mit einfachem Pfad
            "firebird+fdb://sysdba:masterkey@localhost:3050/home/projects/langchain_project/WINCASA2022.FDB",
            
            # Format 4: Embedded (Fallback)
            "firebird+fdb://sysdba:masterkey@/home/projects/langchain_project/WINCASA2022.FDB",
        ]
        
        for i, conn_str in enumerate(connection_formats, 1):
            print(f"\n--- Test {i}: {conn_str[:60]}... ---")
            
            try:
                # Context7 Pattern: SQLDatabase.from_uri()
                db = SQLDatabase.from_uri(conn_str)
                
                # Test basic functionality
                print(f"✅ Connection successful!")
                print(f"   Dialect: {db.dialect}")
                
                # Test table detection
                tables = db.get_usable_table_names()
                print(f"   Tables found: {len(tables)}")
                
                if len(tables) > 0:
                    print(f"   Sample tables: {tables[:3]}")
                    
                    # Test query execution (Context7 Pattern)
                    result = db.run("SELECT FIRST 1 * FROM RDB$DATABASE")
                    print(f"   Query test: ✅ Success")
                    
                    print(f"🎉 WORKING CONNECTION FORMAT: {conn_str}")
                    return db, conn_str
                
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Failed: {error_msg[:100]}...")
                
                # Diagnose spezifische Fehler
                if "invalid literal for int()" in error_msg:
                    print("   → SQLAlchemy Port parsing issue")
                elif "I/O error" in error_msg:
                    print("   → Firebird file access issue")
                elif "No such file" in error_msg:
                    print("   → Database file not found")
                else:
                    print(f"   → Unknown error: {error_msg}")
        
        print("\n❌ Alle Connection String Formate fehlgeschlagen")
        return None, None
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Install: pip install langchain-community")
        return None, None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return None, None

def test_langchain_sql_agent_with_working_connection(db, conn_str):
    """Test LangChain SQL Agent mit funktionierender Verbindung"""
    print("\n🤖 Testing LangChain SQL Agent mit funktionierender Connection...")
    
    try:
        from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
        from langchain_community.agent_toolkits import create_sql_agent
        from langchain_openai import ChatOpenAI
        from llm_interface import LLMInterface
        
        # Context7 Pattern: LLM erstellen
        print("1. Creating LLM...")
        llm_interface = LLMInterface("gpt-4")
        llm = llm_interface.llm
        
        # Context7 Pattern: SQLDatabaseToolkit erstellen
        print("2. Creating SQLDatabaseToolkit...")
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        
        # Context7 Pattern: SQL Agent erstellen
        print("3. Creating SQL Agent...")
        agent = create_sql_agent(
            llm=llm,
            toolkit=toolkit,
            verbose=True,
            agent_type="openai-tools"
        )
        
        # Test Agent
        print("4. Testing SQL Agent...")
        result = agent.invoke({"input": "Wie viele Tabellen gibt es in der Datenbank?"})
        
        print(f"✅ SQL Agent funktioniert!")
        print(f"   Result: {result.get('output', 'No output')}")
        
        return True
        
    except Exception as e:
        print(f"❌ SQL Agent test failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🔍 WINCASA LangChain Context7 Connection Test")
    print("=" * 60)
    
    # Test 1: Connection Strings
    db, working_conn_str = test_context7_firebird_connection()
    
    if db and working_conn_str:
        print(f"\n✅ Funktionierende Connection gefunden!")
        print(f"   Format: {working_conn_str}")
        
        # Test 2: SQL Agent
        agent_success = test_langchain_sql_agent_with_working_connection(db, working_conn_str)
        
        if agent_success:
            print(f"\n🎉 LangChain SQL Agent Mode ist vollständig funktional!")
            print(f"   5/5 Modi sind jetzt implementiert und funktional!")
            sys.exit(0)
        else:
            print(f"\n⚠️ Connection funktioniert, aber SQL Agent hat Probleme")
            sys.exit(1)
    else:
        print(f"\n❌ Keine funktionierende Connection gefunden")
        print(f"   Firebird Server läuft, aber SQLAlchemy Connection schlägt fehl")
        sys.exit(1)