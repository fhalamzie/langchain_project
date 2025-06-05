"""
qa_enhancer.py - Erweitertes Q&A-System mit SQL-Ausführung und Ergebnisaufbereitung

Dieses Modul verbessert die bestehende Q&A-Funktionalität durch:
1. Optimierte Kontext-Auswahl für Tabellen
2. Ausführung generierter SQL-Abfragen
3. Aufbereitung der Ergebnisse für benutzerfreundliche Antworten
4. Feedback-Mechanismen für kontinuierliche Verbesserung
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# Importiere lokale Module
from db_executor import execute_sql, get_all_tables, results_to_dataframe
from langchain_openai import ChatOpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Konfiguration
SCHEMA_DIR = Path("./output/schema")
YAML_DIR = Path("./output/yamls")
COMPACT_SCHEMA_PATH = SCHEMA_DIR / "compact_schema.json"
LOG_DIR = Path("./output/logs")
FEEDBACK_DIR = Path("./output/feedback")
MAX_CONTEXT_TOKENS = 4000  # Ungefähre Tokengrenze für Kontext
MAX_TABLES_IN_CONTEXT = 7  # Maximale Anzahl von Tabellen im Kontext

# Stelle sicher, dass die Verzeichnisse existieren
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


class QAEnhancer:
    """
    Erweiterte Q&A-Klasse mit SQL-Ausführung und Ergebnisaufbereitung.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialisiert die QAEnhancer-Klasse.

        Args:
            api_key: OpenAI API-Schlüssel (optional)
        """
        # API-Schlüssel aus .env-Datei oder Parameter
        if api_key is None:
            api_key = self._get_api_key_from_env()

        # Initialisiere das LLM für verschiedene Zwecke
        self.llm = ChatOpenAI(
            model="gpt-4-1106-preview", temperature=0, openai_api_key=api_key
        )

        # LLM mit höherer Kreativität für Antwortgenerierung
        self.answer_llm = ChatOpenAI(
            model="gpt-4-1106-preview", temperature=0.3, openai_api_key=api_key
        )

        # Lade das kompakte Schema, wenn es existiert
        self.schema_data = self._load_compact_schema()

        # Vektorisierer für semantische Ähnlichkeitssuche
        self.vectorizer = None
        self.table_vectors = None
        self.table_names = []

        # Initialisiere die semantische Suche
        self._initialize_semantic_search()

    def _get_api_key_from_env(self, env_file_path="/home/envs/openai.env"):
        """Ruft den API-Schlüssel aus einer .env-Datei ab."""
        try:
            with open(env_file_path, "r") as file:
                for line in file:
                    if line.startswith("OPENAI_API_KEY="):
                        return line.strip().split("=", 1)[1]
            raise ValueError(
                f"OPENAI_API_KEY nicht in der Datei {env_file_path} gefunden"
            )
        except FileNotFoundError:
            raise ValueError(f"Die .env-Datei wurde nicht gefunden: {env_file_path}")
        except Exception as e:
            raise ValueError(f"Unerwarteter Fehler beim Lesen der .env-Datei: {e}")

    def _load_compact_schema(self) -> Dict[str, Any]:
        """
        Lädt die kompakte Schemabeschreibung aus der JSON-Datei.

        Returns:
            Dict: Die Schemadaten oder ein leeres Dictionary, wenn nicht verfügbar
        """
        if not COMPACT_SCHEMA_PATH.exists():
            print("Kompakte Schemadatei nicht gefunden.")
            return {}

        try:
            with open(COMPACT_SCHEMA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden der Schemadatei: {e}")
            return {}

    def _initialize_semantic_search(self):
        """Initialisiert die Komponenten für semantische Suche."""
        if not self.schema_data or "tables" not in self.schema_data:
            print("Keine Schemadaten für semantische Suche verfügbar.")
            return

        # Extrahiere Tabellennamen und Beschreibungen
        table_texts = []
        self.table_names = []

        for table_name, table_info in self.schema_data.get("tables", {}).items():
            self.table_names.append(table_name)

            # Kombiniere verschiedene Textfelder für bessere Matching-Ergebnisse
            description = table_info.get("description", "")
            business_context = table_info.get("business_context", "")

            # Erstelle einen kombinierten Text mit Schlüsselwörtern
            combined_text = f"{table_name} {description} {business_context}"

            # Füge Spalteninformationen hinzu
            for column in table_info.get("columns", []):
                col_name = column.get("name", "")
                col_desc = column.get("description", "")
                combined_text += f" {col_name} {col_desc}"

            table_texts.append(combined_text)

        # Erstelle TF-IDF-Vektoren
        if table_texts:
            self.vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
            self.table_vectors = self.vectorizer.fit_transform(table_texts)

    def get_relevant_tables(
        self, query: str, max_tables: int = MAX_TABLES_IN_CONTEXT
    ) -> List[str]:
        """
        Ermittelt die relevantesten Tabellen für eine Benutzeranfrage.

        Args:
            query: Die Benutzeranfrage
            max_tables: Maximale Anzahl zurückzugebender Tabellen

        Returns:
            List[str]: Liste der relevantesten Tabellennamen
        """
        if not self.vectorizer or not self.table_vectors.any():
            print("Semantische Suche nicht initialisiert.")
            return []

        # Verarbeite die Anfrage
        query_vector = self.vectorizer.transform([query])

        # Berechne Ähnlichkeiten
        similarities = cosine_similarity(query_vector, self.table_vectors).flatten()

        # Sortiere Tabellen nach Ähnlichkeit
        table_similarity = [
            (self.table_names[i], similarities[i]) for i in range(len(self.table_names))
        ]
        sorted_tables = sorted(table_similarity, key=lambda x: x[1], reverse=True)

        # Gib die Top-N-Tabellen zurück
        return [table for table, score in sorted_tables[:max_tables] if score > 0.1]

    def get_table_context(self, table_names: List[str]) -> str:
        """
        Erstellt einen Kontext-String für die angegebenen Tabellen.

        Args:
            table_names: Liste der Tabellennamen

        Returns:
            str: Formatierter Kontext mit Tabellenbeschreibungen
        """
        if not self.schema_data or "tables" not in self.schema_data:
            return "Keine Schemainformationen verfügbar."

        context_parts = []

        for table_name in table_names:
            if table_name in self.schema_data.get("tables", {}):
                table_info = self.schema_data["tables"][table_name]

                # Sammle Tabelleninformationen
                description = table_info.get(
                    "description", "Keine Beschreibung verfügbar."
                )
                business_context = table_info.get("business_context", "")

                # Erstelle Tabellenbeschreibung
                table_context = f"TABELLE: {table_name}\n"
                table_context += f"BESCHREIBUNG: {description}\n"

                if business_context:
                    table_context += f"GESCHÄFTSKONTEXT: {business_context}\n"

                # Füge Spalteninformationen hinzu
                table_context += "SPALTEN:\n"
                for column in table_info.get("columns", []):
                    col_name = column.get("name", "")
                    col_desc = column.get("description", "Keine Beschreibung")
                    col_type = column.get("type", "")

                    table_context += f"  - {col_name} ({col_type}): {col_desc}\n"

                # Füge Beziehungen hinzu, wenn vorhanden
                relations = table_info.get("relations", {})
                if relations:
                    table_context += "BEZIEHUNGEN:\n"

                    # Fremdschlüssel
                    if "foreign_keys" in relations and relations["foreign_keys"]:
                        table_context += "  Fremdschlüssel:\n"
                        for fk in relations["foreign_keys"]:
                            if isinstance(fk, dict):
                                field = fk.get("field", "")
                                ref_table = fk.get("references_table", "")
                                ref_field = fk.get("references_field", "")
                                table_context += (
                                    f"    - {field} → {ref_table}({ref_field})\n"
                                )
                            elif isinstance(fk, str):
                                table_context += f"    - {fk}\n"

                    # Referenziert von
                    if "referenced_by" in relations and relations["referenced_by"]:
                        table_context += "  Referenziert von:\n"
                        for ref in relations["referenced_by"]:
                            if isinstance(ref, dict):
                                ref_table = ref.get("table", "")
                                ref_field = ref.get("field", "")
                                table_context += f"    - {ref_table}({ref_field})\n"
                            elif isinstance(ref, str):
                                table_context += f"    - {ref}\n"

                # Typische Abfragen
                common_queries = table_info.get("common_queries", [])
                if common_queries:
                    table_context += "TYPISCHE ABFRAGEN:\n"
                    for query in common_queries[:3]:  # Begrenze auf 3 Beispiele
                        table_context += f"  - {query}\n"

                context_parts.append(table_context)

        # Kombiniere alle Tabellenkontexte
        return "\n\n".join(context_parts)

    def generate_sql(self, user_query: str, schema_context: str) -> str:
        """
        Generiert SQL basierend auf der Benutzeranfrage und dem Schema-Kontext.

        Args:
            user_query: Die Benutzeranfrage
            schema_context: Der Schemakontext mit relevanten Tabellen

        Returns:
            str: Die generierte SQL-Abfrage
        """
        system_message = f"""Du bist ein SQL-Experte. 
        Generiere SQL-Abfragen basierend auf der Benutzeranfrage und dem bereitgestellten Datenbankschema.
        Du darfst NUR SELECT-Abfragen generieren. Andere Operationen (INSERT, UPDATE, DELETE, DROP usw.) sind nicht erlaubt.
        Verwende IMMER die korrekten Tabellen- und Spaltennamen aus dem bereitgestellten Schema.
        Antworte ausschließlich mit SQL-Code, ohne Erklärungen oder zusätzlichen Text.
        
        Hier ist das Datenbankschema:
        {schema_context}
        """

        messages = [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": f"Generiere eine SQL-Abfrage für: {user_query}",
            },
        ]

        # Generiere SQL mit dem LLM
        response = self.llm.invoke(messages)

        # Extrahiere den SQL-Code aus der Antwort
        sql = response.content.strip()

        # Entferne Markdown-Code-Blöcke, falls vorhanden
        sql = re.sub(r"^```sql\s*", "", sql)
        sql = re.sub(r"\s*```$", "", sql)

        return sql.strip()

    def format_results(self, results: List[Dict[str, Any]], max_rows: int = 10) -> str:
        """
        Formatiert die Abfrageergebnisse für die Anzeige.

        Args:
            results: Die Abfrageergebnisse
            max_rows: Maximale Anzahl von Zeilen für die Anzeige

        Returns:
            str: Formatierte Ergebnisse
        """
        if not results:
            return "Keine Ergebnisse gefunden."

        # Konvertiere zu DataFrame für einfacheres Handling
        df = results_to_dataframe(results)

        # Begrenze die Anzahl der Zeilen
        if len(df) > max_rows:
            df = df.head(max_rows)
            footer = f"\n... und {len(results) - max_rows} weitere Zeilen"
        else:
            footer = ""

        # Formatiere als Markdown-Tabelle
        formatted = df.to_markdown(index=False) + footer

        return formatted

    def generate_natural_answer(
        self,
        user_query: str,
        sql: str,
        results: List[Dict[str, Any]],
        schema_context: str,
    ) -> str:
        """
        Generiert eine natürlichsprachige Antwort basierend auf den Abfrageergebnissen.

        Args:
            user_query: Die Benutzeranfrage
            sql: Die ausgeführte SQL-Abfrage
            results: Die Abfrageergebnisse
            schema_context: Der Schemakontext

        Returns:
            str: Die natürlichsprachige Antwort
        """
        # Bereite die Ergebnisse für das LLM vor
        if not results:
            results_text = "Keine Ergebnisse gefunden."
        else:
            # Begrenze die Anzahl der Ergebnisse, um den Kontext nicht zu überschreiten
            limited_results = results[:20]
            df = results_to_dataframe(limited_results)
            results_text = df.to_csv(index=False)

            if len(results) > 20:
                results_text += f"\n\n(Nur die ersten 20 von insgesamt {len(results)} Ergebnissen werden angezeigt)"

        system_message = """Du bist ein hilfreicher Assistent für Datenbankabfragen.
        Deine Aufgabe ist es, die Ergebnisse einer SQL-Abfrage in natürlicher Sprache zusammenzufassen.
        Beantworte die Frage des Benutzers basierend auf den SQL-Ergebnissen.
        Erkläre die Ergebnisse klar und verständlich und beziehe dich auf die spezifischen Daten.
        Wenn keine Ergebnisse gefunden wurden, erkläre mögliche Gründe dafür.
        Gib keine Informationen an, die nicht in den Ergebnissen enthalten sind.
        """

        messages = [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": (
                    f"""Benutzerfrage: {user_query}
            
            Ausgeführte SQL-Abfrage:
            {sql}
            
            Abfrageergebnisse:
            {results_text}
            
            Basierend auf diesen Informationen, beantworte die Frage des Benutzers in natürlicher Sprache.
            """
                ),
            },
        ]

        # Generiere die natürlichsprachige Antwort
        response = self.answer_llm.invoke(messages)

        return response.content.strip()

    def log_interaction(
        self, user_query: str, sql: str, success: bool, result_summary: str, answer: str
    ) -> None:
        """
        Protokolliert eine Benutzerinteraktion für spätere Analyse.

        Args:
            user_query: Die Benutzeranfrage
            sql: Die generierte SQL-Abfrage
            success: Ob die Abfrage erfolgreich war
            result_summary: Zusammenfassung der Ergebnisse
            answer: Die generierte Antwort
        """
        log_file = LOG_DIR / "qa_interactions.jsonl"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "sql": sql,
            "success": success,
            "result_summary": result_summary,
            "answer": answer,
        }

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Fehler beim Protokollieren der Interaktion: {e}")

    def save_feedback(
        self,
        user_query: str,
        answer: str,
        feedback: str,
        rating: int,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Speichert Benutzerfeedback zur generierten Antwort.

        Args:
            user_query: Die Benutzeranfrage
            answer: Die generierte Antwort
            feedback: Textfeedback des Benutzers
            rating: Bewertung (1-5)
            user_id: Optionale Benutzer-ID
        """
        feedback_file = FEEDBACK_DIR / "user_feedback.jsonl"

        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "user_query": user_query,
            "answer": answer,
            "rating": rating,
            "feedback": feedback,
        }

        try:
            with open(feedback_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(feedback_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Fehler beim Speichern des Feedbacks: {e}")

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Verarbeitet eine Benutzeranfrage von Anfang bis Ende.

        Args:
            user_query: Die Benutzeranfrage

        Returns:
            Dict: Ergebnisse der Verarbeitung mit SQL, Rohdaten und Antwort
        """
        # 1. Relevante Tabellen finden
        relevant_tables = self.get_relevant_tables(user_query)

        # Wenn keine relevanten Tabellen gefunden wurden, gib einen Hinweis zurück
        if not relevant_tables:
            return {
                "success": False,
                "error": "Keine relevanten Tabellen für diese Anfrage gefunden.",
                "sql": "",
                "raw_results": [],
                "formatted_results": "",
                "answer": (
                    "Ich konnte keine relevanten Tabellen für Ihre Anfrage identifizieren. Bitte stellen Sie Ihre Frage anders oder spezifischer."
                ),
            }

        # 2. Schemakontext erstellen
        schema_context = self.get_table_context(relevant_tables)

        # 3. SQL generieren
        sql = self.generate_sql(user_query, schema_context)

        # 4. SQL ausführen
        success, result = execute_sql(sql)

        # 5. Ergebnisse formatieren
        if success:
            formatted_results = self.format_results(result)

            # 6. Natürlichsprachige Antwort generieren
            answer = self.generate_natural_answer(
                user_query, sql, result, schema_context
            )
        else:
            formatted_results = f"Fehler: {result}"
            answer = f"Bei der Ausführung der SQL-Abfrage ist ein Fehler aufgetreten: {result}"

        # 7. Interaktion protokollieren
        result_summary = (
            f"{len(result) if success else 0} Ergebnisse" if success else result
        )
        self.log_interaction(user_query, sql, success, result_summary, answer)

        # 8. Ergebnis zurückgeben
        return {
            "success": success,
            "sql": sql,
            "relevant_tables": relevant_tables,
            "raw_results": result if success else [],
            "formatted_results": formatted_results,
            "answer": answer,
        }


# Beispielverwendung
if __name__ == "__main__":
    enhancer = QAEnhancer()

    # Beispielanfrage
    query = "Welche Bewohner leben in der Marienstraße 26?"

    result = enhancer.process_query(query)

    print("Benutzeranfrage:", query)
    print("\nGenerierte SQL:", result["sql"])
    print("\nRelevante Tabellen:", result["relevant_tables"])
    print("\nFormatierte Ergebnisse:", result["formatted_results"])
    print("\nNatürlichsprachige Antwort:", result["answer"])
