import os
from firebird_sql_agent import FirebirdDocumentedSQLAgent

# Für den Test eine minimale Firebird-Connection-String verwenden
# Dieser muss nicht tatsächlich verbinden, sondern nur die Engine-Erstellung testen
test_connection_string = "firebird+fdb://sysdba:masterkey@localhost/test.fdb"

print("Versuche FirebirdDocumentedSQLAgent zu initialisieren...")
try:
    # Instanz mit einem Dummy-LLM erstellen
    agent = FirebirdDocumentedSQLAgent(
        db_connection_string=test_connection_string,
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