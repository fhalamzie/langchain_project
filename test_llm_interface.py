import sys
from llm_interface import LLMInterface

print("=== TEST: PASS INTEGRATION IN LLM_INTERFACE.PY ===")

try:
    print("Versuche, eine LLMInterface-Instanz zu erstellen...")
    llm_interface = LLMInterface()
    print("LLMInterface-Instanz erfolgreich erstellt!")
    print("API-Schlüssel wurde korrekt aus dem Password-Manager abgerufen.")
    
    # Optional: Ein einfacher Test der LLM-Funktionalität
    print("\nFühre einen einfachen Test der LLM-Funktionalität durch...")
    test_query = "Was ist 2+2? Antworte mit nur einer Zahl."
    response = llm_interface.generate_sql(test_query)
    print(f"Antwort vom LLM: {response}")
    
    print("\nTest erfolgreich abgeschlossen!")
except Exception as e:
    print(f"Fehler: {e}")
    sys.exit(1)