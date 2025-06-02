import os
from firebird_sql_agent import FirebirdDocumentedSQLAgent

# Den tatsächlichen Verbindungsstring für die WINCASA-Datenbank verwenden
# Pfad angepasst basierend auf der Projektstruktur
real_connection_string = "firebird+fdb://sysdba:masterkey@localhost//home/projects/langchain_project/WINCASA2022.FDB"

print("Versuche FirebirdDocumentedSQLAgent mit realem Verbindungsstring zu initialisieren...")
try:
    # Instanz mit einem Dummy-LLM erstellen
    agent = FirebirdDocumentedSQLAgent(
        db_connection_string=real_connection_string,
        llm="dummy-model",  # String-Wert wird zu MagicMock
        retrieval_mode="faiss"
    )
    print("✓ Agent wurde erfolgreich initialisiert!")
    
    # Prüfen, ob die SQL-Agent-Komponente erstellt wurde
    if agent.sql_agent:
        print("✓ SQL Agent wurde erfolgreich erstellt")
    else:
        print("✗ SQL Agent konnte nicht erstellt werden")
        
except Exception as e:
    print(f"✗ Agent-Initialisierung fehlgeschlagen: {e}")
    import traceback
    traceback.print_exc()