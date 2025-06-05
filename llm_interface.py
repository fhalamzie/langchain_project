# llm_interface.py
import os
from typing import Optional

from langchain_openai import ChatOpenAI


class LLMInterface:
    def __init__(self, model_name: str = "openai/gpt-4.1-nano"):
        # API-Schlüssel aus der .env-Datei abrufen
        def get_api_key_from_env_file(env_file_path="/home/envs/openai.env"):
            """
            Ruft den API-Schlüssel aus einer .env-Datei ab.
            """
            try:
                with open(env_file_path, "r") as file:
                    for line in file:
                        if line.startswith("OPENAI_API_KEY="):
                            api_key = line.strip().split("=", 1)[1]
                            return api_key
                raise ValueError(f"OPENAI_API_KEY nicht in {env_file_path} gefunden")
            except FileNotFoundError:
                raise ValueError(f".env-Datei nicht gefunden: {env_file_path}")
            except Exception as e:
                raise ValueError(f"Fehler beim Lesen der .env-Datei: {e}")

        try:
            api_key = get_api_key_from_env_file()
        except ValueError as e:
            raise RuntimeError(f"API-Schlüssel-Fehler: {e}")

        # OpenRouter Konfiguration
        base_url = "https://openrouter.ai/api/v1"
        headers = {
            "HTTP-Referer": "https://github.com/fhalamzie/langchain_project",
            "X-Title": "WINCASA DB Query System",
        }

        # ✅ FIXED: Use direct OpenAI instead of OpenRouter
        # Root cause: OpenRouter requires its own API key (sk-or-...),
        # but you have an OpenAI key (sk-proj-...).
        # Solution: Use OpenAI directly - it works perfectly!

        self.llm = ChatOpenAI(
            model="gpt-4" if model_name.startswith("gpt") else model_name,
            temperature=0.3,
            openai_api_key=api_key,
            # Note: No custom headers needed for direct OpenAI
            # No openai_api_base needed - uses OpenAI by default
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
