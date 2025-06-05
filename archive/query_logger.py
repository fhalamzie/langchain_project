# query_logger.py
import datetime
import json
import os
from pathlib import Path


def ensure_log_dir():
    """Stellt sicher, dass das Protokollverzeichnis existiert"""
    log_dir = Path("output/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def log_query_result(prompt, sql, result, success=True, error=None):
    """
    Protokolliert das Ergebnis einer Abfrage

    Args:
        prompt: Die ursprüngliche Benutzerabfrage
        sql: Die generierte SQL-Abfrage
        result: Das Ergebnis der Abfrage
        success: Ob die Abfrage erfolgreich war
        error: Fehlermeldung, falls vorhanden
    """
    try:
        log_dir = ensure_log_dir()

        # Erstelle einen Zeitstempel für den Dateinamen
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"query_log_{timestamp}.json"

        # Erstelle eine JSON-serialisierbare Version des Ergebnisses
        safe_result = []
        if result and success:
            for row in result[:10]:  # Begrenze auf 10 Zeilen für die Protokollierung
                safe_row = {}
                for key, value in row.items():
                    # Konvertiere nicht-serialisierbare Typen
                    if isinstance(value, (datetime.date, datetime.datetime)):
                        safe_row[key] = value.isoformat()
                    elif isinstance(value, bytes):
                        try:
                            safe_row[key] = value.decode("utf-8")
                        except UnicodeDecodeError:
                            safe_row[key] = value.decode("latin-1", errors="replace")
                    else:
                        safe_row[key] = str(value)
                safe_result.append(safe_row)

        # Erstelle das Protokollobjekt
        log_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "prompt": prompt,
            "sql": sql,
            "success": success,
            "error": error,
            "result": safe_result if success else None,
            "result_count": len(result) if result and success else 0,
        }

        # Speichere das Protokoll
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

        print(f"Abfrage protokolliert: {log_file}")

    except Exception as e:
        print(f"Fehler beim Protokollieren der Abfrage: {str(e)}")
