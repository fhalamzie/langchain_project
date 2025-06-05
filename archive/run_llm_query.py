# run_llm_query.py
import datetime
import decimal
import json
import os

from query_logger import log_query_result
from query_memory import log_failure, log_success
from query_router import execute_safe_sql

from llm_interface import LLMInterface


class SafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except UnicodeDecodeError:
                return obj.decode("latin-1", errors="replace")
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


# Schema laden
try:
    base_dir = os.path.dirname(__file__)
    schema_path = os.path.abspath(
        os.path.join(base_dir, "output/wincasa_schema_summary.yaml")
    )

    # Prüfen, ob die Schemadatei existiert
    if not os.path.exists(schema_path):
        # Alternative Pfade probieren
        alternative_paths = [
            os.path.join(base_dir, "wincasa_schema_summary.yaml"),
            os.path.join(base_dir, "../wincasa_schema_summary.yaml"),
        ]

        for path in alternative_paths:
            if os.path.exists(path):
                schema_path = path
                break

    # Schema laden wenn vorhanden
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_text = f.read()
        print(f"Schema geladen von: {schema_path}")
    else:
        schema_text = "Schema nicht gefunden."
        print(
            f"⚠️ Schema-Datei konnte nicht gefunden werden. Versucht wurden: {schema_path} und {alternative_paths}"
        )
except Exception as e:
    schema_text = f"Fehler beim Laden des Schemas: {str(e)}"
    print(f"❌ {schema_text}")

# Nutzerprompt eingeben
prompt = (
    input("Was möchtest du wissen? ")
    + "\nAntworte bitte ausschließlich mit SQL-Code. Kein Erklärungstext, keine Formatierung, kein Markdown."
)

# LLM initialisieren
llm = LLMInterface()

try:
    sql = llm.generate_sql(prompt, schema_text)
    print("\nGenerierte SQL:")
    print(sql)

    result = execute_safe_sql(sql)

    for i, row in enumerate(result[:3]):
        safe_row = {
            k: (
                v.decode("utf-8", errors="replace")
                if isinstance(v, bytes)
                else (
                    float(v)
                    if isinstance(v, decimal.Decimal)
                    else (
                        v.isoformat()
                        if isinstance(v, (datetime.date, datetime.datetime))
                        else v
                    )
                )
            )
            for k, v in row.items()
        }
        print(json.dumps(safe_row, ensure_ascii=False))

    log_query_result(prompt, sql, result, success=True)
    log_success(prompt, sql)

except Exception as e:
    print("\n❌ Fehler:", str(e))
    log_query_result(
        prompt, sql if "sql" in locals() else None, None, success=False, error=str(e)
    )
    log_failure(prompt, sql if "sql" in locals() else None, error=str(e))
