import argparse
import decimal
import json
from datetime import date, datetime

import firebird.driver as driver

class EnhancedJSONEncoder(json.JSONEncoder):
    """Erweiterter JSON-Encoder, der zusätzliche Python-Typen unterstützt.
    
    Diese Klasse erweitert den Standard-JSON-Encoder, um Decimal und Datetime-Objekte
    korrekt zu serialisieren.
    """

    def default(self, obj: object) -> object:
        """Serialisiert zusätzliche Python-Typen.
        
        Args:
            obj: Das zu serialisierende Objekt
            
        Returns:
            Ein JSON-serialisierbares Objekt
        """
        if isinstance(obj, decimal.Decimal):
            return float(obj)

        if isinstance(obj, (date, datetime)):
            return obj.isoformat()

        return super().default(obj)


def is_valid_identifier(name: str) -> bool:
    """Validiert, dass ein Bezeichner nur erlaubte Zeichen enthält.
    
    Args:
        name: Der zu prüfende Bezeichner
        
    Returns:
        bool: True, wenn der Bezeichner gültig ist, sonst False
    """
    import re
    return bool(re.match(r'^[A-Za-z0-9_$]+$', name))


def extract_data(db_path, user, password, output_path):
    """
    Extrahiert Daten aus einer Firebird-Datenbank und speichert sie als JSON.

    Args:
        db_path (str): Pfad zur .FDB-Datei.
        user (str): Datenbank-Benutzername.
        password (str): Datenbank-Passwort.
        output_path (str): Pfad zur Ausgabe-JSON-Datei.
    """
    try:
        # === VERBINDUNG ZUR FIREBIRD-DATENBANK ===
        with driver.connect(
            database=db_path,
            user=user,
            password=password,
        ) as con:

            export = {}

            # === TABELLEN & DATEN ===
            tables_data = {}

            with con.cursor() as cur:
                cur.execute(
                    """
                    SELECT rdb$relation_name
                    FROM rdb$relations
                    WHERE rdb$system_flag = 0 AND rdb$view_blr IS NULL
                    """
                )
                tables = [row[0].strip() for row in cur.fetchall()]

            for table in tables:
                # Sicherheitsüberprüfung für Tabellennamen
                if not is_valid_identifier(table):
                    print(f"Warnhinweis: Überspringe Tabelle mit unsicherem Namen: {table}")
                    continue

                with con.cursor() as cur:
                    # Spalten abrufen
                    cur.execute(
                        """
                        SELECT
                            rf.rdb$field_name,
                            f.rdb$field_type,
                            f.rdb$field_length,
                            f.rdb$field_precision,
                            f.rdb$field_scale,
                            f.rdb$null_flag
                        FROM rdb$relation_fields rf
                        JOIN rdb$fields f ON rf.rdb$field_source = f.rdb$field_name
                        WHERE rf.rdb$relation_name = ?
                        ORDER BY rf.rdb$field_position
                        """,
                        (table,)
                    )
                    columns = [col[0].strip() for col in cur.fetchall()]

                    try:
                        # Escaping des Tabellennamens für die SQL-Abfrage
                        # Da Tabellennamen nicht als Parameter übergeben werden können
                        table_quoted = table.replace('"', '""')
                        query = f'SELECT FIRST 1000 * FROM "{table_quoted}"'
                        cur.execute(query)

                        rows = cur.fetchall()
                        row_dicts = [dict(zip(columns, row)) for row in rows]

                    except Exception as e:
                        row_dicts = f"Fehler beim Abrufen: {str(e)}"

                    tables_data[table] = {"columns": columns, "rows": row_dicts}

            # === STORED PROCEDURES ===
            procedures_data = {}

            with con.cursor() as cur:
                cur.execute("SELECT rdb$procedure_name FROM rdb$procedures")
                procedure_names = [row[0].strip() for row in cur.fetchall()]

            for proc in procedure_names:
                # Sicherheitsüberprüfung für Prozedurnamen
                if not is_valid_identifier(proc):
                    print(f"Warnhinweis: Überspringe Prozedur mit unsicherem Namen: {proc}")
                    continue

                with con.cursor() as cur:
                    # Abfrage der Prozedurquelle mit Parameter
                    cur.execute(
                        """
                        SELECT rdb$procedure_source
                        FROM rdb$procedures
                        WHERE rdb$procedure_name = ?
                        """,
                        (proc,)
                    )
                    body = cur.fetchone()
                    body = body[0].strip() if body and body[0] else ""

                    # Abfrage der Prozedurparameter mit Parameter
                    cur.execute(
                        """
                        SELECT
                            rdb$parameter_name,
                            rdb$parameter_type,
                            rdb$field_source
                        FROM rdb$procedure_parameters
                        WHERE rdb$procedure_name = ?
                        ORDER BY rdb$parameter_type, rdb$parameter_number
                        """,
                        (proc,)
                    )
                    params = cur.fetchall()
                    param_list = []
                    for p in params:
                        name = p[0].strip()
                        direction = "IN" if p[1] == 0 else "OUT"
                        field_source = p[2].strip()
                        param_list.append({
                            "name": name,
                            "direction": direction,
                            "type": field_source
                        })

                    procedures_data[proc] = {"parameters": param_list, "body": body}

            export["tables"] = tables_data
            export["stored_procedures"] = procedures_data

        # === EXPORT SCHREIBEN ===
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export, f, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)

        print(f"Export abgeschlossen: {output_path}")

    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")


if __name__ == "__main__":
    # === ARGUMENTE PARSEN (optional überschreibbar per CLI) ===
    parser = argparse.ArgumentParser(description="Exportiere Firebird-Datenbank nach JSON")

    parser.add_argument(
        "--db",
        default="home/projects/venv-ai/data/WINCASA2022.FDB",
        help="Pfad zur .FDB-Datei",
    )

    parser.add_argument(
        "--out", default="wincasa_export.json", help="Pfad zur Ausgabe-JSON-Datei"
    )

    parser.add_argument("--user", default="sysdba", help="Datenbank-Benutzername")

    parser.add_argument("--password", default="masterkey", help="Datenbank-Passwort")

    args = parser.parse_args()

    extract_data(args.db, args.user, args.password, args.out)
