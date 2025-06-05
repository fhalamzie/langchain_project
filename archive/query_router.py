# query_router.py
import logging
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

# Konfiguriere Logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Datenbank-Konfiguration - verwende das aktuelle Arbeitsverzeichnis /home/projects/
DB_PATH = os.path.join("/home/projects/langchain_project", "WINCASA2022.FDB")
# Alternativpfad falls die Datei im aktuellen Verzeichnis nicht gefunden wird
if not os.path.exists(DB_PATH):
    alt_path = os.path.join("/home/projects", "WINCASA2022.FDB")
    if os.path.exists(alt_path):
        DB_PATH = alt_path

DB_USER = "sysdba"  # Kleingeschrieben wie im Beispielcode
DB_PASSWORD = "masterkey"

logger.info(f"Verwende Datenbank-Pfad: {DB_PATH}")

# Versuche den Firebird-Treiber zu importieren
try:
    # Pfade für die native Firebird-Library festlegen
    current_dir = Path(__file__).parent.absolute()

    # Mögliche Pfade für die FB Client Library - priorisiere die lokale Kopie
    fb_lib_paths = [
        # Lokale Kopie im Projektverzeichnis (sollte vorhanden sein)
        current_dir / "lib" / "libfbclient.so",
        # Standard-Pfade auf Linux
        Path("/opt/firebird/lib/libfbclient.so"),
        Path("/usr/lib/libfbclient.so"),
        Path("/usr/local/lib/libfbclient.so"),
        # Durchsuche das aktuelle Verzeichnis rekursiv nach .so Dateien
        current_dir,
    ]

    # Suche nach libfbclient.so
    fb_lib_found = False
    for path in fb_lib_paths:
        if path.exists():
            if path.is_file() and "fbclient" in path.name.lower():
                # Direkter Treffer auf eine Datei
                fb_lib_path = path
                fb_lib_found = True
                logger.info(f"Firebird-Client-Library direkt gefunden: {path}")
                break

            # Wenn es ein Verzeichnis ist, suche nach der Datei
            if path.is_dir():
                lib_files = list(path.glob("**/libfbclient.so*")) + list(
                    path.glob("**/fbclient.dll")
                )
                if lib_files:
                    fb_lib_path = lib_files[0]
                    fb_lib_found = True
                    logger.info(
                        f"Firebird-Client-Library im Verzeichnis gefunden: {fb_lib_path}"
                    )
                    break

    # Ausgabe des Suchpfads
    logger.info(
        f"Suche Firebird-Client-Library in: {', '.join(str(p) for p in fb_lib_paths)}"
    )

    if fb_lib_found:
        logger.info(f"Firebird-Client-Library gefunden: {fb_lib_path}")
        # Setze Umgebungsvariable für den Driver
        os.environ["FIREBIRD_LIBRARY_PATH"] = str(fb_lib_path)
    else:
        logger.warning("Firebird-Client-Library nicht gefunden in den Suchpfaden.")

    # Firebird-Treiber importieren
    from firebird import driver

    FIREBIRD_AVAILABLE = True
    logger.info("Firebird-Driver erfolgreich importiert.")

except ImportError:
    FIREBIRD_AVAILABLE = False
    logger.error(
        "Firebird-Driver nicht gefunden. Installiere ihn mit: pip install firebird-driver"
    )

except Exception as e:
    FIREBIRD_AVAILABLE = False
    logger.error(f"Problem mit Firebird-Driver: {str(e)}")

    # Versuche, mehr Informationen zu erhalten
    try:
        logger.info("Systemumgebung:")
        logger.info(f"Python-Version: {sys.version}")
        logger.info(f"Betriebssystem: {sys.platform}")

        # Liste installierte Pakete auf
        logger.info("Installierte Pakete:")
        packages = subprocess.check_output(
            [sys.executable, "-m", "pip", "list"]
        ).decode("utf-8")
        logger.info(packages)

    except Exception:
        pass

# Diese Zeilen wurden entfernt, da sie bereits oben definiert sind


@contextmanager
def get_db_connection():
    """
    Liefert eine Datenbankverbindung mit dem Firebird-Driver.
    Wirft eine Ausnahme, wenn keine Verbindung hergestellt werden kann.
    Verwendet die gleiche Verbindungsmethode wie im funktionierenden Beispielcode.
    """
    conn = None
    try:
        if not FIREBIRD_AVAILABLE:
            raise ImportError(
                "Firebird-Driver nicht verfügbar. Installiere ihn mit: pip install firebird-driver"
            )

        # Überprüfe, ob die Datenbankdatei existiert
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Datenbank-Datei '{DB_PATH}' nicht gefunden.")

        logger.info(f"Verbinde zur Datenbank: {DB_PATH}")

        # Verbindung mit dem genauen Format aus dem funktionierenden Beispielcode
        conn = driver.connect(database=DB_PATH, user=DB_USER, password=DB_PASSWORD)

        logger.info("Datenbankverbindung erfolgreich hergestellt!")
        yield conn
    except Exception as e:
        logger.error(f"Fehler beim Verbinden zur Datenbank: {str(e)}")

        # Mehr Details zum Problem ausgeben
        if "location of Firebird Client Library" in str(e):
            logger.error("Die Client-Library wurde nicht gefunden.")
            lib_path = os.environ.get("FIREBIRD_LIBRARY_PATH", "nicht gesetzt")
            logger.error(f"FIREBIRD_LIBRARY_PATH: {lib_path}")
            logger.error(
                "Überprüfen Sie, ob die Library-Datei im korrekten Pfad existiert."
            )
        elif "Permission denied" in str(e):
            logger.error(
                "Zugriffsverweigerung beim Zugriff auf Dateien oder Verzeichnisse."
            )
            logger.error(
                "Überprüfen Sie die Berechtigungen für die Datenbank-Datei und temporäre Verzeichnisse."
            )

        # Keine Beispieldaten mehr verwenden - Fehler weiterreichen
        raise
    finally:
        if conn:
            try:
                conn.close()
                logger.info("Datenbankverbindung geschlossen.")
            except Exception:
                pass


def execute_safe_sql(sql_query):
    """
    Führt eine SQL-Abfrage aus und gibt die Ergebnisse zurück.

    Args:
        sql_query: Die auszuführende SQL-Abfrage

    Returns:
        list: Eine Liste von Wörterbüchern mit den Abfrageergebnissen

    Raises:
        Exception: Wenn ein Fehler bei der SQL-Ausführung auftritt
    """
    logger.info(f"Führe SQL aus: {sql_query[:100]}...")

    # Verwende das Verbindungsmanagement aus dem Beispielcode
    try:
        # Verbindung zur Datenbank herstellen
        with get_db_connection() as conn:
            # Cursor erstellen
            cursor = conn.cursor()

            # SQL-Abfrage ausführen
            cursor.execute(sql_query)

            # Ergebnisse abrufen
            columns = [desc[0].strip() for desc in cursor.description]
            results = []

            for row in cursor.fetchall():
                result_dict = {columns[i]: value for i, value in enumerate(row)}
                results.append(result_dict)

            logger.info(f"SQL-Ausführung erfolgreich: {len(results)} Ergebnisse")
            return results
    except Exception as e:
        logger.error(f"Fehler bei der SQL-Ausführung: {str(e)}")
        # Fehler weiterleiten statt leere Liste zurückzugeben
        raise
