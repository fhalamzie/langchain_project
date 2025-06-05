"""
db_executor.py - Modul zur sicheren Ausführung von SQL-Abfragen auf der Firebird-Datenbank

Dieses Modul bietet Funktionen für:
1. Sichere Ausführung von SQL-Abfragen
2. Grundlegende Validierung von SQL-Abfragen
3. Caching von Abfrageergebnissen
4. Timeout- und Ressourcenbegrenzungen
"""

import hashlib
import json
import os
import re
import signal
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import fdb
import pandas as pd

# Konfiguration
DB_PATH = "./WINCASA2022.FDB"
DB_USER = "SYSDBA"
DB_PASSWORD = "masterkey"
QUERY_TIMEOUT = 30  # Timeout in Sekunden
CACHE_DIR = Path("./output/cache")
MAX_RESULTS = 1000  # Maximale Anzahl von Zeilen, die zurückgegeben werden
SAFE_TABLES = (
    set()
)  # Tabellen, die als sicher für Abfragen eingestuft sind (wird später gefüllt)
SENSITIVE_COLUMNS = set()  # Spalten mit sensiblen Daten (wird später gefüllt)

# Temporäres Verzeichnis für Firebird einrichten
fb_temp_dir = Path("./fb_temp").absolute()
if not fb_temp_dir.exists():
    fb_temp_dir.mkdir(exist_ok=True)

# Stelle sicher, dass das Cache-Verzeichnis existiert
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Firebird-Umgebungsvariablen setzen
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


# Klasse für Timeout-Ausnahmen
class QueryTimeoutError(Exception):
    """Ausnahme, die ausgelöst wird, wenn eine Abfrage das Zeitlimit überschreitet."""

    pass


# Klasse für SQL-Sicherheitsausnahmen
class SQLSecurityError(Exception):
    """Ausnahme, die ausgelöst wird, wenn eine Abfrage Sicherheitsbedenken aufwirft."""

    pass


# Klasse für SQL-Validierungsfehler
class SQLValidationError(Exception):
    """Ausnahme, die ausgelöst wird, wenn eine SQL-Abfrage ungültig ist."""

    pass


@contextmanager
def get_db_connection():
    """
    Kontextmanager für Datenbankverbindungen.
    Stellt sicher, dass Verbindungen ordnungsgemäß geschlossen werden.
    """
    conn = None
    try:
        # Überprüfe, ob die Datenbankdatei existiert
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Datenbank-Datei '{DB_PATH}' nicht gefunden.")

        conn = fdb.connect(
            dsn=DB_PATH, user=DB_USER, password=DB_PASSWORD, charset="WIN1252"
        )
        yield conn
    except Exception as e:
        raise Exception(f"Fehler bei der Datenbankverbindung: {e}")
    finally:
        if conn:
            conn.close()


def timeout_handler(signum, frame):
    """Signal-Handler für Timeouts."""
    raise QueryTimeoutError("Die SQL-Abfrage hat das Zeitlimit überschritten.")


def convert_win1252_to_utf8(text):
    """Konvertiert Windows-1252-kodierten Text nach UTF-8."""
    if isinstance(text, bytes):
        return text.decode("windows-1252", errors="replace")
    return text


def validate_sql(sql: str) -> Tuple[bool, str]:
    """
    Grundlegende Validierung einer SQL-Abfrage.

    Args:
        sql: Die zu validierende SQL-Abfrage

    Returns:
        Tuple: (ist_gültig, fehlermeldung)
    """
    # Entferne Kommentare und mehrfache Leerzeichen
    cleaned_sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    cleaned_sql = re.sub(r"/\*.*?\*/", "", cleaned_sql, flags=re.DOTALL)
    cleaned_sql = re.sub(r"\s+", " ", cleaned_sql).strip()

    # Prüfe auf gefährliche Operationen
    dangerous_operations = [
        r"\bDROP\b",
        r"\bTRUNCATE\b",
        r"\bALTER\b",
        r"\bCREATE\b",
        r"\bDELETE\b",
        r"\bINSERT\b",
        r"\bUPDATE\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bEXECUTE\b",
    ]

    for pattern in dangerous_operations:
        if re.search(pattern, cleaned_sql, re.IGNORECASE):
            # Entferne die \b-Markierungen ohne strip() zu verwenden
            operation_name = pattern.replace("\\b", "")
            return False, f"Nicht erlaubte Operation: {operation_name}"

    # Prüfe, ob es sich um eine SELECT-Abfrage handelt
    if not re.match(r"^\s*SELECT\b", cleaned_sql, re.IGNORECASE):
        return False, "Nur SELECT-Abfragen sind erlaubt"

    # Weitere Sicherheitsüberprüfungen könnten hier hinzugefügt werden

    return True, ""


def get_query_hash(sql: str) -> str:
    """
    Erstellt einen Hash-Wert für eine SQL-Abfrage, um Cache-Schlüssel zu generieren.

    Args:
        sql: Die SQL-Abfrage

    Returns:
        str: Hash-Wert der Abfrage
    """
    # Entferne Leerzeichen und konvertiere zu Kleinbuchstaben für konsistentes Hashing
    normalized_sql = re.sub(r"\s+", " ", sql.lower()).strip()
    return hashlib.md5(normalized_sql.encode()).hexdigest()


def save_to_cache(query_hash: str, results: List[Dict[str, Any]]) -> None:
    """
    Speichert Abfrageergebnisse im Cache.

    Args:
        query_hash: Der Hash-Wert der Abfrage
        results: Die zu speichernden Ergebnisse
    """
    cache_file = CACHE_DIR / f"{query_hash}.json"
    cache_data = {"timestamp": datetime.now().isoformat(), "results": results}

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, default=str)


def get_from_cache(
    query_hash: str, max_age_seconds: int = 3600
) -> Optional[List[Dict[str, Any]]]:
    """
    Versucht, Ergebnisse aus dem Cache zu laden.

    Args:
        query_hash: Der Hash-Wert der Abfrage
        max_age_seconds: Maximales Alter der Cache-Einträge in Sekunden

    Returns:
        Optional[List[Dict[str, Any]]]: Die Ergebnisse oder None, wenn nicht im Cache oder veraltet
    """
    cache_file = CACHE_DIR / f"{query_hash}.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        # Prüfe, ob der Cache-Eintrag zu alt ist
        timestamp = datetime.fromisoformat(cache_data["timestamp"])
        age_seconds = (datetime.now() - timestamp).total_seconds()

        if age_seconds > max_age_seconds:
            return None

        return cache_data["results"]
    except Exception as e:
        print(f"Fehler beim Laden aus dem Cache: {e}")
        return None


def execute_sql(
    sql: str,
    params: Optional[Dict[str, Any]] = None,
    use_cache: bool = True,
    max_cache_age: int = 3600,
) -> Tuple[bool, Union[List[Dict[str, Any]], str]]:
    """
    Führt eine SQL-Abfrage sicher aus und gibt die Ergebnisse zurück.

    Args:
        sql: Die auszuführende SQL-Abfrage
        params: Parameter für die Abfrage (für prepared statements)
        use_cache: Ob der Cache verwendet werden soll
        max_cache_age: Maximales Alter der Cache-Einträge in Sekunden

    Returns:
        Tuple: (erfolg, ergebnisse_oder_fehlermeldung)
    """
    # Validiere die Abfrage
    is_valid, error_msg = validate_sql(sql)
    if not is_valid:
        return False, error_msg

    # Prüfe den Cache, wenn aktiviert
    if use_cache:
        query_hash = get_query_hash(sql)
        cached_results = get_from_cache(query_hash, max_cache_age)
        if cached_results:
            return True, cached_results

    # Führe die Abfrage aus
    try:
        with get_db_connection() as conn:
            if conn is None:
                return False, "Keine Datenbankverbindung verfügbar."

            cursor = conn.cursor()

            # Setze Timeout
            original_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(QUERY_TIMEOUT)

            try:
                # Führe die Abfrage aus (mit oder ohne Parameter)
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)

                # Hole die Spaltenüberschriften
                column_names = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )

                # Begrenze die Anzahl der zurückgegebenen Zeilen
                results = []
                for i, row in enumerate(cursor):
                    if i >= MAX_RESULTS:
                        break

                    # Konvertiere die Zeile in ein Dictionary und handle Kodierung
                    row_dict = {}
                    for idx, col_name in enumerate(column_names):
                        value = row[idx]
                        if isinstance(value, (str, bytes)):
                            value = convert_win1252_to_utf8(value)
                        row_dict[col_name] = value

                    results.append(row_dict)

                # Speichere im Cache, wenn aktiviert
                if use_cache and results:
                    query_hash = get_query_hash(sql)
                    save_to_cache(query_hash, results)

                return True, results
            finally:
                # Setze den Alarm zurück und stelle den ursprünglichen Handler wieder her
                signal.alarm(0)
                signal.signal(signal.SIGALRM, original_handler)

    except QueryTimeoutError:
        return False, "Die Abfrage hat das Zeitlimit überschritten."
    except SQLSecurityError as e:
        return False, f"Sicherheitsfehler: {str(e)}"
    except Exception as e:
        return False, f"Fehler bei der Ausführung der Abfrage: {str(e)}"


def results_to_dataframe(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Konvertiert Abfrageergebnisse in ein Pandas DataFrame.

    Args:
        results: Die Abfrageergebnisse als Liste von Dictionaries

    Returns:
        pd.DataFrame: Die Ergebnisse als DataFrame
    """
    return pd.DataFrame(results)


def get_all_tables() -> List[str]:
    """
    Gibt eine Liste aller Tabellen in der Datenbank zurück.

    Returns:
        List[str]: Liste der Tabellennamen
    """
    try:
        with get_db_connection() as conn:
            if conn is None:
                return []

            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT rdb$relation_name FROM rdb$relations
                WHERE rdb$view_blr IS NULL AND rdb$system_flag = 0
            """
            )
            return [row[0].strip() for row in cursor.fetchall()]
    except Exception as e:
        print(f"Fehler beim Abrufen aller Tabellen: {e}")
        return []


def fill_safe_tables():
    """Füllt die Liste der sicheren Tabellen aus der Datenbank."""
    global SAFE_TABLES
    # Hier könnte man die sicheren Tabellen aus einer Konfigurationsdatei laden
    # oder basierend auf bestimmten Kriterien automatisch bestimmen
    # Für jetzt nehmen wir einfach alle Tabellen als sicher an
    SAFE_TABLES = set(get_all_tables())


# Initialisiere die Liste der sicheren Tabellen
fill_safe_tables()

# Beispielverwendung:
if __name__ == "__main__":
    # Beispiel für eine einfache Abfrage
    sql = "SELECT * FROM PERSONEN LIMIT 5"
    success, result = execute_sql(sql)

    if success:
        print(f"Abfrage erfolgreich, {len(result)} Ergebnisse gefunden.")
        for row in result[:3]:  # Zeige die ersten 3 Ergebnisse
            print(row)
    else:
        print(f"Fehler: {result}")
