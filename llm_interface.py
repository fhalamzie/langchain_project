# llm_interface.py
import os
import subprocess
from langchain_openai import ChatOpenAI
from typing import Optional

class LLMInterface:
    def __init__(self):
        # API-Schlüssel aus der .env-Datei abrufen
        def get_api_key_from_env_file(env_file_path="/home/envs/openai.env"):
            """
            Ruft den API-Schlüssel aus einer .env-Datei ab.
            """
            try:
                with open(env_file_path, 'r') as file:
                    for line in file:
                        if line.startswith('OPENAI_API_KEY='):
                            # Extrahiere den Wert nach dem Gleichheitszeichen
                            api_key = line.strip().split('=', 1)[1]
                            return api_key
                raise ValueError(f"OPENAI_API_KEY nicht in der Datei {env_file_path} gefunden")
            except FileNotFoundError:
                raise ValueError(f"Die .env-Datei wurde nicht gefunden: {env_file_path}")
            except Exception as e:
                raise ValueError(f"Unerwarteter Fehler beim Lesen der .env-Datei: {e}")
        
        # API-Schlüssel aus der .env-Datei abrufen
        try:
            openai_api_key = get_api_key_from_env_file()
        except ValueError as e:
            raise ValueError(f"OPENAI_API_KEY konnte nicht aus der .env-Datei abgerufen werden: {e}")
        
        # Initialisiere das LLM
        self.llm = ChatOpenAI(
            model="gpt-4-1106-preview",
            temperature=0,
            openai_api_key=openai_api_key
        )
    
    def generate_sql(self, prompt: str, schema_text: Optional[str] = None) -> str:
        """
        Generiert SQL basierend auf dem Prompt und optionalem Schema-Text.
        
        Args:
            prompt: Die Benutzeranfrage, die in SQL umgewandelt werden soll
            schema_text: Optional. Beschreibung des Datenbankschemas
            
        Returns:
            str: Die generierte SQL-Abfrage
        """
        # Erstelle den vollständigen Prompt mit Schema, falls vorhanden
        messages = []
        
        if schema_text:
            system_message = f"""Du bist ein SQL-Experte. 
            Generiere SQL-Abfragen basierend auf der Benutzeranfrage und dem bereitgestellten Datenbankschema.
            Antworte ausschließlich mit SQL-Code, ohne Erklärungen oder zusätzlichen Text.
            
            Hier ist das Datenbankschema:
            {schema_text}
            """
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        # Generiere SQL mit dem LLM
        response = self.llm.invoke(messages)
        
        # Extrahiere den SQL-Code aus der Antwort
        return response.content.strip()