import json
from pathlib import Path

import fdb

db_path = Path("./data/WINCASA2022.FDB").resolve()
output_file = Path("./data/firebird_schema_overview.json").resolve()

con = fdb.connect(dsn=str(db_path), user="SYSDBA", password="masterkey")
cur = con.cursor()

cur.execute(
    """
    SELECT rdb$relation_name
    FROM rdb$relations
    WHERE rdb$system_flag = 0
"""
)
tables = [row[0].strip() for row in cur.fetchall()]

schema = {}

for table in tables:
    cur.execute(
        f"""
        SELECT rf.rdb$field_name, f.rdb$field_type, f.rdb$field_length
        FROM rdb$relation_fields rf
        JOIN rdb$fields f ON rf.rdb$field_source = f.rdb$field_name
        WHERE rf.rdb$relation_name = '{table}'
    """
    )
    schema[table] = [
        {"column": r[0].strip(), "type": r[1], "length": r[2]} for r in cur.fetchall()
    ]

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)

print(f"Export abgeschlossen: {output_file}")
