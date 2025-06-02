import firebird.driver as driver

import json

import decimal

import argparse

from datetime import date, datetime


# === ARGUMENTE PARSEN (optional überschreibbar per CLI) ===
ip
parser = argparse.ArgumentParser(description="Exportiere Firebird-Datenbank nach JSON")

parser.add_argument("--db", default="home/projects/venv-ai/data/WINCASA2022.FDB", help="Pfad zur .FDB-Datei")

parser.add_argument("--out", default="wincasa_export.json", help="Pfad zur Ausgabe-JSON-Datei")

parser.add_argument("--user", default="sysdba", help="Datenbank-Benutzername")

parser.add_argument("--password", default="masterkey", help="Datenbank-Passwort")

args = parser.parse_args()







class EnhancedJSONEncoder(json.JSONEncoder):

    def default(self, obj):

        if isinstance(obj, decimal.Decimal):

            return float(obj)

        if isinstance(obj, (date, datetime)):

            return obj.isoformat()

        return super().default(obj)



# === VERBINDUNG ZUR FIREBIRD-DATENBANK ===

with driver.connect(

    database=args.db,

    user=args.user,

    password=args.password,

) as con:

    export = {}



    # === TABELLEN & DATEN ===

    tables_data = {}



    with con.cursor() as cur:

        cur.execute("""

            SELECT rdb$relation_name

            FROM rdb$relations

            WHERE rdb$system_flag = 0 AND rdb$view_blr IS NULL

        """)

        tables = [row[0].strip() for row in cur.fetchall()]



    for table in tables:

        with con.cursor() as cur:

            # Spalten abrufen

            cur.execute(f"""

                SELECT

                    rf.rdb$field_name,

                    f.rdb$field_type,

                    f.rdb$field_length,

                    f.rdb$field_precision,

                    f.rdb$field_scale,

                    f.rdb$null_flag

                FROM rdb$relation_fields rf

                JOIN rdb$fields f ON rf.rdb$field_source = f.rdb$field_name

                WHERE rf.rdb$relation_name = '{table}'

                ORDER BY rf.rdb$field_position

            """)

            columns = [col[0].strip() for col in cur.fetchall()]



            try:

                cur.execute(f'SELECT FIRST 1000 * FROM "{table}"')

                rows = cur.fetchall()

                row_dicts = [dict(zip(columns, row)) for row in rows]

            except Exception as e:

                row_dicts = f"Fehler beim Abrufen: {str(e)}"



            tables_data[table] = {

                "columns": columns,

                "rows": row_dicts

            }



    # === STORED PROCEDURES ===

    procedures_data = {}



    with con.cursor() as cur:

        cur.execute("SELECT rdb$procedure_name FROM rdb$procedures")

        procedure_names = [row[0].strip() for row in cur.fetchall()]



    for proc in procedure_names:

        with con.cursor() as cur:

            cur.execute(f"""

                SELECT rdb$procedure_source

                FROM rdb$procedures

                WHERE rdb$procedure_name = '{proc}'

            """)

            body = cur.fetchone()

            body = body[0].strip() if body and body[0] else ""



            cur.execute(f"""

                SELECT

                    rdb$parameter_name,

                    rdb$parameter_type,

                    rdb$field_source

                FROM rdb$procedure_parameters

                WHERE rdb$procedure_name = '{proc}'

                ORDER BY rdb$parameter_type, rdb$parameter_number

            """)

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



            procedures_data[proc] = {

                "parameters": param_list,

                "body": body

            }



    export["tables"] = tables_data

    export["stored_procedures"] = procedures_data



# === EXPORT SCHREIBEN ===

with open(args.out, "w", encoding="utf-8") as f:

    json.dump(export, f, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)



print(f"Export abgeschlossen: {args.out}")

