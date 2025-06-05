import hashlib
import json
import os
import random
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

# Temporäres Verzeichnis für Firebird einrichten
fb_temp_dir = Path("./fb_temp").absolute()
if not fb_temp_dir.exists():
    fb_temp_dir.mkdir(exist_ok=True)
print(f"Firebird temporäres Verzeichnis: {fb_temp_dir}")

# Alle relevanten Umgebungsvariablen für Firebird setzen
os.environ["FIREBIRD_TMP"] = str(fb_temp_dir)
os.environ["FIREBIRD_TEMP"] = str(fb_temp_dir)
os.environ["FIREBIRD_TMPDIR"] = str(fb_temp_dir)
os.environ["FB_TMPDIR"] = str(fb_temp_dir)
os.environ["TMPDIR"] = str(fb_temp_dir)
os.environ["TMP"] = str(fb_temp_dir)
os.environ["TEMP"] = str(fb_temp_dir)
os.environ["FB_HOME"] = str(fb_temp_dir)
os.environ["FIREBIRD_HOME"] = str(fb_temp_dir)
os.environ["FIREBIRD_LOCK"] = str(fb_temp_dir)

import subprocess
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Erst jetzt importieren wir fdb
import fdb
import streamlit as st
from faker import Faker
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


# ==== SETUP – VERBESSERTE VERZEICHNISERSTELLUNG
# API-Schlüssel aus der .env-Datei abrufen
def get_api_key_from_env_file(env_file_path="/home/envs/openai.env"):
    """
    Ruft den API-Schlüssel aus einer .env-Datei ab.

    Args:
        env_file_path: Der Pfad zur .env-Datei (Standard: "/home/envs/openai.env")

    Returns:
        str: Der abgerufene API-Schlüssel

    Raises:
        ValueError: Wenn der API-Schlüssel nicht abgerufen werden kann
    """
    try:
        with open(env_file_path, "r") as file:
            for line in file:
                if line.startswith("OPENAI_API_KEY="):
                    # Extrahiere den Wert nach dem Gleichheitszeichen
                    api_key = line.strip().split("=", 1)[1]
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
    raise ValueError(
        f"OPENAI_API_KEY konnte nicht aus der .env-Datei abgerufen werden: {e}"
    )

# Datenbank-Konfiguration
DB_PATH = "./WINCASA2022.FDB"
DB_USER = "SYSDBA"
DB_PASSWORD = "masterkey"
faker = Faker("de_DE")


def ensure_dir(directory):
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


# Zentrale Verzeichnisdefinitionen
output_dir = ensure_dir("output")
yaml_output_dir = ensure_dir("output/yamls")
schema_output_dir = ensure_dir("output/schema")
ddl_output_dir = ensure_dir("output/ddl")
logs_dir = ensure_dir("output/logs")
DEFAULT_MAX_SAMPLE_SIZE = 15
MAX_MODEL_TOKENS = 128000
TOKEN_MARGIN = 5000
llm = ChatOpenAI(
    model="gpt-4-1106-preview", temperature=0, openai_api_key=openai_api_key
)


# ==== MODELS
class Column(BaseModel):
    name: str
    description: str
    type: str
    nullable: bool
    semantic_type: str = ""
    example_values: List[str] = Field(default_factory=list)


class TableDocumentation(BaseModel):
    table_name: str
    description: str
    business_context: str = ""
    business_examples: List[str] = Field(default_factory=list)
    internal_conventions: str = ""
    columns: List[Column]
    machine_constraints: Any = Field(default_factory=dict)
    is_empty: bool = False
    priority: str = "medium"
    common_queries: List[str] = Field(default_factory=list)
    relations: Optional[List[Any]] = Field(default_factory=list)


parser = PydanticOutputParser(pydantic_object=TableDocumentation)


# ==== STATUS FÜR ALLE PHASEN/KOMPONENTEN
class GenerationStatus:
    def __init__(self):
        self.tables_generated = 0
        self.tables_skipped = 0
        self.tables_in_phase1 = 0
        self.tables_in_phase2 = 0
        self.procedures_generated = 0
        self.procedures_skipped = 0
        self.procedures_in_phase1 = 0
        self.procedures_in_phase2 = 0
        self.schema_generated = False
        self.diagrams_generated = False
        self.ddl_generated = False
        self.relations_analyzed = False
        self.errors = []
        self.warnings = []
        self.info = []
        self.generated_details = {}

    def to_dict(self):
        return {
            "tables": {
                "generated": self.tables_generated,
                "skipped": self.tables_skipped,
                "in_phase1": self.tables_in_phase1,
                "in_phase2": self.tables_in_phase2,
            },
            "procedures": {
                "generated": self.procedures_generated,
                "skipped": self.procedures_skipped,
                "in_phase1": self.procedures_in_phase1,
                "in_phase2": self.procedures_in_phase2,
            },
            "components": {
                "schema": self.schema_generated,
                "diagrams": self.diagrams_generated,
                "ddl": self.ddl_generated,
                "relations": self.relations_analyzed,
            },
            "messages": {
                "errors": self.errors,
                "warnings": self.warnings,
                "info": self.info,
            },
            "generated_details": self.generated_details,
        }

    def save(self):
        try:
            with open(os.path.join(logs_dir, "generation_status.json"), "w") as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Fehler beim Speichern des Status: {e}")

    def load(self):
        try:
            with open(os.path.join(logs_dir, "generation_status.json"), "r") as f:
                data = json.load(f)
                for category, values in data["tables"].items():
                    setattr(self, f"tables_{category}", values)
                for category, values in data["procedures"].items():
                    setattr(self, f"procedures_{category}", values)
                for component, value in data["components"].items():
                    setattr(self, f"{component}_generated", value)
                self.errors = data["messages"]["errors"]
                self.warnings = data["messages"]["warnings"]
                self.info = data["messages"]["info"]
                self.generated_details = data.get("generated_details", {})
        except Exception as e:
            print(f"Fehler beim Laden des Status: {e}")


status = GenerationStatus()
if not os.path.exists(os.path.join(logs_dir, "generation_status.json")):
    status.save()


# ==== HILFSFUNKTIONEN (Token, Logging, etc.)
def count_tokens_of_prompt(prompt_msg):
    try:
        if isinstance(prompt_msg, list):
            if isinstance(prompt_msg[0], dict):
                content = prompt_msg[0].get("content", "")
            elif hasattr(prompt_msg[0], "content"):
                content = prompt_msg[0].content
            else:
                content = str(prompt_msg[0])
        else:
            content = str(prompt_msg)
        return int(len(content.encode("utf-8")) / 3.5)
    except Exception as e:
        print("Tokenzähler-Fehler:", e)
        return MAX_MODEL_TOKENS


def merge_yaml_outputs(yaml_list):
    if not yaml_list:
        return {}
    merged = dict(yaml_list[0])
    merged_columns = []
    for y in yaml_list:
        if "columns" in y and isinstance(y["columns"], list):
            merged_columns.extend(y["columns"])
    merged["columns"] = merged_columns
    for key in ["business_examples", "relations", "common_queries"]:
        merged[key] = []
        for y in yaml_list:
            v = y.get(key, [])
            if v:
                merged[key].extend(v if isinstance(v, list) else [v])
    for field in [
        "description",
        "business_context",
        "internal_conventions",
        "machine_constraints",
    ]:
        found = [y.get(field, "") for y in yaml_list if y.get(field, "")]
        merged[field] = found[0] if found else ""
    merged["is_empty"] = False
    merged["priority"] = "high"
    merged["table_name"] = merged.get(
        "table_name", yaml_list[0].get("table_name", "MERGED_PROCEDURE")
    )
    return merged


def log_skipped_item(item_name, item_type="table"):
    try:
        log_file = os.path.join(logs_dir, "skipped_items.json")
        skipped_data = {"tables": [], "procedures": []}
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    skipped_data = json.load(f)
            except:
                pass
        if item_type == "table":
            if item_name not in skipped_data["tables"]:
                skipped_data["tables"].append(item_name)
                status.tables_skipped += 1
        elif item_type == "procedure":
            if item_name not in skipped_data["procedures"]:
                skipped_data["procedures"].append(item_name)
                status.procedures_skipped += 1
        with open(log_file, "w") as f:
            json.dump(skipped_data, f)
    except Exception as e:
        print(f"Fehler beim Protokollieren des übersprungenen Elements: {e}")


def log_message(message, level="info", save_status=True):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        if level == "error":
            print(f"ERROR: {message}")
            status.errors.append(formatted_message)
            st.error(message)
        elif level == "warning":
            print(f"WARNING: {message}")
            status.warnings.append(formatted_message)
            st.warning(message)
        else:
            print(f"INFO: {message}")
            status.info.append(formatted_message)
            st.info(message)
        if save_status:
            status.save()
    except Exception as e:
        print(f"Fehler beim Loggen der Nachricht: {e}")


# ==== SAFE LLM CALL
def safe_llm_call(prompt, item_name, item_type="table"):
    try:
        # Bestimme die Tokenzahl basierend auf dem übergebenen Prompt-Format
        if isinstance(prompt, list):
            if isinstance(prompt[0], dict):
                # Prompt ist eine Liste von Dicts
                content = prompt[0].get("content", "")
            elif hasattr(prompt[0], "content"):
                # Prompt ist eine Liste von Message-Objekten
                content = prompt[0].content
            else:
                # Fallback, falls es sich um ein unerwartetes Format handelt
                content = str(prompt[0])
        else:
            content = str(prompt)

        token_estimate = int(len(content.encode("utf-8")) / 3.5)
        print(f"Prompt für {item_name}: ca. {token_estimate} tokens")
        log_message(
            f"Prompt für {item_name}: ca. {token_estimate} Tokens (Schätzung)",
            "info",
            save_status=False,
        )

        if token_estimate > (MAX_MODEL_TOKENS - TOKEN_MARGIN):
            log_message(
                f"⏩ {item_type.capitalize()} '{item_name}' übersprungen (Prompt zu groß: {int(token_estimate)} Tokens)",
                "warning",
            )
            print(
                f"⏩ SKIP {item_name} wegen zu großem Prompt ({int(token_estimate)} tokens geschätzt!)"
            )
            log_skipped_item(item_name, item_type)
            return None

        try:
            # Bei Dict-Prompts die Größe überprüfen
            if isinstance(prompt, list) and isinstance(prompt[0], dict):
                prompt_size = len(json.dumps(content))
                max_safe_size = 450000
                if prompt_size > max_safe_size:
                    log_message(
                        f"⏩ {item_type.capitalize()} '{item_name}' übersprungen (Prompt-Byte-Größe zu groß: {prompt_size} Bytes)",
                        "warning",
                    )
                    log_skipped_item(item_name, item_type)
                    return None
        except Exception as e:
            print(f"Fehler bei Prompt-Size-Überprüfung: {e}")
            if token_estimate > (MAX_MODEL_TOKENS - TOKEN_MARGIN * 2):
                log_skipped_item(item_name, item_type)
                return None

        # Bei Message-Objekten die Rolle sicherstellen
        if (
            isinstance(prompt, list)
            and isinstance(prompt[0], dict)
            and "role" not in prompt[0]
        ):
            # Füge role hinzu, falls diese fehlt
            new_prompt = []
            for msg in prompt:
                if "role" not in msg:
                    msg = {"role": "user", **msg}
                new_prompt.append(msg)
            prompt = new_prompt

        return llm.invoke(prompt)

    except Exception as e:
        log_message(f"Fehler beim LLM-Aufruf für {item_name}: {str(e)}", "error")
        print(f"ERROR bei {item_name}: {str(e)}")
        log_skipped_item(item_name, item_type)
        return None


# ==== LLM-basierte Übersetzung
def translate_to_german(text):
    prompt = [
        {
            "role": "user",
            "content": (
                f"Übersetze folgenden Text ins Deutsche und korrigiere alle eventuellen Fehler:\n\n{text}"
            ),
        }
    ]
    response = safe_llm_call(prompt, "Translation", item_type="translation")
    if response:
        return response.content.strip()
    else:
        return text


# ==== YAML FIX-FUNKTIONEN
def validate_yaml(yaml_text):
    try:
        cleaned_text = yaml_text.strip()
        # Entferne Markdown-Formatierungen, falls vorhanden
        if cleaned_text.startswith("```yaml"):
            cleaned_text = re.sub(r"```yaml\s*", "", cleaned_text)
            cleaned_text = re.sub(r"\s*```\s*$", "", cleaned_text)
        elif cleaned_text.startswith("```"):
            cleaned_text = re.sub(r"```\s*", "", cleaned_text)
            cleaned_text = re.sub(r"\s*```\s*$", "", cleaned_text)

        # Validiere das YAML
        yaml.safe_load(cleaned_text)
        return True, cleaned_text
    except Exception as e:
        print(f"YAML-Validierungsfehler: {e}")
        # Versuche grundlegende YAML-Syntax-Fehler zu beheben
        try:
            lines = cleaned_text.split("\n")
            fixed_lines = []
            indentation = ""
            for i, line in enumerate(lines):
                if (
                    i > 0
                    and line.strip()
                    and ":" not in line
                    and not line.strip().startswith("-")
                    and not line.strip().startswith("#")
                ):
                    # Füge Strichpunkt für Listen-Elemente hinzu, wenn diese fehlen
                    if indentation:
                        fixed_lines.append(f"{indentation}- {line.strip()}")
                    else:
                        fixed_lines.append(f"- {line.strip()}")
                else:
                    fixed_lines.append(line)
                    # Speichere die aktuelle Einrückung, wenn es eine Schlüssel-Definition gibt
                    if ":" in line:
                        match = re.match(r"^(\s*)", line)
                        if match:
                            indentation = (
                                match.group(1) + "  "
                            )  # Einrückung plus 2 Leerzeichen

            fixed_yaml = "\n".join(fixed_lines)
            # Überprüfe, ob die Reparatur erfolgreich war
            yaml.safe_load(fixed_yaml)
            return True, fixed_yaml
        except:
            # Wenn auch das Fixen fehlschlägt, gib den Original-Fehler zurück
            return False, f"YAML-Fehler: {str(e)}"


def fix_yaml_for_table(table_name, translate_english=False):
    try:
        yaml_file = yaml_output_dir / f"{table_name}.yaml"
        if not yaml_file.exists():
            return False, f"YAML für {table_name} existiert nicht."
        with open(yaml_file, "r", encoding="utf-8") as f:
            broken_yaml = f.read()
        fix_prompt = f"""Du erhältst folgenden fehlerhaften YAML-Code. Bitte repariere diesen Code so, dass ein gültiges YAML resultiert.
Übersetze auch alle englischen Beschreibungen ins Deutsche.
Antworte ausschließlich mit dem korrigierten YAML-Code, ohne zusätzliche Erklärungen.
{broken_yaml}
"""
        prompt = [{"role": "user", "content": fix_prompt}]
        response = safe_llm_call(prompt, f"{table_name} YAML Fix", item_type="yaml_fix")
        if not response:
            return False, f"LLM-Antwort zum Fixen von {table_name} fehlgeschlagen."
        fixed_yaml = response.content.strip()
        if translate_english:
            fixed_yaml = translate_to_german(fixed_yaml)
        valid, cleaned_yaml = validate_yaml(fixed_yaml)
        if valid:
            with open(yaml_file, "w", encoding="utf-8") as f:
                f.write(cleaned_yaml)
            return True, f"YAML für {table_name} erfolgreich repariert."
        else:
            return (
                False,
                f"Reparatur für {table_name} hat nicht zu gültigem YAML geführt.",
            )
    except Exception as e:
        return False, f"Fehler bei der YAML-Reparatur für {table_name}: {str(e)}"


def fix_all_broken_yamls(translate_english=False):
    broken_tables = identify_broken_yamls()
    results = {}
    for table in broken_tables:
        if "_PROCEDURE" in table:
            continue
        success, msg = fix_yaml_for_table(table, translate_english=translate_english)
        results[table] = (success, msg)
        log_message(msg, "info" if success else "warning")
    return results


def identify_broken_yamls():
    broken = []
    for file in yaml_output_dir.glob("*.yaml"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                valid, _ = validate_yaml(content)
                if not valid:
                    broken.append(file.stem.upper())
        except:
            broken.append(file.stem.upper())
    return broken


# ==== DB BASICS & DDL-FUNKTIONEN
def clean_yaml_response(response_text: str) -> str:
    if response_text.strip().startswith("```yaml"):
        match = re.search(r"```yaml\s*([\s\S]*?)```", response_text)
        if match:
            return match.group(1).strip()
    elif response_text.strip().startswith("```"):
        match = re.search(r"```\s*([\s\S]*?)```", response_text)
        if match:
            return match.group(1).strip()
    return response_text


@contextmanager
def get_db_connection():
    conn = None
    try:
        # Überprüfe, ob die Datenbankdatei existiert
        if not os.path.exists(DB_PATH):
            log_message(
                f"Datenbank-Datei '{DB_PATH}' nicht gefunden. Falls Sie die Datenbank haben, stellen Sie sicher, dass sie im richtigen Pfad liegt.",
                "warning",
            )
            yield None
            return

        conn = fdb.connect(
            dsn=DB_PATH, user=DB_USER, password=DB_PASSWORD, charset="WIN1252"
        )
        yield conn
    except Exception as e:
        log_message(f"Fehler bei der Datenbankverbindung: {e}", "error")
        log_message(
            "Das Skript wird ohne Datenbankverbindung fortgesetzt. Einige Funktionen könnten eingeschränkt sein.",
            "warning",
        )
        yield None
    finally:
        if conn:
            conn.close()


def convert_win1252_to_utf8(text):
    if isinstance(text, bytes):
        return text.decode("windows-1252", errors="replace")
    return text


def get_all_tables():
    try:
        with get_db_connection() as conn:
            if conn is None:
                log_message(
                    "Keine Datenbankverbindung verfügbar. Verwende Beispieltabellen.",
                    "warning",
                )
                return ["BEISPIEL_TABELLE1", "BEISPIEL_TABELLE2"]

            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT rdb$relation_name FROM rdb$relations
                WHERE rdb$view_blr IS NULL AND rdb$system_flag = 0
            """
            )
            return [row[0].strip() for row in cursor.fetchall()]
    except Exception as e:
        log_message(f"Fehler beim Abrufen aller Tabellen: {e}", "error")
        return []


def get_table_columns(table_name: str) -> List[str]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT * FROM {table_name} WHERE 1=0")
            return [desc[0].strip() for desc in cursor.description]
        except Exception as e:
            log_message(
                f"Fehler beim Abrufen der Spalten für {table_name}: {e}", "warning"
            )
            return []


def get_sample_data(table: str, sample_size: int = None) -> pd.DataFrame:
    try:
        columns = get_table_columns(table)
        col_count = len(columns)
        if sample_size is None:
            if col_count > 150:
                max_sample_size = 3
            elif col_count > 100:
                max_sample_size = 5
            elif col_count > 50:
                max_sample_size = 8
            else:
                max_sample_size = min(
                    DEFAULT_MAX_SAMPLE_SIZE, max(5, int(400 / max(1, col_count)))
                )
        else:
            max_sample_size = sample_size
        print(f"Tabelle {table}: {col_count} Spalten → {max_sample_size} Zeilen Sample")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"SELECT FIRST {max_sample_size} * FROM {table}")
                rows = cursor.fetchall()
                columns = [desc[0].strip() for desc in cursor.description]
                converted_rows = []
                for row in rows:
                    converted_row = [
                        (
                            convert_win1252_to_utf8(item)
                            if isinstance(item, bytes)
                            else item
                        )
                        for item in row
                    ]
                    converted_rows.append(converted_row)
                return pd.DataFrame(converted_rows, columns=columns)
            except Exception as e:
                log_message(
                    f"Fehler beim Abrufen von Beispieldaten aus {table}: {e}", "warning"
                )
                return pd.DataFrame()
    except Exception as e:
        log_message(f"Fehler beim Abrufen von Beispieldaten für {table}: {e}", "error")
        return pd.DataFrame()


def get_column_metadata(table_name: str) -> Dict[str, Dict[str, Any]]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    r.RDB$FIELD_NAME as field_name,
                    f.RDB$FIELD_TYPE as field_type,
                    f.RDB$FIELD_LENGTH as field_length,
                    f.RDB$FIELD_PRECISION as field_precision,
                    f.RDB$FIELD_SCALE as field_scale,
                    r.RDB$NULL_FLAG as is_not_null,
                    r.RDB$DEFAULT_SOURCE as default_value,
                    r.RDB$DESCRIPTION as description
                FROM RDB$RELATION_FIELDS r
                JOIN RDB$FIELDS f ON r.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
                WHERE r.RDB$RELATION_NAME = ?
                ORDER BY r.RDB$FIELD_POSITION
            """,
                (table_name,),
            )
            type_map = {
                7: "SMALLINT",
                8: "INTEGER",
                10: "FLOAT",
                12: "DATE",
                13: "TIME",
                14: "CHAR",
                16: "BIGINT",
                27: "DOUBLE PRECISION",
                35: "TIMESTAMP",
                37: "VARCHAR",
                261: "BLOB",
            }
            columns = {}
            for (
                name,
                type_id,
                length,
                precision,
                scale,
                not_null,
                default,
                desc,
            ) in cursor.fetchall():
                name = name.strip()
                data_type = type_map.get(type_id, f"UNKNOWN({type_id})")
                if (
                    data_type in ("SMALLINT", "INTEGER", "BIGINT")
                    and scale
                    and scale < 0
                ):
                    data_type = f"NUMERIC({precision},{abs(scale)})"
                if desc and isinstance(desc, bytes):
                    desc = convert_win1252_to_utf8(desc)
                if default and isinstance(default, bytes):
                    default = convert_win1252_to_utf8(default)
                columns[name] = {
                    "data_type": data_type,
                    "length": length,
                    "precision": precision,
                    "scale": scale,
                    "is_nullable": not_null != 1,
                    "default": default.strip() if default else None,
                    "description": desc.strip() if desc else None,
                }
            return columns
    except Exception as e:
        log_message(
            f"Fehler beim Abrufen der Spaltenmetadaten für {table_name}: {e}", "error"
        )
        return {}


def get_ddl_constraints(table_name: str):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            constraints = {
                "primary_key": [],
                "unique": [],
                "foreign_keys": [],
                "checks": [],
                "defaults": {},
            }
            cur.execute(
                """
              SELECT sg.RDB$FIELD_NAME FROM RDB$RELATION_CONSTRAINTS rc
              JOIN RDB$INDEX_SEGMENTS sg ON rc.RDB$INDEX_NAME = sg.RDB$INDEX_NAME
              WHERE rc.RDB$CONSTRAINT_TYPE = 'PRIMARY KEY' AND rc.RDB$RELATION_NAME = ?
            """,
                (table_name,),
            )
            constraints["primary_key"] = [r[0].strip() for r in cur.fetchall()]
            cur.execute(
                """
              SELECT sg.RDB$FIELD_NAME FROM RDB$RELATION_CONSTRAINTS rc
              JOIN RDB$INDEX_SEGMENTS sg ON rc.RDB$INDEX_NAME = sg.RDB$INDEX_NAME
              WHERE rc.RDB$CONSTRAINT_TYPE = 'UNIQUE' AND rc.RDB$RELATION_NAME = ?
            """,
                (table_name,),
            )
            constraints["unique"] = [r[0].strip() for r in cur.fetchall()]
            cur.execute(
                """
              SELECT sg.RDB$FIELD_NAME, rc2.RDB$RELATION_NAME, sg2.RDB$FIELD_NAME
              FROM RDB$RELATION_CONSTRAINTS rc
              JOIN RDB$REF_CONSTRAINTS re ON rc.RDB$CONSTRAINT_NAME = re.RDB$CONSTRAINT_NAME
              JOIN RDB$RELATION_CONSTRAINTS rc2 ON re.RDB$CONST_NAME_UQ = rc2.RDB$CONSTRAINT_NAME
              JOIN RDB$INDEX_SEGMENTS sg ON rc.RDB$INDEX_NAME = sg.RDB$INDEX_NAME
              JOIN RDB$INDEX_SEGMENTS sg2 ON rc2.RDB$INDEX_NAME = sg2.RDB$INDEX_NAME
              WHERE rc.RDB$CONSTRAINT_TYPE = 'FOREIGN KEY' AND rc.RDB$RELATION_NAME = ?
            """,
                (table_name,),
            )
            for f1, tab2, f2 in cur.fetchall():
                constraints["foreign_keys"].append(
                    {
                        "field": f1.strip(),
                        "references_table": tab2.strip(),
                        "references_field": f2.strip(),
                    }
                )
            cur.execute(
                """
              SELECT r.RDB$FIELD_NAME, r.RDB$DEFAULT_SOURCE, r.RDB$NULL_FLAG, f.RDB$VALIDATION_SOURCE
              FROM RDB$RELATION_FIELDS r
              JOIN RDB$FIELDS f ON r.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
              WHERE r.RDB$RELATION_NAME = ?
            """,
                (table_name,),
            )
            for fname, default, notnull, check in cur.fetchall():
                if default:
                    constraints["defaults"][fname.strip()] = convert_win1252_to_utf8(
                        default
                    ).strip()
                if check:
                    constraints["checks"].append(
                        {
                            "field": fname.strip(),
                            "rule": convert_win1252_to_utf8(check).strip(),
                        }
                    )
            return constraints
    except Exception as e:
        log_message(
            f"Fehler beim Abrufen der Constraints für {table_name}: {e}", "error"
        )
        return {
            "primary_key": [],
            "unique": [],
            "foreign_keys": [],
            "checks": [],
            "defaults": {},
        }


def get_table_relations(table_name: str) -> Dict[str, List[Dict[str, str]]]:
    relations = {"foreign_keys": [], "referenced_by": []}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT rc.RDB$CONSTRAINT_NAME, rc.RDB$RELATION_NAME, seg.RDB$FIELD_NAME,
                       rc2.RDB$RELATION_NAME, seg2.RDB$FIELD_NAME
                FROM RDB$RELATION_CONSTRAINTS rc
                JOIN RDB$REF_CONSTRAINTS refc ON rc.RDB$CONSTRAINT_NAME = refc.RDB$CONSTRAINT_NAME
                JOIN RDB$RELATION_CONSTRAINTS rc2 ON rc2.RDB$CONSTRAINT_NAME = refc.RDB$CONST_NAME_UQ
                JOIN RDB$INDEX_SEGMENTS seg ON rc.RDB$INDEX_NAME = seg.RDB$INDEX_NAME
                JOIN RDB$INDEX_SEGMENTS seg2 ON rc2.RDB$INDEX_NAME = seg2.RDB$INDEX_NAME
                WHERE rc.RDB$CONSTRAINT_TYPE = 'FOREIGN KEY'
                  AND rc.RDB$RELATION_NAME = ?
            """,
                (table_name,),
            )
            for _, table, field, ref_table, ref_field in cursor.fetchall():
                relations["foreign_keys"].append(
                    {
                        "field": field.strip() if field else "",
                        "references_table": ref_table.strip() if ref_table else "",
                        "references_field": ref_field.strip() if ref_field else "",
                    }
                )
            cursor.execute(
                """
                SELECT rc.RDB$CONSTRAINT_NAME, rc.RDB$RELATION_NAME, seg.RDB$FIELD_NAME,
                       rc2.RDB$RELATION_NAME, seg2.RDB$FIELD_NAME
                FROM RDB$RELATION_CONSTRAINTS rc
                JOIN RDB$REF_CONSTRAINTS refc ON rc.RDB$CONSTRAINT_NAME = refc.RDB$CONSTRAINT_NAME
                JOIN RDB$RELATION_CONSTRAINTS rc2 ON rc2.RDB$CONSTRAINT_NAME = refc.RDB$CONST_NAME_UQ
                JOIN RDB$INDEX_SEGMENTS seg ON rc.RDB$INDEX_NAME = seg.RDB$INDEX_NAME
                JOIN RDB$INDEX_SEGMENTS seg2 ON rc2.RDB$INDEX_NAME = seg2.RDB$INDEX_NAME
                WHERE rc.RDB$CONSTRAINT_TYPE = 'FOREIGN KEY'
                  AND rc2.RDB$RELATION_NAME = ?
            """,
                (table_name,),
            )
            for _, table, field, ref_table, ref_field in cursor.fetchall():
                relations["referenced_by"].append(
                    {
                        "table": table.strip() if table else "",
                        "field": field.strip() if field else "",
                        "via_field": ref_field.strip() if ref_field else "",
                    }
                )
    except Exception as e:
        log_message(
            f"Fehler beim Abfragen von Beziehungen für {table_name}: {e}", "warning"
        )
    return relations


def get_table_ddl(table_name: str) -> str:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            column_sql = []
            metadata = get_column_metadata(table_name)
            for col_name, col_info in metadata.items():
                data_type = col_info["data_type"]
                nullable = "NULL" if col_info["is_nullable"] else "NOT NULL"
                default = (
                    f"DEFAULT {col_info['default']}" if col_info["default"] else ""
                )
                column_sql.append(
                    f"    {col_name} {data_type} {nullable} {default}".strip()
                )
            constraints = get_ddl_constraints(table_name)
            if constraints["primary_key"]:
                pk_cols = ", ".join(constraints["primary_key"])
                column_sql.append(f"    PRIMARY KEY ({pk_cols})")
            for uk in constraints["unique"]:
                column_sql.append(f"    UNIQUE ({uk})")
            for fk in constraints["foreign_keys"]:
                column_sql.append(
                    f"    FOREIGN KEY ({fk['field']}) REFERENCES {fk['references_table']}({fk['references_field']})"
                )
            ddl = f"CREATE TABLE {table_name} (\n" + ",\n".join(column_sql) + "\n);"
            return ddl
    except Exception as e:
        log_message(f"Fehler beim Abrufen des DDL für {table_name}: {e}", "warning")
        return f"-- Fehler beim Generieren des DDL für {table_name}"


def get_procedure_ddl(proc_name: str) -> str:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT rdb$procedure_source FROM rdb$procedures
                WHERE rdb$procedure_name = ?
            """,
                (proc_name,),
            )
            result = cursor.fetchone()
            if result and result[0]:
                source = convert_win1252_to_utf8(result[0])
                return f"CREATE OR ALTER PROCEDURE {proc_name}\n{source}\n"
            else:
                return f"-- Kein Quelltext für Prozedur {proc_name} gefunden"
    except Exception as e:
        log_message(
            f"Fehler beim Abrufen des DDL für Prozedur {proc_name}: {e}", "warning"
        )
        return f"-- Fehler beim Generieren des Prozedur-DDL für {proc_name}"


# ==== SEMANTIK-FUNKTIONEN
SENSITIVE_COLUMNS = {
    "name": [
        "name",
        "vorname",
        "nachname",
        "kunde",
        "mieter",
        "person",
        "ansprechpartner",
        "kontakt",
    ],
    "email": ["email", "mail", "e-mail", "emailadresse"],
    "phone": ["telefon", "tel", "handy", "mobil", "fax", "telefonnr", "telnr"],
    "address": ["adresse", "straße", "strasse", "hausnr", "plz", "ort", "stadt"],
    "id": [
        "personalausweis",
        "ausweis",
        "pass",
        "reisepass",
        "id",
        "kundennr",
        "mieternr",
        "vertragsnr",
    ],
    "account": ["konto", "iban", "kontonr", "blz", "bank"],
    "finance": ["gehalt", "einkommen", "miete", "betrag", "summe", "preis", "zahlung"],
}
SPECIAL_KUERZEL_FIELDS = {
    "EIGADR": {"ENOTIZ": "owner_note"},
    "OBJEKTE": {"OBEZ": "street_code"},
}


def identify_column_type(
    column_name: str, sample_data: pd.Series = None, table_name: str = ""
) -> str:
    """
    Identifiziert den semantischen Typ einer Spalte basierend auf ihrem Namen und Beispieldaten.
    """
    col_name_lower = column_name.lower()
    tbl_upper = table_name.upper()
    if tbl_upper in SPECIAL_KUERZEL_FIELDS:
        sem = SPECIAL_KUERZEL_FIELDS[tbl_upper].get(column_name.upper())
        if sem:
            return sem
    for semantic_type, keywords in SENSITIVE_COLUMNS.items():
        if any(keyword in col_name_lower for keyword in keywords):
            return semantic_type
    return "regular"


def generate_street_code_example(street_name: str = "", house_number: str = "") -> str:
    if not street_name:
        street_examples = [
            "Marienstraße",
            "Hochfelder",
            "Lindenallee",
            "Hauptstraße",
            "Bergweg",
        ]
        street_name = random.choice(street_examples)
    if not house_number or not house_number.isdigit():
        house_number = str(random.randint(1, 99))
    street_clean = (
        street_name.upper()
        .replace("Ä", "AE")
        .replace("Ö", "OE")
        .replace("Ü", "UE")
        .replace("ß", "SS")
    )
    street_clean = re.sub(r"[^A-Z]", "", street_clean)
    prefix = street_clean[:5].ljust(5, "X")
    return f"{prefix}{house_number}"


def generate_sev_owner_note(first_name: str = None, last_name: str = None) -> str:
    if not first_name or not last_name:
        fake_name = faker.name().split()
        first_name = fake_name[0] if fake_name else "Max"
        last_name = fake_name[-1] if len(fake_name) > 1 else "Mustermann"
    first_initial = first_name[0].upper() if first_name else "X"
    last_name_clean = (
        last_name.upper()
        .replace("Ä", "AE")
        .replace("Ö", "OE")
        .replace("Ü", "UE")
        .replace("ß", "SS")
    )
    last_name_clean = re.sub(r"[^A-Z]", "", last_name_clean)
    return f"{first_initial}{last_name_clean}"


def generate_anonymized_example(original_value: Any, semantic_type: str) -> str:
    if original_value is None or pd.isna(original_value):
        return ""

    try:
        seed = str(original_value)
        hash_val = int(hashlib.md5(seed.encode("utf-8")).hexdigest(), 16) % 10000
        random.seed(hash_val)

        if semantic_type == "name":
            return faker.name()
        elif semantic_type == "email":
            return faker.email()
        elif semantic_type == "phone":
            return faker.phone_number()
        elif semantic_type == "address":
            return faker.address().replace("\n", " ")
        elif semantic_type == "id":
            return f"ID-{faker.random_number(digits=6)}"
        elif semantic_type == "account":
            return faker.iban()
        elif semantic_type == "finance":
            try:
                orig_val = float(str(original_value).replace(",", ".").replace(" ", ""))
                variance = max(abs(orig_val) * 0.1, 50)
                return (
                    f"{orig_val + random.uniform(-variance, variance):.2f} €".replace(
                        ".", ","
                    )
                )
            except:
                return f"{random.randint(100, 2000)},00 €"
        elif semantic_type == "street_code":
            return generate_street_code_example()
        elif semantic_type == "owner_note":
            return generate_sev_owner_note()
        else:
            return str(original_value)
    except Exception as e:
        print(f"Fehler bei Anonymisierung ({semantic_type}): {e}")
        return str(original_value)


def profile_data(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    if df.empty:
        return {}
    return {
        column: {
            "data_type": str(df[column].dtype),
            "null_count": df[column].isna().sum(),
            "unique_values": df[column].nunique(),
        }
        for column in df.columns
    }


def is_temporary_trivial_table(table_name, df, column_metadata, relations):
    if any(
        pat in table_name.lower()
        for pat in ["temp", "tmp", "cache", "backup", "hist", "log", "vorl"]
    ):
        return True

    if df is not None and not df.empty:
        trivial = True
        for col in df.columns:
            series = df[col]
            if series.nunique(dropna=True) > 1:
                trivial = False
                break
            if all(str(x).strip() in ["", "0", "0.0", "None", "NaN"] for x in series):
                continue
            else:
                trivial = False
                break
        if trivial and (
            not relations["foreign_keys"] and not relations["referenced_by"]
        ):
            return True

    if (
        column_metadata
        and all(meta.get("is_nullable", True) for meta in column_metadata.values())
        and (not relations["foreign_keys"] and not relations["referenced_by"])
    ):
        return True

    return False


def determine_table_priority(table_name, column_metadata, relations):
    normalized_name = table_name.lower()
    if (
        "objekt" in normalized_name
        or "mieter" in normalized_name
        or "vertrag" in normalized_name
    ):
        return "high"
    if len(relations["foreign_keys"]) > 3 or len(relations["referenced_by"]) > 3:
        return "high"
    if len(column_metadata) > 20:
        return "high"
    return "medium"


def typical_use_cases(table_name, columns, relations):
    normalized = table_name.lower()
    result = []
    if "objekt" in normalized or "immobilie" in normalized:
        result += [
            "Verknüpfung von Bewohnern und Mietverträgen mit Immobilien.",
            "Abfrage von Ausstattung und Zustand einzelner Objekte.",
            "Abfrage, in welcher Straße sich ein Objekt befindet.",
        ]
    if (
        "mieter" in normalized
        or "kunde" in normalized
        or "person" in normalized
        or "bewohner" in normalized
    ):
        result += [
            "Abfrage und Verwaltung persönlicher Kontaktdaten von Mietern.",
            "Zuordnung von Mietern zu Wohnungen/Einheiten.",
            "Nachverfolgung der Mietdauer eines Bewohners.",
        ]
    if "eigent" in normalized:
        result += [
            "Verwaltung von Eigentümerinformationen und -kontaktdaten.",
            "Zuordnung von Eigentümern zu Immobilien/Objekten.",
            "Nachverfolgung von Zahlungen und Vertragsbeziehungen mit Eigentümern.",
        ]
    if "vertrag" in normalized:
        result += [
            "Verwaltung von Start-, Endtermin und Konditionen des Mietvertrags.",
            "Übersicht über gekündigte oder bald auslaufende Verträge.",
            "Dokumentation und Verfolgung von Vertragsänderungen.",
        ]
    if not result:
        result = [f"Datenhaltung für {table_name}-Informationen."]
    return result


def typical_queries(table_name, columns, relations):
    normalized = table_name.lower()
    column_names = [c["name"].lower() for c in columns]
    queries = []
    if table_name.upper() == "EIGADR" or "enotiz" in column_names:
        queries.append("Wie lautet das SEV-Eigentümer-Kürzel für Max Mustermann?")
        queries.append(
            "Ist der Eigentümer mit Kürzel FHUBER ein SEV- oder WEG-Eigentümer?"
        )
    if table_name.upper() == "OBJEKTE" or "obez" in column_names:
        queries.append("Welche Straße verbirgt sich hinter dem Kürzel MARIE26?")
        queries.append("Wie viele Wohnungen hat das Objekt OBEZ=MARIE12?")
    if (
        "adresse" in column_names
        or "straße" in column_names
        or "strasse" in column_names
    ):
        queries.append("Wer wohnt aktuell in der Marienstraße 26?")
        queries.append(
            "Wie hoch ist die durchschnittliche Miete in der Hochfelder Straße?"
        )
    if not queries:
        queries = [f"Zeige Details zum Eintrag {table_name}."]
    return queries


PROMPT = """
Du bist ein datenbankkundiger Assistent für ein Immobilienverwaltungssystem namens "Wincasa".
Bevor du die YAML-Dokumentation generierst, denke explizit schrittweise über folgende Aspekte nach (Chain-of-Thought):
- Welche Constraints definieren die Tabelle (PK/FK/Unique/Check/Default)?
- Welche Rollen und Business-Kontexte gibt es für jede Spalte und für Beziehungen?
- Gibt es Lookup-/Referenztabellen für Codes/Status?
- Gibt es Hinweise, dass die Tabelle nur temporär oder irrelevant ist?
- Wie werden die Daten voraussichtlich benutzt?
Nutze dieses Reasoning, um besonders erklärende, nützliche und konsistente Beschreibungen und Use-Cases zu generieren!
WICHTIG: Antworte AUSSCHLIESSLICH AUF DEUTSCH. Alle Beschreibungen, Kommentare und Erläuterungen müssen auf Deutsch sein.
In der Tabelle EIGADR bedeutet das Feld ENOTIZ einen Eigentümer-Kürzel im Format Erster Buchstabe Vorname + Nachname (z.B. FHALAMZIE). In der Tabelle OBJEKTE enthält das Feld OBEZ das interne Straßenkürzel (erste 5 Buchstaben und Hausnummer, z.B. MARIE26). Bitte beschreibe diese internen Kürzel ausführlich im YAML (Feld "internal_conventions").
Erstelle ein YAML-Dokument mit
- table_name, description, business_context, business_examples, internal_conventions,
- columns, machine_constraints, is_empty, priority, common_queries, relations.
Antworte NUR mit YAML, OHNE ```yaml oder andere Markup-Tags!
Tabelle/Procedure: {table_name}
Spalten/Parameter mit Metadaten: {columns}
Beispielzeilen/Call-Beispiele: {examples}
Relationen: {relation_info}
Constraints/DDL: {ddl_constraints}
Tabelle ist leer: {is_empty}
Vermutete Priorität: {priority}
Typische Nutzung: {use_cases}
Typische Abfragen: {sample_queries}
"""
prompt_template = ChatPromptTemplate.from_template(PROMPT)


# ==== PROZESSFUNKTIONEN
def process_table(table_name, phase="phase1", translate_english=False):
    try:
        print(f"Start Verarbeitung Tabelle: {table_name}")
        df = get_sample_data(table_name)
        is_empty = df.empty
        column_metadata = get_column_metadata(table_name)
        relations = get_table_relations(table_name)
        ddl_constraints = get_ddl_constraints(table_name)
        temp_tote = is_temporary_trivial_table(
            table_name, df if not is_empty else None, column_metadata, relations
        )
        priority = (
            "low"
            if temp_tote
            else determine_table_priority(table_name, column_metadata, relations)
        )

        if not is_empty:
            semantic_types = {}
            anonymized_columns = {}
            for column in df.columns:
                semantic_type = identify_column_type(column, df[column], table_name)
                semantic_types[column] = semantic_type
                if semantic_type != "regular":
                    anonymized_columns[column] = df[column].apply(
                        lambda x: generate_anonymized_example(x, semantic_type)
                    )
                else:
                    anonymized_columns[column] = df[column]
            anonymized_df = pd.DataFrame(anonymized_columns)
        else:
            semantic_types = {
                col: identify_column_type(col, None, table_name)
                for col in column_metadata.keys()
            }

        sample = []
        if not is_empty:
            sample = anonymized_df.fillna("").to_dict(orient="records")
            for row in sample:
                for k, v in row.items():
                    row[k] = v

        columns_with_metadata = []
        for col_name, meta in column_metadata.items():
            mapped_sem_type = None
            if table_name.upper() in SPECIAL_KUERZEL_FIELDS:
                mapped_sem_type = SPECIAL_KUERZEL_FIELDS[table_name.upper()].get(
                    col_name.upper()
                )
            if not mapped_sem_type:
                mapped_sem_type = semantic_types.get(col_name, "regular")
            if translate_english and meta.get("description"):
                meta["description"] = translate_to_german(meta["description"])
            col_data = {
                "name": col_name,
                **meta,
                "semantic_type": mapped_sem_type,
                "example_values": (
                    [str(row.get(col_name, "")) for row in sample[:3]]
                    if not is_empty and sample
                    else []
                ),
            }
            columns_with_metadata.append(col_data)

        use_cases = typical_use_cases(table_name, columns_with_metadata, relations)
        sample_queries = typical_queries(table_name, columns_with_metadata, relations)

        prompt = prompt_template.format_messages(
            table_name=table_name,
            columns=json.dumps(columns_with_metadata, ensure_ascii=False, default=str),
            examples=json.dumps(sample, indent=2, ensure_ascii=False, default=str),
            relation_info=json.dumps(relations, ensure_ascii=False, default=str),
            ddl_constraints=json.dumps(
                ddl_constraints, ensure_ascii=False, default=str
            ),
            is_empty=str(is_empty).lower(),
            priority=priority,
            use_cases=json.dumps(use_cases, ensure_ascii=False),
            sample_queries=json.dumps(sample_queries, ensure_ascii=False),
        )

        response = safe_llm_call(prompt, table_name)
        if response is None:
            return False, f"⏩ SKIP {table_name} wegen zu großem Prompt"

        output_yaml = response.content
        is_valid, cleaned_yaml = validate_yaml(output_yaml)

        if is_valid:
            output_file = yaml_output_dir / f"{table_name}.yaml"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(cleaned_yaml)

            status_msg = f"✅ YAML generiert für: {table_name}"
            if is_empty:
                status_msg = f"ℹ️ YAML generiert für leere Tabelle: {table_name} (Priorität: {priority})"
            if temp_tote:
                status_msg += " (automatisch als temporär/tote Tabelle erkannt!)"

            status.tables_generated += 1
            if phase == "phase1":
                status.tables_in_phase1 += 1
            else:
                status.tables_in_phase2 += 1
            status.generated_details[table_name] = phase
            status.save()

            return True, status_msg
        else:
            return False, f"⚠️ YAML ungültig für {table_name}: {cleaned_yaml}"
    except Exception as e:
        error_msg = f"Fehler bei Tabelle {table_name}: {str(e)}"
        print(error_msg)
        log_message(error_msg, "error")
        return False, f"❌ FEHLER: {str(e)}"


def get_all_procedures() -> List[str]:
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT rdb$procedure_name FROM rdb$procedures")
            return [row[0].strip() for row in cur.fetchall()]
    except Exception as e:
        log_message(f"Fehler beim Abrufen aller Prozeduren: {e}", "error")
        return []


def get_procedure_info(procedure_name: str) -> Dict:
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT rp.RDB$PROCEDURE_NAME, rp.RDB$DESCRIPTION
                FROM RDB$PROCEDURES rp
                WHERE rp.RDB$PROCEDURE_NAME = ?
            """,
                (procedure_name,),
            )
            row = cur.fetchone()
            if not row:
                return {}

            cur.execute(
                """
                SELECT rf.RDB$PARAMETER_NAME, rf.RDB$PARAMETER_TYPE, f.RDB$FIELD_TYPE, f.RDB$FIELD_LENGTH
                FROM RDB$PROCEDURE_PARAMETERS rf
                  JOIN RDB$FIELDS f ON rf.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
                WHERE rf.RDB$PROCEDURE_NAME = ?
                ORDER BY rf.RDB$PARAMETER_TYPE, rf.RDB$PARAMETER_NUMBER
            """,
                (procedure_name,),
            )

            params = [
                {
                    "name": p[0].strip(),
                    "mode": "IN" if p[1] == 0 else "OUT",
                    "type": str(p[2]),
                    "length": p[3],
                }
                for p in cur.fetchall()
            ]

            input_params = [p for p in params if p["mode"] == "IN"]
            output_params = [p for p in params if p["mode"] == "OUT"]

            return {
                "name": row[0].strip(),
                "description": convert_win1252_to_utf8(row[1]) if row[1] else "",
                "inputs": input_params,
                "outputs": output_params,
            }
    except Exception as e:
        log_message(
            f"Fehler beim Abrufen der Prozedurinfos für {procedure_name}: {e}", "error"
        )
        return {}


def process_procedure(proc_name, phase="phase1"):
    try:
        print(f"Start Verarbeitung Prozedur: {proc_name}")
        proc_info = get_procedure_info(proc_name)
        if not proc_info:
            return False, f"⚠️ Keine Infos für Prozedur: {proc_name}"

        columns = []
        for param in proc_info.get("inputs", []) + proc_info.get("outputs", []):
            columns.append(
                {
                    "name": param["name"],
                    "type": param["type"],
                    "nullable": False,
                    "description": f"{param['mode']}-Parameter für {proc_info['name']}",
                    "semantic_type": "parameter",
                    "example_values": [],
                }
            )

        max_cols_per_prompt = 60
        overlap = 10
        blocks = []

        if len(columns) <= max_cols_per_prompt:
            blocks = [columns]
        else:
            log_message(
                f"Prozedur {proc_info['name']} hat {len(columns)} Parameter, splitte auf Blöcke.",
                "info",
            )
            for start in range(0, len(columns), max_cols_per_prompt - overlap):
                block = columns[start : start + max_cols_per_prompt]
                blocks.append(block)

        yaml_outputs = []

        for chunk_idx, cols_chunk in enumerate(blocks):
            prompt = prompt_template.format_messages(
                table_name=proc_info["name"]
                + (f"_block{chunk_idx+1}" if len(blocks) > 1 else ""),
                columns=json.dumps(cols_chunk, ensure_ascii=False),
                examples="[]",
                relation_info="[]",
                ddl_constraints=json.dumps({}, ensure_ascii=False),
                is_empty="false",
                priority="high",
                use_cases=json.dumps(
                    [
                        "Aufruf der Prozedur im Geschäftsprozess",
                        "Integration mit Frontend-Anwendungen",
                        "Automatisierte Datenverarbeitung",
                    ],
                    ensure_ascii=False,
                ),
                sample_queries=json.dumps(
                    [
                        "Wie rufe ich die Prozedur auf?",
                        "Welche Parameter erwartet die Prozedur?",
                        "Was gibt die Prozedur zurück?",
                    ],
                    ensure_ascii=False,
                ),
            )

            response = safe_llm_call(
                prompt,
                f"{proc_info['name']} Block {chunk_idx+1}",
                item_type="procedure",
            )

            if response is None:
                print(
                    f"⏩ SKIP Prozedur {proc_info['name']} Block {chunk_idx+1} (Prompt zu groß)"
                )
                continue

            output_yaml = response.content
            is_valid, cleaned_yaml = validate_yaml(output_yaml)

            if not is_valid:
                log_message(
                    f"YAML ungültig für Prozedur {proc_info['name']} Block {chunk_idx+1}: {cleaned_yaml}",
                    "error",
                )
                continue

            try:
                yaml_obj = yaml.safe_load(cleaned_yaml)
                yaml_outputs.append(yaml_obj)
            except Exception as e:
                log_message(f"YAML-Parsing-Fehler: {e}", "error")
                continue

        if not yaml_outputs:
            return (
                False,
                f"⚠️ Keine gültigen Chunks für Prozedur {proc_info['name']}, übersprungen.",
            )

        merged_yaml = merge_yaml_outputs(yaml_outputs)
        out_file = yaml_output_dir / f"{proc_info['name']}_procedure.yaml"
        out_file.parent.mkdir(parents=True, exist_ok=True)

        with open(out_file, "w", encoding="utf-8") as f:
            yaml.dump(merged_yaml, f, allow_unicode=True, sort_keys=False)

        status.procedures_generated += 1
        if phase == "phase1":
            status.procedures_in_phase1 += 1
        else:
            status.procedures_in_phase2 += 1
        status.generated_details[proc_info["name"] + "_procedure"] = phase
        status.save()

        return (
            True,
            f"✅ YAML für Prozedur {proc_info['name']} generiert (Chunking/merged)",
        )
    except Exception as e:
        error_msg = f"Fehler bei Prozedur {proc_name}: {str(e)}"
        print(error_msg)
        log_message(error_msg, "error")
        return False, f"❌ FEHLER: {str(e)}"


def load_existing_yaml_dict():
    result = {}
    if yaml_output_dir.exists():
        for file_path in yaml_output_dir.glob("*.yaml"):
            if "_procedure.yaml" in str(file_path):
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    table_data = yaml.safe_load(f)
                table_name = table_data.get("table_name", file_path.stem)
                result[table_name] = table_data
            except Exception as e:
                print(f"Fehler beim Laden von {file_path}: {e}")
    return result


def generate_yaml_batch(
    existing_yamls={},
    force_regenerate=False,
    phase="phase1",
    table_subset=None,
    translate_english=False,
):
    try:
        all_tables = get_all_tables()
        if table_subset:
            tables_to_process = [table for table in all_tables if table in table_subset]
        else:
            tables_to_process = all_tables

        tables_count = len(tables_to_process)
        completed = 0
        skipped = 0
        success = 0

        for table in tables_to_process:
            yaml_path = yaml_output_dir / f"{table}.yaml"

            # Überprüfe, ob die Tabelle bereits in Phase 2 ist und wir aktuell in Phase 2 sind
            already_in_phase2 = (
                phase == "phase2"
                and table in status.generated_details
                and status.generated_details[table] == "phase2"
            )

            if already_in_phase2:
                completed += 1
                log_message(
                    f"⏭️ Überspringe Tabelle bereits in Phase 2: {table} ({completed}/{tables_count})"
                )
                continue

            if (
                yaml_path.exists()
                and not force_regenerate
                and table not in existing_yamls
            ):
                completed += 1
                log_message(
                    f"⏭️ Überspringe existierende Tabelle: {table} ({completed}/{tables_count})"
                )
                continue

            success_flag, message = process_table(
                table, phase=phase, translate_english=translate_english
            )
            log_message(message)

            completed += 1
            if success_flag:
                success += 1
            else:
                skipped += 1

            print(
                f"Fortschritt: {completed}/{tables_count} Tabellen ({success} erfolgreich, {skipped} übersprungen)"
            )

        log_message(
            f"Batch abgeschlossen: {success} generiert, {skipped} übersprungen", "info"
        )
        return success, skipped
    except Exception as e:
        log_message(f"Fehler im Batch-Prozess: {str(e)}", "error")
        return 0, 0


def generate_all_procedure_yaml(phase="phase1"):
    try:
        procs = get_all_procedures()
        total = len(procs)
        success = 0
        failures = 0

        for i, proc_name in enumerate(procs, 1):
            yaml_path = yaml_output_dir / f"{proc_name}_procedure.yaml"

            # Überprüfe, ob die Prozedur bereits in Phase 2 ist und wir aktuell in Phase 2 sind
            proc_key = f"{proc_name}_procedure"
            already_in_phase2 = (
                phase == "phase2"
                and proc_key in status.generated_details
                and status.generated_details[proc_key] == "phase2"
            )

            if already_in_phase2:
                log_message(
                    f"⏭️ Überspringe Prozedur bereits in Phase 2: {proc_name} ({i}/{total})"
                )
                continue

            if yaml_path.exists():
                log_message(
                    f"⏭️ Überspringe existierende Prozedur: {proc_name} ({i}/{total})"
                )
                continue

            success_flag, msg = process_procedure(proc_name, phase=phase)

            if success_flag:
                success += 1
            else:
                failures += 1

            log_message(f"{msg} ({i}/{total})")

        log_message(
            f"Prozedur-Batch abgeschlossen: {success} generiert, {failures} übersprungen/fehlgeschlagen"
        )
        return success, failures
    except Exception as e:
        log_message(f"Fehler im Prozedur-Batch-Prozess: {str(e)}", "error")
        return 0, 0


def create_index_file():
    try:
        ensure_dir(schema_output_dir)
        index_file = schema_output_dir / "index.md"

        # Debug-Ausgabe
        yaml_files_count = len(list(yaml_output_dir.glob("*.yaml")))
        log_message(f"Gefundene YAML-Dateien: {yaml_files_count}", "info")

        with open(index_file, "w", encoding="utf-8") as f:
            f.write("# Wincasa - Datenbankdokumentation\n\n")
            f.write("## Inhaltsverzeichnis\n\n")
            f.write("### Tabellen\n\n")

            yamls = []
            for yaml_file in yaml_output_dir.glob("*.yaml"):
                if "_procedure" not in yaml_file.stem:
                    try:
                        with open(yaml_file, "r", encoding="utf-8") as yf:
                            yaml_content = yf.read()
                            data = yaml.safe_load(yaml_content)
                            priority = data.get("priority", "medium")
                            is_empty = data.get("is_empty", False)
                            description = data.get("description", "").strip()
                            description = (
                                description[:100] + "..."
                                if len(description) > 100
                                else description
                            )
                            if not description:
                                description = f"Tabelle {yaml_file.stem}"
                            yamls.append(
                                {
                                    "name": yaml_file.stem,
                                    "priority": priority,
                                    "is_empty": is_empty,
                                    "description": description,
                                }
                            )
                            log_message(
                                f"Tabelle {yaml_file.stem} erfolgreich verarbeitet",
                                "info",
                                save_status=False,
                            )
                    except Exception as e:
                        log_message(
                            f"Fehler beim Verarbeiten von {yaml_file.stem}: {str(e)}",
                            "warning",
                            save_status=False,
                        )
                        yamls.append(
                            {
                                "name": yaml_file.stem,
                                "priority": "unknown",
                                "is_empty": False,
                                "description": f"Tabelle {yaml_file.stem}",
                            }
                        )

            # Sortiere nach Priority und Name
            def priority_sort(item):
                priority_map = {"high": 0, "medium": 1, "low": 2, "unknown": 3}
                return (priority_map.get(item["priority"], 4), item["name"])

            yamls.sort(key=priority_sort)

            for item in yamls:
                priority_emoji = (
                    "🔴"
                    if item["priority"] == "high"
                    else "🟠" if item["priority"] == "medium" else "🟢"
                )
                empty_flag = " (leer)" if item["is_empty"] else ""
                f.write(
                    f"- {priority_emoji} [{item['name']}]({item['name']}.md){empty_flag} - {item['description']}\n"
                )

            f.write("\n### Prozeduren\n\n")

            procedures = []
            for yaml_file in yaml_output_dir.glob("*_procedure.yaml"):
                name = yaml_file.stem.replace("_procedure", "")
                try:
                    with open(yaml_file, "r", encoding="utf-8") as yf:
                        yaml_content = yf.read()
                        data = yaml.safe_load(yaml_content)
                        description = data.get("description", "").strip()
                        description = (
                            description[:100] + "..."
                            if len(description) > 100
                            else description
                        )
                        if not description:
                            description = f"Prozedur {name}"
                        procedures.append({"name": name, "description": description})
                        log_message(
                            f"Prozedur {name} erfolgreich verarbeitet",
                            "info",
                            save_status=False,
                        )
                except Exception as e:
                    log_message(
                        f"Fehler beim Verarbeiten von Prozedur {name}: {str(e)}",
                        "warning",
                        save_status=False,
                    )
                    procedures.append({"name": name, "description": f"Prozedur {name}"})

            procedures.sort(key=lambda x: x["name"])

            for item in procedures:
                f.write(
                    f"- [{item['name']}]({item['name']}_proc.md) - {item['description']}\n"
                )

        # Erstelle Markdown-Dateien für jede Tabelle und Prozedur
        for yaml_file in yaml_output_dir.glob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as yf:
                    data = yaml.safe_load(yf)

                    if "_procedure" in yaml_file.stem:
                        # Prozedur
                        name = yaml_file.stem.replace("_procedure", "")
                        md_file = schema_output_dir / f"{name}_proc.md"
                        with open(md_file, "w", encoding="utf-8") as f:
                            f.write(f"# Prozedur: {name}\n\n")
                            f.write(
                                f"## Beschreibung\n\n{data.get('description', '')}\n\n"
                            )
                            f.write(
                                f"## Geschäftskontext\n\n{data.get('business_context', '')}\n\n"
                            )
                            f.write("## Parameter\n\n")

                            if "columns" in data and data["columns"]:
                                f.write("| Name | Typ | Richtung | Beschreibung |\n")
                                f.write("|------|-----|----------|-------------|\n")
                                for col in data["columns"]:
                                    desc = col.get("description", "").replace("\n", " ")
                                    direction = (
                                        "Eingang"
                                        if "IN-" in desc
                                        else "Ausgang" if "OUT-" in desc else "-"
                                    )
                                    f.write(
                                        f"| {col.get('name', '')} | {col.get('type', '')} | {direction} | {desc} |\n"
                                    )
                            else:
                                f.write("_Keine Parameter dokumentiert_\n")

                            if (
                                "business_examples" in data
                                and data["business_examples"]
                            ):
                                f.write(
                                    "\n## Beispiele für die geschäftliche Verwendung\n\n"
                                )
                                for ex in data["business_examples"]:
                                    f.write(f"- {ex}\n")
                    else:
                        # Tabelle
                        name = yaml_file.stem
                        md_file = schema_output_dir / f"{name}.md"
                        with open(md_file, "w", encoding="utf-8") as f:
                            priority = data.get("priority", "medium")
                            priority_emoji = (
                                "🔴"
                                if priority == "high"
                                else "🟠" if priority == "medium" else "🟢"
                            )

                            f.write(f"# Tabelle: {name} {priority_emoji}\n\n")
                            f.write(
                                f"## Beschreibung\n\n{data.get('description', '')}\n\n"
                            )
                            f.write(
                                f"## Geschäftskontext\n\n{data.get('business_context', '')}\n\n"
                            )

                            if data.get("internal_conventions"):
                                f.write(
                                    f"## Interne Konventionen\n\n{data.get('internal_conventions', '')}\n\n"
                                )

                            f.write("## Spalten\n\n")
                            if "columns" in data and data["columns"]:
                                f.write("| Name | Typ | Nullable | Beschreibung |\n")
                                f.write("|------|-----|----------|-------------|\n")
                                for col in data["columns"]:
                                    nullable = (
                                        "Ja" if col.get("nullable", True) else "Nein"
                                    )
                                    desc = col.get("description", "").replace("\n", " ")
                                    f.write(
                                        f"| {col.get('name', '')} | {col.get('type', '')} | {nullable} | {desc} |\n"
                                    )
                            else:
                                f.write("_Keine Spalten dokumentiert_\n")

                            if "relations" in data and data["relations"]:
                                f.write("\n## Beziehungen\n\n")

                                if isinstance(data["relations"], dict):
                                    # Write foreign keys
                                    if (
                                        "foreign_keys" in data["relations"]
                                        and data["relations"]["foreign_keys"]
                                    ):
                                        f.write("### Fremdschlüssel\n\n")
                                        f.write("| Spalte | Referenziert |\n")
                                        f.write("|--------|-------------|\n")
                                        for fk in data["relations"]["foreign_keys"]:
                                            if isinstance(fk, dict):
                                                # Dictionary-Format
                                                f.write(
                                                    f"| {fk.get('field', '')} | {fk.get('references_table', '')}({fk.get('references_field', '')}) |\n"
                                                )
                                            elif isinstance(fk, str):
                                                # String-Format: "FIELD -> TABLE(FIELD)"
                                                parts = fk.split("->")
                                                if len(parts) == 2:
                                                    from_field = parts[0].strip()
                                                    to_part = parts[1].strip()
                                                    # Extrahiere TABLE(FIELD)
                                                    match = re.search(
                                                        r"(\w+)\((\w+)\)", to_part
                                                    )
                                                    if match:
                                                        to_table = match.group(1)
                                                        to_field = match.group(2)
                                                        f.write(
                                                            f"| {from_field} | {to_table}({to_field}) |\n"
                                                        )
                                                    else:
                                                        f.write(
                                                            f"| {from_field} | {to_part} |\n"
                                                        )

                                    # Write references
                                    if (
                                        "referenced_by" in data["relations"]
                                        and data["relations"]["referenced_by"]
                                    ):
                                        f.write("\n### Referenziert von\n\n")
                                        f.write("| Tabelle | Spalte | Via |\n")
                                        f.write("|---------|--------|-----|\n")
                                        for ref in data["relations"]["referenced_by"]:
                                            if isinstance(ref, dict):
                                                # Dictionary-Format
                                                f.write(
                                                    f"| {ref.get('table', '')} | {ref.get('field', '')} | {ref.get('via_field', '')} |\n"
                                                )
                                            elif isinstance(ref, str):
                                                # String-Format: Möglicherweise "TABLE.FIELD"
                                                parts = ref.split(".")
                                                if len(parts) == 2:
                                                    ref_table = parts[0].strip()
                                                    ref_field = parts[1].strip()
                                                    f.write(
                                                        f"| {ref_table} | {ref_field} | - |\n"
                                                    )
                                                else:
                                                    f.write(f"| {ref} | - | - |\n")
                                else:
                                    # Simple list format
                                    f.write(
                                        "\n".join(
                                            [f"- {rel}" for rel in data["relations"]]
                                        )
                                    )

                            if "common_queries" in data and data["common_queries"]:
                                f.write("\n## Typische Abfragen\n\n")
                                for query in data["common_queries"]:
                                    f.write(f"- {query}\n")

                            if (
                                "business_examples" in data
                                and data["business_examples"]
                            ):
                                f.write("\n## Geschäftsbeispiele\n\n")
                                for ex in data["business_examples"]:
                                    f.write(f"- {ex}\n")
            except Exception as e:
                print(f"Fehler beim Verarbeiten von {yaml_file}: {e}")

        status.schema_generated = True
        status.save()
        # Gib die Anzahl der verarbeiteten Tabellen und Prozeduren zurück
        return (
            True,
            f"Indexdatei erstellt mit {len(yamls)} Tabellen und {len(procedures)} Prozeduren.",
        )
    except Exception as e:
        log_message(f"Fehler beim Erstellen der Indexdatei: {e}", "error")
        return False, f"Fehler: {e}"


def create_database_overview():
    try:
        ensure_dir(schema_output_dir)
        overview_file = schema_output_dir / "db_overview.md"
        dot_file = schema_output_dir / "db_diagram.dot"

        # Sammle Tabellen und Beziehungen
        tables = {}
        relationships = []

        for yaml_file in yaml_output_dir.glob("*.yaml"):
            if "_procedure" in yaml_file.stem:
                continue

            try:
                with open(yaml_file, "r", encoding="utf-8") as yf:
                    data = yaml.safe_load(yf)
                    table_name = yaml_file.stem
                    tables[table_name] = {
                        "name": table_name,
                        "description": data.get("description", ""),
                        "priority": data.get("priority", "medium"),
                        "is_empty": data.get("is_empty", False),
                        "columns": data.get("columns", []),
                    }

                    # Extrahiere Beziehungen
                    if "relations" in data and isinstance(data["relations"], dict):
                        if "foreign_keys" in data["relations"]:
                            for fk in data["relations"]["foreign_keys"]:
                                if isinstance(fk, dict):
                                    # Dictionary-Format
                                    relationships.append(
                                        {
                                            "from": table_name,
                                            "to": fk.get("references_table", ""),
                                            "label": (
                                                f"{fk.get('field', '')} → {fk.get('references_field', '')}"
                                            ),
                                        }
                                    )
                                elif isinstance(fk, str):
                                    # String-Format: "FIELD -> TABLE(FIELD)"
                                    parts = fk.split("->")
                                    if len(parts) == 2:
                                        from_field = parts[0].strip()
                                        to_part = parts[1].strip()
                                        # Extrahiere TABLE(FIELD)
                                        match = re.search(r"(\w+)\((\w+)\)", to_part)
                                        if match:
                                            to_table = match.group(1)
                                            to_field = match.group(2)
                                            relationships.append(
                                                {
                                                    "from": table_name,
                                                    "to": to_table,
                                                    "label": (
                                                        f"{from_field} → {to_field}"
                                                    ),
                                                }
                                            )
            except Exception as e:
                print(f"Fehler beim Laden von {yaml_file}: {e}")

        # Erstelle Markdown-Übersicht
        with open(overview_file, "w", encoding="utf-8") as f:
            f.write("# Datenbankübersicht\n\n")

            # Tabellen nach Priorität
            f.write("## Tabellen nach Priorität\n\n")
            f.write("### Hochprioritätstabellen 🔴\n\n")
            high_priority = [t for t in tables.values() if t["priority"] == "high"]
            for t in sorted(high_priority, key=lambda x: x["name"]):
                f.write(
                    f"- [{t['name']}]({t['name']}.md): {t['description'][:80]}...\n"
                )

            f.write("\n### Mittlere Priorität 🟠\n\n")
            med_priority = [t for t in tables.values() if t["priority"] == "medium"]
            for t in sorted(med_priority, key=lambda x: x["name"]):
                f.write(
                    f"- [{t['name']}]({t['name']}.md): {t['description'][:80]}...\n"
                )

            f.write("\n### Niedrige Priorität 🟢\n\n")
            low_priority = [t for t in tables.values() if t["priority"] == "low"]
            for t in sorted(low_priority, key=lambda x: x["name"]):
                f.write(
                    f"- [{t['name']}]({t['name']}.md): {t['description'][:80]}...\n"
                )

            # Tabellenstatistik
            f.write("\n## Statistik\n\n")
            f.write(f"- Gesamtanzahl Tabellen: {len(tables)}\n")
            f.write(f"- Hochprioritätstabellen: {len(high_priority)}\n")
            f.write(f"- Mittlere Priorität: {len(med_priority)}\n")
            f.write(f"- Niedrige Priorität: {len(low_priority)}\n")
            f.write(
                f"- Leere Tabellen: {len([t for t in tables.values() if t['is_empty']])}\n"
            )
            f.write(f"- Beziehungen: {len(relationships)}\n")

            # Beziehungen
            f.write("\n## Wichtige Beziehungen\n\n")
            f.write("| Von | Zu | Spalten |\n")
            f.write("|-----|----|---------|\n")

            # Filtern wir auf wichtige Beziehungen (High-Prio-Tabellen)
            high_prio_names = [t["name"] for t in high_priority]
            important_rels = [
                r
                for r in relationships
                if r["from_table"] in high_prio_names
                and r["to_table"] in high_prio_names
            ]

            for rel in sorted(
                important_rels, key=lambda x: (x["from_table"], x["to_table"])
            ):
                f.write(
                    f"| [{rel['from_table']}]({rel['from_table']}.md) | [{rel['to_table']}]({rel['to_table']}.md) | {rel['from_column']} → {rel['to_column']} |\n"
                )

        # Erstelle DOT-Datei für Graphviz
        with open(dot_file, "w", encoding="utf-8") as f:
            f.write("digraph database {\n")
            f.write('  graph [rankdir=LR, fontname="Helvetica", nodesep=0.8];\n')
            f.write('  node [shape=record, fontname="Helvetica", fontsize=10];\n')
            f.write('  edge [fontname="Helvetica", fontsize=9];\n\n')

            # Knoten für Tabellen
            for table_name, table in tables.items():
                color = (
                    "crimson"
                    if table["priority"] == "high"
                    else "darkorange" if table["priority"] == "medium" else "green3"
                )
                style = "filled" if not table["is_empty"] else "filled,dashed"
                label = f"{table_name}"
                f.write(
                    f'  "{table_name}" [label="{label}", style="{style}", fillcolor="{color}", fontcolor="white"];\n'
                )

            # Kanten für Beziehungen
            for rel in relationships:
                f.write(
                    f"  \"{rel['from_table']}\" -> \"{rel['to_table']}\" [label=\"{rel['from_column']} → {rel['to_column']}\"];\n"
                )

            f.write("}\n")

        # Generiere Cluster-Diagramm für High-Prio-Tabellen
        high_prio_dot_file = schema_output_dir / "high_prio_diagram.dot"
        with open(high_prio_dot_file, "w", encoding="utf-8") as f:
            f.write("digraph high_priority {\n")
            f.write('  graph [rankdir=LR, fontname="Helvetica", nodesep=0.8];\n')
            f.write('  node [shape=record, fontname="Helvetica", fontsize=10];\n')
            f.write('  edge [fontname="Helvetica", fontsize=9];\n\n')

            # Nur High-Prio-Tabellen
            for table_name in high_prio_names:
                f.write(
                    f'  "{table_name}" [label="{table_name}", style="filled", fillcolor="crimson", fontcolor="white"];\n'
                )

            # Nur Beziehungen zwischen High-Prio-Tabellen
            for rel in important_rels:
                f.write(
                    f"  \"{rel['from_table']}\" -> \"{rel['to_table']}\" [label=\"{rel['from_column']}\"];\n"
                )

            f.write("}\n")

        return True, "Datenbank-Übersicht und Diagramm generiert."
    except Exception as e:
        log_message(f"Fehler beim Erstellen der Datenbankübersicht: {e}", "error")
        return False, f"Fehler: {e}"


def generate_relation_report():
    try:
        ensure_dir(schema_output_dir)
        relations_file = schema_output_dir / "relation_report.md"
        clusters_file = schema_output_dir / "table_clusters.md"

        # Sammle alle Beziehungen
        all_tables = set()
        relationships = []

        for yaml_file in yaml_output_dir.glob("*.yaml"):
            if "_procedure" in yaml_file.stem:
                continue

            try:
                with open(yaml_file, "r", encoding="utf-8") as yf:
                    data = yaml.safe_load(yf)
                    table_name = yaml_file.stem
                    all_tables.add(table_name)

                    # Extrahiere Beziehungen
                    if "relations" in data and isinstance(data["relations"], dict):
                        if "foreign_keys" in data["relations"]:
                            for fk in data["relations"]["foreign_keys"]:
                                # Unterstütze beide Formate: Dictionary und String
                                if isinstance(fk, dict):
                                    # Dictionary-Format: {"field": "X", "references_table": "Y", "references_field": "Z"}
                                    ref_table = fk.get("references_table", "")
                                    if ref_table:  # Nur gültige Referenzen
                                        relationships.append(
                                            {
                                                "from_table": table_name,
                                                "from_column": fk.get("field", ""),
                                                "to_table": ref_table,
                                                "to_column": fk.get(
                                                    "references_field", ""
                                                ),
                                            }
                                        )
                                        all_tables.add(ref_table)
                                elif isinstance(fk, str):
                                    # String-Format: "FIELD -> TABLE(FIELD)"
                                    parts = fk.split("->")
                                    if len(parts) == 2:
                                        from_column = parts[0].strip()
                                        to_part = parts[1].strip()
                                        # Extrahiere TABLE(FIELD)
                                        match = re.search(r"(\w+)\((\w+)\)", to_part)
                                        if match:
                                            to_table = match.group(1)
                                            to_column = match.group(2)
                                            relationships.append(
                                                {
                                                    "from_table": table_name,
                                                    "from_column": from_column,
                                                    "to_table": to_table,
                                                    "to_column": to_column,
                                                }
                                            )
                                            all_tables.add(to_table)
            except Exception as e:
                print(f"Fehler beim Laden von {yaml_file}: {e}")

        # Erstelle Graph für Clusteranalyse
        table_connections = {}
        for table in all_tables:
            table_connections[table] = []

        for rel in relationships:
            from_table = rel["from_table"]
            to_table = rel["to_table"]
            if from_table in table_connections:
                table_connections[from_table].append(to_table)
            if to_table in table_connections:
                table_connections[to_table].append(from_table)

        # Identifiziere Cluster (zusammenhängende Komponenten)
        def dfs(node, visited, component):
            visited.add(node)
            component.append(node)
            for neighbor in table_connections.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, visited, component)

        visited = set()
        clusters = []

        for table in all_tables:
            if table not in visited:
                component = []
                dfs(table, visited, component)
                clusters.append(sorted(component))

        # Sortiere nach Größe (größte zuerst)
        clusters.sort(key=len, reverse=True)

        # Generiere Bericht
        with open(relations_file, "w", encoding="utf-8") as f:
            f.write("# Beziehungsbericht\n\n")

            f.write("## Übersicht\n\n")
            f.write(f"- Anzahl Tabellen: {len(all_tables)}\n")
            f.write(f"- Anzahl Beziehungen: {len(relationships)}\n")
            f.write(f"- Anzahl Cluster: {len(clusters)}\n\n")

            # Finde die Tabellen mit den meisten Beziehungen
            table_rel_count = {}
            for table in all_tables:
                inbound = len([r for r in relationships if r["to_table"] == table])
                outbound = len([r for r in relationships if r["from_table"] == table])
                table_rel_count[table] = {
                    "in": inbound,
                    "out": outbound,
                    "total": inbound + outbound,
                }

            hub_tables = sorted(
                table_rel_count.items(), key=lambda x: x[1]["total"], reverse=True
            )[:15]

            f.write("## Top-Verbindungstabellen\n\n")
            f.write("| Tabelle | Eingehend | Ausgehend | Gesamt |\n")
            f.write("|---------|-----------|-----------|--------|\n")
            for table, counts in hub_tables:
                f.write(
                    f"| [{table}]({table}.md) | {counts['in']} | {counts['out']} | {counts['total']} |\n"
                )

            f.write("\n## Alle Beziehungen\n\n")
            f.write("| Von | Zu | Spalten |\n")
            f.write("|-----|----|---------|\n")

            for rel in sorted(
                relationships, key=lambda x: (x["from_table"], x["to_table"])
            ):
                f.write(
                    f"| [{rel['from_table']}]({rel['from_table']}.md) | [{rel['to_table']}]({rel['to_table']}.md) | {rel['from_column']} → {rel['to_column']} |\n"
                )

        # Erstelle Clusterbericht
        with open(clusters_file, "w", encoding="utf-8") as f:
            f.write("# Tabellencluster-Analyse\n\n")
            f.write(
                "Diese Analyse gruppiert Tabellen basierend auf ihren Beziehungen zueinander.\n"
            )
            f.write(
                "Tabellen im selben Cluster sind durch Beziehungen (direkt oder indirekt) miteinander verbunden.\n\n"
            )

            f.write("## Identifizierte Cluster\n\n")

            for i, cluster in enumerate(clusters, 1):
                size = len(cluster)
                if size > 50:
                    desc = "Hauptcluster (Kernsystem)"
                elif size > 20:
                    desc = "Großes Teilsystem"
                elif size > 10:
                    desc = "Mittleres Teilsystem"
                elif size > 3:
                    desc = "Kleines Teilsystem"
                else:
                    desc = "Isolierte Tabellenfamilie"

                f.write(f"### Cluster {i}: {desc} ({size} Tabellen)\n\n")

                # Bei großen Clustern nur die wichtigsten Tabellen zeigen
                if size > 20:
                    # Finde die 10 am stärksten vernetzten Tabellen in diesem Cluster
                    cluster_hubs = sorted(
                        [
                            (t, table_rel_count[t]["total"])
                            for t in cluster
                            if t in table_rel_count
                        ],
                        key=lambda x: x[1],
                        reverse=True,
                    )[:10]

                    f.write("**Zentrale Tabellen:**\n\n")
                    for table, count in cluster_hubs:
                        f.write(f"- [{table}]({table}.md) ({count} Verbindungen)\n")
                    f.write(f"\n**Und {size-10} weitere Tabellen...**\n\n")
                else:
                    for table in cluster:
                        count = table_rel_count.get(table, {}).get("total", 0)
                        f.write(f"- [{table}]({table}.md) ({count} Verbindungen)\n")

                f.write("\n")

            # Erstelle Cluster-Diagramm für jeden großen Cluster
            for i, cluster in enumerate(
                clusters[:3], 1
            ):  # Beschränke auf die 3 größten Cluster
                cluster_dot_file = schema_output_dir / f"cluster_{i}_diagram.dot"
                with open(cluster_dot_file, "w", encoding="utf-8") as df:
                    df.write(f"digraph cluster_{i} {{\n")
                    df.write(
                        '  graph [rankdir=LR, fontname="Helvetica", nodesep=0.8];\n'
                    )
                    df.write(
                        '  node [shape=record, fontname="Helvetica", fontsize=10];\n'
                    )
                    df.write('  edge [fontname="Helvetica", fontsize=9];\n\n')

                    # Knoten
                    for table in cluster:
                        count = table_rel_count.get(table, {}).get("total", 0)
                        size = 1.0 + min(
                            count / 10, 2.0
                        )  # Größere Knoten für stärker vernetzte Tabellen
                        df.write(
                            f'  "{table}" [label="{table}", width={size}, height={size}, style="filled", fillcolor="skyblue"];\n'
                        )

                    # Kanten
                    for rel in relationships:
                        if rel["from_table"] in cluster and rel["to_table"] in cluster:
                            df.write(
                                f"  \"{rel['from_table']}\" -> \"{rel['to_table']}\" [label=\"{rel['from_column']}\"];\n"
                            )

                    df.write("}\n")

            # Convert DOT files to PNG and SVG using Graphviz
            try:
                import subprocess

                for i in range(
                    1, min(4, len(clusters) + 1)
                ):  # For the 3 largest clusters or fewer if less exist
                    dot_file = schema_output_dir / f"cluster_{i}_diagram.dot"
                    if dot_file.exists():
                        png_file = schema_output_dir / f"cluster_{i}_diagram.png"
                        svg_file = schema_output_dir / f"cluster_{i}_diagram.svg"

                        # Generate PNG
                        subprocess.run(
                            ["dot", "-Tpng", str(dot_file), "-o", str(png_file)],
                            check=True,
                        )

                        # Generate SVG (for better quality and interactivity)
                        subprocess.run(
                            ["dot", "-Tsvg", str(dot_file), "-o", str(svg_file)],
                            check=True,
                        )

                        # Add links to the diagrams in the cluster report
                        with open(clusters_file, "a", encoding="utf-8") as f:
                            f.write(f"\n## Diagramm für Cluster {i}\n\n")
                            f.write(
                                f"![Cluster {i} Diagram](cluster_{i}_diagram.png)\n\n"
                            )
                            f.write(
                                f"[SVG-Version (interaktiv)](cluster_{i}_diagram.svg)\n\n"
                            )

                # Generate individual table diagrams
                generate_table_diagrams(relationships, all_tables, schema_output_dir)

                status.diagrams_generated = True
                log_message("Beziehungsdiagramme wurden erfolgreich erstellt", "info")
            except Exception as e:
                log_message(f"Fehler bei der Diagrammerstellung: {str(e)}", "warning")
                log_message(
                    "Stellen Sie sicher, dass Graphviz installiert ist (apt-get install graphviz)",
                    "info",
                )

        status.relations_analyzed = True
        status.save()
        return all_tables
    except Exception as e:
        log_message(f"Fehler bei der Beziehungsanalyse: {str(e)}", "error")
        return []


def generate_table_diagrams(relationships, tables_with_relations, output_dir):
    """
    Generiert Beziehungsdiagramme für einzelne Tabellen.

    Args:
        relationships: Liste der Beziehungen zwischen Tabellen
        tables_with_relations: Set von Tabellen mit Beziehungen
        output_dir: Ausgabeverzeichnis für die Diagramme
    """
    try:
        import shutil
        import subprocess

        # Prüfe, ob das 'dot'-Programm von Graphviz installiert ist
        dot_path = shutil.which("dot")
        if not dot_path:
            log_message(
                "Graphviz ist nicht installiert. Bitte installieren Sie es mit 'apt-get install graphviz'.",
                "error",
            )
            return

        # Erstelle ein Verzeichnis für die Tabellendiagramme
        table_diagrams_dir = output_dir / "table_diagrams"
        table_diagrams_dir.mkdir(exist_ok=True)

        # Erstelle eine Indexdatei für die Tabellendiagramme
        index_file = output_dir / "table_diagrams.md"
        with open(index_file, "w", encoding="utf-8") as f:
            f.write("# Tabellenbeziehungsdiagramme\n\n")
            f.write(
                "Diese Diagramme zeigen die direkten Beziehungen jeder Tabelle.\n\n"
            )
            f.write("| Tabelle | Anzahl Beziehungen | Diagramm |\n")
            f.write("|---------|-------------------|----------|\n")

        # Generiere Diagramm für jede Tabelle mit Beziehungen
        for table in sorted(tables_with_relations):
            # Finde alle direkten Beziehungen für diese Tabelle
            direct_relations = []
            for rel in relationships:
                if rel["from_table"] == table or rel["to_table"] == table:
                    direct_relations.append(rel)

            if not direct_relations:
                continue

            # Erstelle DOT-Datei für die Tabelle
            dot_file = table_diagrams_dir / f"{table}_relations.dot"
            with open(dot_file, "w", encoding="utf-8") as df:
                df.write(f"digraph {table}_relations {{\n")
                df.write('  graph [rankdir=LR, fontname="Helvetica"];\n')
                df.write('  node [shape=record, fontname="Helvetica", fontsize=10];\n')
                df.write('  edge [fontname="Helvetica", fontsize=9];\n\n')

                # Zentraler Knoten (die Tabelle selbst)
                df.write(
                    f'  "{table}" [label="{table}", style="filled", fillcolor="lightblue"];\n'
                )

                # Verwandte Tabellen und Kanten
                related_tables = set()
                for rel in direct_relations:
                    if rel["from_table"] == table:
                        related_tables.add(rel["to_table"])
                        df.write(
                            f"  \"{rel['to_table']}\" [label=\"{rel['to_table']}\"];\n"
                        )
                        df.write(
                            f"  \"{table}\" -> \"{rel['to_table']}\" [label=\"{rel['from_column']} → {rel['to_column']}\"];\n"
                        )
                    elif rel["to_table"] == table:
                        related_tables.add(rel["from_table"])
                        df.write(
                            f"  \"{rel['from_table']}\" [label=\"{rel['from_table']}\"];\n"
                        )
                        df.write(
                            f"  \"{rel['from_table']}\" -> \"{table}\" [label=\"{rel['from_column']} → {rel['to_column']}\"];\n"
                        )

                df.write("}\n")

            # Konvertiere zu PNG und SVG
            png_file = table_diagrams_dir / f"{table}_relations.png"
            svg_file = table_diagrams_dir / f"{table}_relations.svg"

            try:
                subprocess.run(
                    [dot_path, "-Tpng", str(dot_file), "-o", str(png_file)], check=True
                )
                subprocess.run(
                    [dot_path, "-Tsvg", str(dot_file), "-o", str(svg_file)], check=True
                )
            except subprocess.CalledProcessError as e:
                log_message(
                    f"Fehler beim Ausführen von Graphviz für {table}: {e}", "warning"
                )
                continue

            # Füge Eintrag zur Indexdatei hinzu
            with open(index_file, "a", encoding="utf-8") as f:
                rel_count = len(direct_relations)
                f.write(
                    f"| [{table}]({table}.md) | {rel_count} | [PNG](table_diagrams/{table}_relations.png) / [SVG](table_diagrams/{table}_relations.svg) |\n"
                )

        # Füge Link zur Indexdatei in den Hauptbericht ein
        with open(output_dir / "relation_report.md", "a", encoding="utf-8") as f:
            f.write("\n## Einzelne Tabellendiagramme\n\n")
            f.write("Für jede Tabelle wurde ein eigenes Beziehungsdiagramm erstellt.\n")
            f.write("[Alle Tabellendiagramme anzeigen](table_diagrams.md)\n")

        log_message(f"Tabellendiagramme wurden erfolgreich erstellt", "info")
    except Exception as e:
        log_message(
            f"Fehler bei der Erstellung der Tabellendiagramme: {str(e)}", "warning"
        )


def export_all_ddl():
    try:
        ddl_dir = ensure_dir(ddl_output_dir)
        tables = get_all_tables()
        procedures = get_all_procedures()

        # Exportiere Tabellen-DDL
        for table in tables:
            ddl = get_table_ddl(table)
            with open(ddl_dir / f"{table}_table.sql", "w", encoding="utf-8") as f:
                f.write(f"-- Tabelle: {table}\n")
                f.write(
                    f"-- Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )
                f.write(ddl)

        # Exportiere Prozeduren-DDL
        for proc in procedures:
            ddl = get_procedure_ddl(proc)
            with open(ddl_dir / f"{proc}_procedure.sql", "w", encoding="utf-8") as f:
                f.write(f"-- Prozedur: {proc}\n")
                f.write(
                    f"-- Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )
                f.write(ddl)

        # Generiere combined.sql
        with open(ddl_dir / "combined.sql", "w", encoding="utf-8") as f:
            f.write(f"-- Wincasa Datenbank DDL\n")
            f.write(f"-- Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("-- ========== TABELLEN ==========\n\n")

            for table in sorted(tables):
                f.write(f"-- Tabelle: {table}\n")
                f.write(get_table_ddl(table))
                f.write("\n\n")

            f.write("-- ========== PROZEDUREN ==========\n\n")
            for proc in sorted(procedures):
                f.write(f"-- Prozedur: {proc}\n")
                f.write(get_procedure_ddl(proc))
                f.write("\n\n")

        status.ddl_generated = True
        status.save()
        return len(tables) + len(procedures)
    except Exception as e:
        log_message(f"Fehler beim DDL-Export: {str(e)}", "error")
        return 0


# ==== SCHEMA-VORVERARBEITUNG FÜR LLM
def generate_compact_schema_description():
    """
    Generiert eine kompakte Beschreibung des Datenbankschemas mit hierarchischer Strukturierung.
    Diese Funktion erstellt eine JSON-Datei, die das gesamte Schema in strukturierter Form enthält.
    """
    try:
        ensure_dir(schema_output_dir)
        schema_file = schema_output_dir / "compact_schema.json"

        # Sammle alle Tabellen und ihre Informationen
        tables_info = {}
        table_groups = {
            "Finanzen": [],
            "Immobilien": [],
            "Personen": [],
            "Verwaltung": [],
            "Dokumente": [],
            "Sonstiges": [],
        }

        # Definiere Schlüsselwörter für die Gruppierung
        group_keywords = {
            "Finanzen": [
                "KONTO",
                "BUCHUNG",
                "SALDO",
                "ZAHLUNG",
                "BANK",
                "RUECKL",
                "UMLAGE",
                "ABRECHNUNG",
                "SOLLGEST",
            ],
            "Immobilien": [
                "OBJEKT",
                "WOHNUNG",
                "HAUS",
                "LIEGEN",
                "ZAEHLER",
                "HEIZ",
                "VERBRAUCH",
            ],
            "Personen": [
                "PERSON",
                "BEWOHNER",
                "EIGENTUEMER",
                "LIEFERAN",
                "MITARBEITER",
                "VERWALTER",
                "ADR",
            ],
            "Verwaltung": [
                "VERWALT",
                "TERMIN",
                "AUFGABE",
                "VORGANG",
                "VERSAMMLUNG",
                "BESCHLUSS",
            ],
            "Dokumente": ["DOKUMENT", "FOTO", "NACHWEIS", "VORLAGE", "ARCHIV"],
        }

        # Sammle alle Beziehungen
        all_relationships = []
        for yaml_file in yaml_output_dir.glob("*.yaml"):
            if "_procedure" in yaml_file.stem:
                continue

            try:
                with open(yaml_file, "r", encoding="utf-8") as yf:
                    data = yaml.safe_load(yf)
                    table_name = yaml_file.stem

                    # Extrahiere Beziehungen
                    if "relations" in data and isinstance(data["relations"], dict):
                        if "foreign_keys" in data["relations"]:
                            for fk in data["relations"]["foreign_keys"]:
                                # Unterstütze beide Formate: Dictionary und String
                                if isinstance(fk, dict):
                                    # Dictionary-Format
                                    ref_table = fk.get("references_table", "")
                                elif isinstance(fk, str):
                                    # String-Format: "FIELD -> TABLE(FIELD)"
                                    parts = fk.split("->")
                                    if len(parts) == 2:
                                        to_part = parts[1].strip()
                                        # Extrahiere TABLE(FIELD)
                                        match = re.search(r"(\w+)\((\w+)\)", to_part)
                                        if match:
                                            ref_table = match.group(1)
                                        else:
                                            ref_table = ""
                                    else:
                                        ref_table = ""
                                else:
                                    ref_table = ""
                                if ref_table:
                                    all_relationships.append(
                                        {
                                            "from_table": table_name,
                                            "from_column": fk.get("field", ""),
                                            "to_table": ref_table,
                                            "to_column": fk.get("references_field", ""),
                                        }
                                    )
            except Exception as e:
                log_message(
                    f"Fehler beim Laden von Beziehungen aus {yaml_file}: {e}",
                    "warning",
                    save_status=False,
                )

        # Verarbeite alle YAML-Dateien
        for yaml_file in yaml_output_dir.glob("*.yaml"):
            if "_procedure" in yaml_file.stem:
                continue

            try:
                with open(yaml_file, "r", encoding="utf-8") as yf:
                    data = yaml.safe_load(yf)
                    table_name = yaml_file.stem

                    # Extrahiere wichtige Informationen
                    description = data.get("description", "").strip()
                    business_context = data.get("business_context", "").strip()

                    # Sammle Spalteninformationen
                    columns = []
                    if "columns" in data and isinstance(data["columns"], list):
                        for col in data["columns"]:
                            if isinstance(col, dict):
                                col_name = col.get("name", "")
                                col_desc = col.get("description", "").strip()
                                col_type = col.get("type", "")
                                nullable = col.get("nullable", True)

                                columns.append(
                                    {
                                        "name": col_name,
                                        "description": col_desc,
                                        "type": col_type,
                                        "nullable": nullable,
                                    }
                                )

                    # Finde Primärschlüssel (basierend auf Namenskonventionen)
                    primary_keys = []
                    for col in columns:
                        col_name = col.get("name", "").upper()
                        if col_name in [
                            "ID",
                            "NR",
                            f"{table_name}NR",
                            f"{table_name}ID",
                        ]:
                            primary_keys.append(col_name)

                    # Finde Fremdschlüssel
                    foreign_keys = []
                    for rel in all_relationships:
                        if rel["from_table"] == table_name:
                            foreign_keys.append(
                                {
                                    "column": rel["from_column"],
                                    "references_table": rel["to_table"],
                                    "references_column": rel["to_column"],
                                }
                            )

                    # Speichere Tabelleninformationen
                    tables_info[table_name] = {
                        "description": description,
                        "business_context": business_context,
                        "columns": columns,
                        "primary_keys": primary_keys,
                        "foreign_keys": foreign_keys,
                    }

                    # Ordne Tabelle einer Gruppe zu
                    assigned = False
                    for group, keywords in group_keywords.items():
                        if any(keyword in table_name for keyword in keywords) or any(
                            keyword.lower() in description.lower()
                            for keyword in keywords
                        ):
                            table_groups[group].append(table_name)
                            assigned = True
                            break

                    if not assigned:
                        table_groups["Sonstiges"].append(table_name)

            except Exception as e:
                log_message(
                    f"Fehler beim Verarbeiten von {yaml_file}: {e}",
                    "warning",
                    save_status=False,
                )

        # Erstelle das endgültige Schema-Objekt
        schema_obj = {
            "tables": tables_info,
            "groups": table_groups,
            "relationships": all_relationships,
        }

        # Speichere das Schema als JSON
        with open(schema_file, "w", encoding="utf-8") as f:
            json.dump(schema_obj, f, indent=2, ensure_ascii=False)

        log_message(f"Kompakte Schemabeschreibung erstellt: {schema_file}", "info")
        return (
            True,
            f"Schema-Datei erstellt mit {len(tables_info)} Tabellen in {len(table_groups)} Gruppen.",
        )
    except Exception as e:
        log_message(
            f"Fehler bei der Erstellung der kompakten Schemabeschreibung: {e}", "error"
        )
        return False, f"Fehler: {e}"


def get_relevant_schema_context(user_query, max_tables=5):
    """
    Wählt basierend auf der Benutzeranfrage die relevantesten Teile des Schemas aus.

    Args:
        user_query: Die Benutzeranfrage
        max_tables: Maximale Anzahl von Tabellen, die zurückgegeben werden sollen

    Returns:
        Ein String mit dem relevanten Schemakontext
    """
    try:
        schema_file = schema_output_dir / "compact_schema.json"
        if not schema_file.exists():
            # Erstelle das Schema, falls es noch nicht existiert
            generate_compact_schema_description()

        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)

        # Extrahiere Schlüsselwörter aus der Anfrage
        query_lower = user_query.lower()
        query_words = set(re.findall(r"\b\w+\b", query_lower))

        # Bewerte die Relevanz jeder Tabelle
        table_scores = {}
        for table_name, table_info in schema["tables"].items():
            score = 0

            # Prüfe Tabellenname
            if table_name.lower() in query_lower:
                score += 10

            # Prüfe Beschreibung und Geschäftskontext
            description = table_info.get("description", "").lower()
            business_context = table_info.get("business_context", "").lower()

            for word in query_words:
                if len(word) < 3:  # Ignoriere zu kurze Wörter
                    continue
                if word in description:
                    score += 3
                if word in business_context:
                    score += 2

            # Prüfe Spalten
            for column in table_info.get("columns", []):
                col_name = column.get("name", "").lower()
                col_desc = column.get("description", "").lower()

                if col_name in query_lower:
                    score += 5

                for word in query_words:
                    if len(word) < 3:
                        continue
                    if word in col_name:
                        score += 2
                    if word in col_desc:
                        score += 1

            # Spezielle Schlüsselwörter für bestimmte Domänen
            if (
                "buchung" in query_lower
                or "zahlung" in query_lower
                or "transaktion" in query_lower
            ):
                if (
                    "BUCHUNG" in table_name
                    or "ZAHLUNG" in table_name
                    or "KONTO" in table_name
                ):
                    score += 8

            if (
                "adresse" in query_lower
                or "straße" in query_lower
                or "ort" in query_lower
            ):
                if (
                    "ADR" in table_name
                    or "PERSON" in table_name
                    or "OBJEKT" in table_name
                ):
                    score += 8

            if "jahr" in query_lower or "datum" in query_lower or "2024" in query_lower:
                # Tabellen mit Datumsspalten sind wahrscheinlich relevant
                for column in table_info.get("columns", []):
                    col_name = column.get("name", "").lower()
                    if "datum" in col_name or "date" in col_name or "zeit" in col_name:
                        score += 5
                        break

            table_scores[table_name] = score

        # Wähle die relevantesten Tabellen aus
        relevant_tables = sorted(
            table_scores.items(), key=lambda x: x[1], reverse=True
        )[:max_tables]

        # Erstelle den Kontext
        context = "Relevante Tabellen für deine Anfrage:\n\n"

        for table_name, score in relevant_tables:
            if score <= 0:  # Ignoriere irrelevante Tabellen
                continue

            table_info = schema["tables"][table_name]
            context += f"Tabelle: {table_name}\n"
            context += f"Beschreibung: {table_info.get('description', '')}\n"

            # Füge wichtige Spalten hinzu
            context += "Wichtige Spalten:\n"
            for column in table_info.get("columns", [])[:10]:  # Begrenze auf 10 Spalten
                context += f"- {column.get('name', '')}: {column.get('type', '')} - {column.get('description', '')}\n"

            # Füge Primärschlüssel hinzu
            if table_info.get("primary_keys"):
                context += f"Primärschlüssel: {', '.join(table_info.get('primary_keys', []))}\n"

            # Füge Fremdschlüssel hinzu
            if table_info.get("foreign_keys"):
                context += "Fremdschlüssel:\n"
                for fk in table_info.get("foreign_keys", []):
                    context += f"- {fk.get('column', '')} → {fk.get('references_table', '')}({fk.get('references_column', '')})\n"

            context += "\n"

        # Füge Beziehungsinformationen hinzu
        related_tables = set([table for table, _ in relevant_tables if _ > 0])
        relevant_relationships = []

        for rel in schema.get("relationships", []):
            if (
                rel["from_table"] in related_tables
                and rel["to_table"] in related_tables
            ):
                relevant_relationships.append(rel)

        if relevant_relationships:
            context += "Beziehungen zwischen diesen Tabellen:\n"
            for rel in relevant_relationships:
                context += f"- {rel['from_table']}({rel['from_column']}) → {rel['to_table']}({rel['to_column']})\n"

        return context
    except Exception as e:
        log_message(
            f"Fehler beim Abrufen des relevanten Schemakontexts: {e}",
            "warning",
            save_status=False,
        )
        return f"Fehler beim Abrufen des Schemakontexts: {e}"


# ==== UI-BEREICH
st.set_page_config(page_title="WINCASA - DB-Dokumentationsgenerator", layout="wide")
st.title("📄 Automatisierte Dokumentation für Wincasa Datenbank")
status.load()

with st.sidebar:
    st.header("Optionen")
    force_regenerate = st.checkbox(
        "Alle Dokumente neu generieren (auch bereits vorhandene)", value=False
    )
    translate_english = st.checkbox("Englische Beschreibungen übersetzen", value=False)
    all_table_names = get_all_tables()
    table_subset = st.multiselect(
        "Wähle Tabellen zur Generierung", all_table_names, default=all_table_names
    )

    components_expander = st.expander("Zu generierende Komponenten", expanded=True)
    with components_expander:
        gen_tables = st.checkbox("Tabellendokumentation", value=True)
        gen_procedures = st.checkbox("Gespeicherte Prozeduren", value=True)
        gen_schema = st.checkbox("Datenbankübersicht & Schema", value=True)
        gen_relations = st.checkbox("Beziehungsdiagramme", value=True)
        gen_ddl = st.checkbox("DDL-Export (Create-Statements)", value=True)

    advanced_expander = st.expander("Erweiterte Optionen", expanded=False)
    with advanced_expander:
        show_skipped = st.checkbox("Übersprungene Items anzeigen", value=True)
        sample_size = st.slider(
            "Maximale Beispieldaten-Größe", 3, 30, DEFAULT_MAX_SAMPLE_SIZE
        )
        DEFAULT_MAX_SAMPLE_SIZE = sample_size

    st.info(
        "Zweiphasen-Prozess: Nach Phase 1 (Initialdokumentation) wird in Phase 2 das gesammelte Wissen für Optimierung genutzt."
    )

    if yaml_output_dir.exists():
        existing_files = list(yaml_output_dir.glob("*.yaml"))
        st.write(f"Vorhandene YAML-Dateien: {len(existing_files)}")

    st.header("Spezielle Aktionen")
    if st.button("🔍 Kaputte YAMLs finden", key="find_broken"):
        broken = identify_broken_yamls()
        if broken:
            st.error(f"⚠️ {len(broken)} kaputte YAMLs gefunden: {', '.join(broken)}")
        else:
            st.success("✅ Alle YAMLs sind gültig!")

    if st.button("🔧 YAML reparieren", key="fix_yaml"):
        fix_results = fix_all_broken_yamls(translate_english=translate_english)
        st.write("Reparatur-Ergebnisse:", fix_results)

    if os.path.exists(os.path.join(logs_dir, "skipped_items.json")) and show_skipped:
        with open(os.path.join(logs_dir, "skipped_items.json"), "r") as f:
            try:
                skipped = json.load(f)
                if skipped.get("tables") or skipped.get("procedures"):
                    st.warning(
                        f"⏩ Übersprungen wegen Größe: {len(skipped.get('tables', []))} Tabellen, {len(skipped.get('procedures', []))} Prozeduren"
                    )
                    with st.expander("Details zu übersprungenen Items"):
                        st.write("Tabellen:", ", ".join(skipped.get("tables", [])))
                        st.write(
                            "Prozeduren:", ", ".join(skipped.get("procedures", []))
                        )
            except:
                pass

    with st.sidebar.expander("Generierungsstatus", expanded=True):
        status.load()
        st.subheader("Komponenten-Status")
        status_data = {
            "Komponente": [
                "Tabellen",
                "Prozeduren",
                "Schema",
                "Beziehungsdiagramme",
                "DDL-Exports",
            ],
            "Generiert": [
                status.tables_generated,
                status.procedures_generated,
                "✅" if status.schema_generated else "❌",
                "✅" if status.diagrams_generated else "❌",
                "✅" if status.ddl_generated else "❌",
            ],
            "Phase 1": [
                status.tables_in_phase1,
                status.procedures_in_phase1,
                "-",
                "-",
                "-",
            ],
            "Phase 2": [
                status.tables_in_phase2,
                status.procedures_in_phase2,
                "-",
                "-",
                "-",
            ],
            "Übersprungen": [
                status.tables_skipped,
                status.procedures_skipped,
                "-",
                "-",
                "-",
            ],
        }
        st.dataframe(pd.DataFrame(status_data).astype(str))

        if status.generated_details:
            details_data = [
                {"Name": key, "Phase": value}
                for key, value in status.generated_details.items()
            ]
            st.subheader("Detaillierte Statusübersicht pro Output")
            st.dataframe(pd.DataFrame(details_data).astype(str))

# Importiere die neue erweiterte Q&A-Funktionalität
try:
    from enhanced_qa_ui import create_enhanced_qa_tab

    enhanced_qa_available = True
except ImportError as e:
    print(f"Erweiterte Q&A-Funktionalität nicht verfügbar: {e}")
    enhanced_qa_available = False

# Hauptinhalt mit Tabs für bessere Organisation
if enhanced_qa_available:
    phase1_tab, phase2_tab, extras_tab, chat_tab, enhanced_qa_tab = st.tabs(
        [
            "Phase 1: Initialdokumentation",
            "Phase 2: Optimierung",
            "Exporte & Weitere Aktionen",
            "LLM Chat",
            "🔍 Erweiterte Datenbankabfrage",
        ]
    )
else:
    phase1_tab, phase2_tab, extras_tab, chat_tab = st.tabs(
        [
            "Phase 1: Initialdokumentation",
            "Phase 2: Optimierung",
            "Exporte & Weitere Aktionen",
            "LLM Chat",
        ]
    )

with phase1_tab:
    st.header("Phase 1 - Grundlegende Dokumentation erstellen")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🟢 ALLE Komponenten generieren (Phase 1)", key="generate_all_p1"):
            log_message(
                "Durchlauf 1: Initiale YAML-Generierung für alle Komponenten", "info"
            )

            if gen_tables:
                generate_yaml_batch(
                    existing_yamls={},
                    force_regenerate=force_regenerate,
                    phase="phase1",
                    table_subset=table_subset,
                    translate_english=translate_english,
                )

            if gen_procedures:
                generate_all_procedure_yaml("phase1")

            if gen_schema:
                create_index_file()
                create_database_overview()

            if gen_relations:
                try:
                    generate_relation_report()
                    log_message("Beziehungsdiagramme erstellt.", "info")
                except Exception as e:
                    log_message(
                        f"Fehler beim Generieren der Beziehungsdiagramme: {e}",
                        "warning",
                    )

            if gen_ddl:
                try:
                    count = export_all_ddl()
                    log_message(f"{count} DDL-Dateien exportiert.", "info")
                except Exception as e:
                    log_message(f"Fehler beim DDL-Export: {e}", "warning")

            log_message(
                "Phase 1 abgeschlossen. Du kannst jetzt optional Phase 2 starten.",
                "info",
            )

            # Erstelle auch die kompakte Schemabeschreibung
            try:
                generate_compact_schema_description()
                log_message(
                    "Kompakte Schemabeschreibung für LLM-Chat erstellt.", "info"
                )
            except Exception as e:
                log_message(
                    f"Fehler bei der Erstellung der kompakten Schemabeschreibung: {e}",
                    "warning",
                )

    with col2:
        if st.button("📋 Nur Tabellen-YAML generieren (Phase 1)", key="gen_tables_p1"):
            generate_yaml_batch(
                existing_yamls={},
                force_regenerate=force_regenerate,
                phase="phase1",
                table_subset=table_subset,
                translate_english=translate_english,
            )
            log_message("Phase 1: Tabellen-YAMLs generiert", "info")

        if st.button("📊 Nur Prozeduren-YAML generieren (Phase 1)", key="gen_procs_p1"):
            generate_all_procedure_yaml("phase1")
            log_message("Phase 1: Prozeduren-YAMLs generiert", "info")

        if st.button("📐 Nur Schema generieren (Phase 1)", key="gen_schema_p1"):
            create_index_file()
            create_database_overview()
            log_message("Phase 1: Schema generiert", "info")

        if st.button("📄 Nur Index.md generieren (Phase 1)", key="gen_index_p1"):
            success, message = create_index_file()
            if success:
                log_message(
                    f"Phase 1: Index.md erfolgreich generiert. {message}", "info"
                )
                st.success(
                    f"✅ Index.md erfolgreich generiert: {schema_output_dir / 'index.md'}"
                )
            else:
                log_message(
                    f"Phase 1: Fehler bei der Generierung von Index.md: {message}",
                    "error",
                )

        if st.button(
            "📊 Nur Beziehungsdiagramme generieren (Phase 1)", key="gen_rel_p1"
        ):
            try:
                generate_relation_report()
                log_message("Phase 1: Beziehungsdiagramme erstellt.", "info")
            except Exception as e:
                log_message(
                    f"Fehler beim Generieren der Beziehungsdiagramme: {e}", "warning"
                )

        if st.button("📑 Nur DDL-Export generieren (Phase 1)", key="gen_ddl_p1"):
            try:
                count = export_all_ddl()
                log_message(f"Phase 1: {count} DDL-Dateien exportiert.", "info")
            except Exception as e:
                log_message(f"Fehler beim DDL-Export: {e}", "warning")

with phase2_tab:
    st.header("Phase 2 - Optimierung mit bestehendem Wissen")

    existing_yamls_count = (
        len(list(yaml_output_dir.glob("*.yaml"))) if yaml_output_dir.exists() else 0
    )
    if existing_yamls_count == 0:
        st.warning(
            "⚠️ Keine YAMLs aus Phase 1 gefunden! Bitte zuerst Phase 1 ausführen."
        )
    else:
        st.success(
            f"✅ {existing_yamls_count} YAML-Dateien aus Phase 1 gefunden. Phase 2 kann gestartet werden."
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 ALLE Komponenten optimieren (Phase 2)", key="optimize_all_p2"):
            log_message(
                "Phase 2: Optimierung aller Komponenten mit bestehendem Wissen", "info"
            )

            new_yaml_context = load_existing_yaml_dict()

            if gen_tables:
                generate_yaml_batch(
                    existing_yamls=new_yaml_context,
                    force_regenerate=force_regenerate,
                    phase="phase2",
                    table_subset=table_subset,
                    translate_english=translate_english,
                )

            if gen_procedures:
                generate_all_procedure_yaml("phase2")

            if gen_schema:
                create_index_file()
                create_database_overview()

            if gen_relations:
                try:
                    generate_relation_report()
                    log_message("Beziehungsdiagramme aktualisiert.", "info")
                except Exception as e:
                    log_message(
                        f"Fehler beim Generieren der Beziehungsdiagramme: {e}",
                        "warning",
                    )

            if gen_ddl:
                try:
                    count = export_all_ddl()
                    log_message(f"{count} DDL-Dateien aktualisiert.", "info")
                except Exception as e:
                    log_message(f"Fehler beim DDL-Export: {e}", "warning")

            log_message("Phase 2 abgeschlossen.", "info")

            # Aktualisiere auch die kompakte Schemabeschreibung
            try:
                generate_compact_schema_description()
                log_message(
                    "Kompakte Schemabeschreibung für LLM-Chat aktualisiert.", "info"
                )
            except Exception as e:
                log_message(
                    f"Fehler bei der Aktualisierung der kompakten Schemabeschreibung: {e}",
                    "warning",
                )

    with col2:
        new_yaml_context = load_existing_yaml_dict()

        if st.button("📋 Nur Tabellen-YAML optimieren (Phase 2)", key="opt_tables_p2"):
            generate_yaml_batch(
                existing_yamls=new_yaml_context,
                force_regenerate=force_regenerate,
                phase="phase2",
                table_subset=table_subset,
                translate_english=translate_english,
            )
            log_message("Phase 2: Tabellen-YAMLs optimiert", "info")

        if st.button("📊 Nur Prozeduren-YAML optimieren (Phase 2)", key="opt_procs_p2"):
            generate_all_procedure_yaml("phase2")
            log_message("Phase 2: Prozeduren-YAMLs optimiert", "info")

        if st.button("📐 Nur Schema optimieren (Phase 2)", key="opt_schema_p2"):
            create_index_file()
            create_database_overview()
            log_message("Phase 2: Schema optimiert", "info")

        if st.button("📄 Nur Index.md generieren (Phase 2)", key="gen_index_p2"):
            success, message = create_index_file()
            if success:
                log_message(
                    f"Phase 2: Index.md erfolgreich generiert. {message}", "info"
                )
                st.success(
                    f"✅ Index.md erfolgreich generiert: {schema_output_dir / 'index.md'}"
                )
            else:
                log_message(
                    f"Phase 2: Fehler bei der Generierung von Index.md: {message}",
                    "error",
                )

        if st.button(
            "📊 Nur Beziehungsdiagramme optimieren (Phase 2)", key="opt_rel_p2"
        ):
            try:
                generate_relation_report()
                log_message("Phase 2: Beziehungsdiagramme optimiert.", "info")
            except Exception as e:
                log_message(
                    f"Fehler beim Optimieren der Beziehungsdiagramme: {e}", "warning"
                )

        if st.button("📑 Nur DDL-Export optimieren (Phase 2)", key="opt_ddl_p2"):
            try:
                count = export_all_ddl()
                log_message(f"Phase 2: {count} DDL-Dateien optimiert.", "info")
            except Exception as e:
                log_message(f"Fehler beim DDL-Export: {e}", "warning")

with extras_tab:
    st.header("Export und Downloads")

    # Füge Button für die Generierung der kompakten Schemabeschreibung hinzu
    if st.button("🔍 Kompakte Schemabeschreibung generieren", key="gen_compact_schema"):
        with st.spinner("Generiere kompakte Schemabeschreibung..."):
            success, message = generate_compact_schema_description()
            if success:
                st.success(message)
                st.info(
                    f"Die Schemabeschreibung wurde in {schema_output_dir / 'compact_schema.json'} gespeichert."
                )
            else:
                st.error(message)

    col1, col2 = st.columns(2)

    with col1:
        zip_filename = f"wincasa_docs_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        zip_path = f"output/{zip_filename}"

        if st.button("💾 Dokumentations-Paket als ZIP erstellen", key="create_zip"):
            try:
                ensure_dir("output")
                shutil.make_archive(
                    base_name=zip_path.replace(".zip", ""),
                    format="zip",
                    root_dir="output",
                )
                log_message(f"ZIP-Paket {zip_filename} erstellt.", "info")
                st.success(f"✅ ZIP-Paket erstellt: {zip_filename}")
                st.download_button(
                    "⬇️ Dokumentations-Paket herunterladen",
                    open(zip_path, "rb"),
                    file_name=zip_filename,
                    mime="application/zip",
                )
            except Exception as e:
                log_message(f"Fehler beim Erstellen des ZIP-Pakets: {e}", "error")

    with col2:
        if st.button("🧪 Nur YAML-Statistik generieren", key="gen_yaml_stats"):
            try:
                all_tables_count = len(get_all_tables())
                yamls = (
                    list(yaml_output_dir.glob("*.yaml"))
                    if yaml_output_dir.exists()
                    else []
                )

                st.write(
                    f"Dokumentierte Tabellen: {len([y for y in yamls if '_procedure' not in y.stem])}/{all_tables_count}"
                )
                st.write(
                    f"Dokumentierte Prozeduren: {len([y for y in yamls if '_procedure' in y.stem])}"
                )

                empty_tables = 0
                priority_counts = {"high": 0, "medium": 0, "low": 0}

                for yaml_file in yamls:
                    try:
                        with open(yaml_file, "r") as f:
                            data = yaml.safe_load(f)
                            if data.get("is_empty", False):
                                empty_tables += 1
                            priority = data.get("priority", "medium")
                            priority_counts[priority] = (
                                priority_counts.get(priority, 0) + 1
                            )
                    except Exception as e:
                        print(f"Fehler bei {yaml_file}: {e}")

                st.write(f"Leere Tabellen: {empty_tables}")
                st.write(
                    f"Tabellen nach Priorität: Hoch={priority_counts['high']}, Mittel={priority_counts['medium']}, Niedrig={priority_counts['low']}"
                )

                # Zeige ein Balkendiagramm
                df = pd.DataFrame.from_dict(
                    priority_counts, orient="index", columns=["Anzahl"]
                )
                st.bar_chart(df)

                log_message("YAML-Statistik generiert", "info")
            except Exception as e:
                log_message(f"Fehler bei der YAML-Statistik: {e}", "error")

if yaml_output_dir.exists():
    yamls = list(yaml_output_dir.glob("*.yaml"))
    if yamls:
        with st.expander("Statistik der vorhandenen Dokumentation", expanded=False):
            try:
                all_tables_counts = len(get_all_tables())
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Dokumentierte Tabellen",
                        f"{len([y for y in yamls if '_procedure' not in y.stem])}/{all_tables_counts}",
                        f"{round(len([y for y in yamls if '_procedure' not in y.stem])/max(1, all_tables_counts)*100)}%",
                    )
                empty_tables = 0
                priority_counts = {"high": 0, "medium": 0, "low": 0}
                for yaml_file in yamls:
                    try:
                        with open(yaml_file, "r") as f:
                            data = yaml.safe_load(f)
                            if data.get("is_empty", False):
                                empty_tables += 1
                            priority = data.get("priority", "medium")
                            priority_counts[priority] = (
                                priority_counts.get(priority, 0) + 1
                            )
                    except:
                        pass
                with col2:
                    st.metric(
                        "Leere Tabellen",
                        empty_tables,
                        f"{round(empty_tables/max(1, len([y for y in yamls if '_procedure' not in y.stem]))*100)}%",
                    )
                with col3:
                    st.metric("Hochprioritäts-Tabellen", priority_counts.get("high", 0))
                st.bar_chart(pd.DataFrame(priority_counts, index=[0]).astype(str))
            except Exception as e:
                st.error(f"Fehler bei der Statistikanzeige: {e}")


# === CHAT-FUNKTIONALITÄT ===
def get_llm_response(prompt, system_message=None):
    """
    Sendet eine Anfrage an das LLM und gibt die Antwort zurück.

    Args:
        prompt: Die Benutzeranfrage
        system_message: Optionale System-Nachricht für Kontext

    Returns:
        Die Antwort des LLM
    """
    try:
        messages = []

        # Füge System-Nachricht hinzu, falls vorhanden
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Füge Benutzeranfrage hinzu
        messages.append({"role": "user", "content": prompt})

        # Logging für Debugging
        log_file = logs_dir / "llm_prompts.log"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(
                    f"\n\n=== NEUE ANFRAGE {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n"
                )
                f.write(f"System-Nachricht: {system_message[:200]}...\n")
                f.write(f"Prompt: {prompt[:500]}...\n")
        except:
            pass

        # Rufe das LLM auf
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"Fehler bei der LLM-Anfrage: {str(e)}"


# Chat-Tab-Inhalt
with chat_tab:
    st.header("💬 Chat mit dem LLM")

    # Initialisiere Session State für Chat-Verlauf
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # System-Nachricht-Eingabe
    with st.expander("Erweiterte Chat-Optionen", expanded=False):
        system_message = st.text_area(
            "System-Nachricht (optional)",
            value="""Du bist ein Datenbankexperte für das Wincasa-Immobilienverwaltungssystem. Du hast Zugriff auf das vollständige Datenbankschema und die Dokumentation aller Tabellen.

WICHTIG: In deinen Antworten MUSST du die Informationen aus dem bereitgestellten Kontext verwenden. Der Kontext enthält:
1. Eine detaillierte Beschreibung der relevanten Tabellen und ihrer Spalten
2. Informationen über Beziehungen zwischen Tabellen
3. Beispiele für typische Abfragen

Wenn du nach Informationen zu bestimmten Tabellen oder Spalten gefragt wirst, suche IMMER zuerst im bereitgestellten Kontext nach diesen Informationen. Beziehe dich explizit auf die Tabellen und Spalten, die im Kontext erwähnt werden.

Wenn du SQL-Abfragen schreibst, verwende die korrekten Tabellen- und Spaltennamen aus dem Kontext. Erkläre, welche Tabellen du verwendest und warum.

Behaupte NIEMALS, dass du keinen Zugriff auf Informationen hast, die im Kontext enthalten sind.""",
            height=200,
        )

        # Option zum Löschen des Chat-Verlaufs
        if st.button("Chat-Verlauf löschen"):
            st.session_state.chat_history = []
            st.rerun()

    # Chat-Verlauf anzeigen
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                st.markdown(f"**👤 Du:** {message['content']}")
            else:
                st.markdown(f"**🤖 LLM:** {message['content']}")

            # Trennlinie zwischen Nachrichten, außer nach der letzten
            if i < len(st.session_state.chat_history) - 1:
                st.markdown("---")

    # Eingabebereich
    with st.form(key="chat_form"):
        user_input = st.text_area("Deine Nachricht:", height=100)

        # Kontextoptionen
        col1, col2 = st.columns(2)
        with col1:
            include_db_info = st.checkbox("Datenbankkontext einbeziehen", value=True)
        with col2:
            include_yaml_info = st.checkbox(
                "YAML-Dokumentation einbeziehen", value=True
            )

        submit_button = st.form_submit_button("Senden")

        if submit_button and user_input:
            # Füge Benutzernachricht zum Verlauf hinzu
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input}
            )

            # Bereite Kontext vor, falls gewünscht
            context = ""

            # Prüfe, ob die kompakte Schemabeschreibung existiert, sonst erstelle sie
            schema_file = schema_output_dir / "compact_schema.json"
            if not schema_file.exists():
                with st.spinner("Erstelle kompakte Schemabeschreibung..."):
                    success, message = generate_compact_schema_description()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

            if include_db_info:
                # Verwende die dynamische Kontextauswahl
                with st.spinner("Analysiere Anfrage und wähle relevanten Kontext..."):
                    schema_context = get_relevant_schema_context(user_input)
                    if schema_context and not schema_context.startswith("Fehler"):
                        context += f"""
=== DATENBANKSCHEMA-KONTEXT ===
Der folgende Kontext enthält Informationen über die relevanten Tabellen und ihre Beziehungen für deine Anfrage.
Du MUSST diese Informationen in deiner Antwort verwenden.

{schema_context}

=== ENDE DES DATENBANKSCHEMA-KONTEXTS ===
"""
                    else:
                        # Fallback auf einfachere Methode
                        try:
                            all_tables = get_all_tables()
                            context += f"=== DATENBANKSCHEMA-KONTEXT ===\nDie Datenbank enthält {len(all_tables)} Tabellen.\n"

                            # Füge Informationen zu den Top-Tabellen hinzu
                            if len(all_tables) > 0:
                                context += f"Wichtige Tabellen sind: {', '.join(all_tables[:10])}.\n=== ENDE DES DATENBANKSCHEMA-KONTEXTS ==="
                        except Exception as e:
                            st.warning(
                                f"Konnte keine Tabelleninformationen abrufen: {e}"
                            )

            if include_yaml_info and yaml_output_dir.exists():
                # Verbesserte Suche nach relevanten YAML-Dateien
                relevant_yamls = []
                user_keywords = set(re.findall(r"\b\w+\b", user_input.lower()))

                # Entferne zu kurze Wörter
                user_keywords = {word for word in user_keywords if len(word) >= 3}

                # Füge domänenspezifische Schlüsselwörter hinzu
                if "buchung" in user_input.lower() or "zahlung" in user_input.lower():
                    user_keywords.update(["buchung", "konto", "zahlung", "bank"])

                if "adresse" in user_input.lower() or "straße" in user_input.lower():
                    user_keywords.update(["adr", "adresse", "person", "bewohner"])

                yaml_scores = {}

                for yaml_file in yaml_output_dir.glob("*.yaml"):
                    try:
                        score = 0
                        # Prüfe Dateiname
                        for keyword in user_keywords:
                            if keyword in yaml_file.stem.lower():
                                score += 5

                        # Wenn der Score > 0 ist oder wir noch keine relevanten YAMLs haben,
                        # prüfe den Inhalt
                        if score > 0 or len(yaml_scores) < 5:
                            with open(yaml_file, "r", encoding="utf-8") as f:
                                content = f.read().lower()
                                for keyword in user_keywords:
                                    if keyword in content:
                                        score += content.count(keyword)

                        if score > 0:
                            yaml_scores[yaml_file] = score
                    except Exception as e:
                        continue

                # Wähle die relevantesten YAMLs
                top_yamls = sorted(
                    yaml_scores.items(), key=lambda x: x[1], reverse=True
                )[:3]

                for yaml_file, score in top_yamls:
                    try:
                        with open(yaml_file, "r", encoding="utf-8") as f:
                            yaml_content = f.read()
                            # Extrahiere nur die wichtigsten Informationen
                            try:
                                data = yaml.safe_load(yaml_content)
                                summary = f"Tabelle: {yaml_file.stem}\n"
                                summary += (
                                    f"Beschreibung: {data.get('description', '')}\n"
                                )

                                # Füge wichtige Spalten hinzu
                                if "columns" in data and isinstance(
                                    data["columns"], list
                                ):
                                    summary += "Wichtige Spalten:\n"
                                    for col in data["columns"][
                                        :5
                                    ]:  # Nur die ersten 5 Spalten
                                        if isinstance(col, dict):
                                            summary += f"- {col.get('name', '')}: {col.get('description', '')}\n"

                                relevant_yamls.append(summary)
                            except:
                                # Fallback auf einfachen Textauszug
                                relevant_yamls.append(
                                    f"Informationen zu {yaml_file.stem}:\n{yaml_content[:300]}..."
                                )
                    except:
                        continue

                if relevant_yamls:
                    context += (
                        "\n\n=== RELEVANTE TABELLENDOKUMENTATION ===\n"
                        + "\n\n".join(relevant_yamls)
                        + "\n=== ENDE DER TABELLENDOKUMENTATION ==="
                    )

            # Erstelle den vollständigen Prompt
            full_prompt = user_input
            if context:
                full_prompt = f"""
{user_input}

WICHTIG - KONTEXT FÜR DEINE ANTWORT:
Du hast Zugriff auf die folgenden Informationen über die Wincasa-Datenbank.
Verwende diese Informationen, um eine präzise Antwort zu geben.
Beziehe dich explizit auf die Tabellen und Spalten aus diesem Kontext.

{context}

Basiere deine Antwort auf diesen Informationen und erkläre, welche Tabellen und Spalten du verwendest.
"""

            # Hole Antwort vom LLM
            with st.spinner("LLM denkt nach..."):
                response = get_llm_response(full_prompt, system_message)

            # Füge LLM-Antwort zum Verlauf hinzu
            st.session_state.chat_history.append(
                {"role": "assistant", "content": response}
            )

            # Aktualisiere die Anzeige
            st.rerun()
