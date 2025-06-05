# query_memory.py
import datetime
import json
import os
from pathlib import Path

# Speicherort relativ zum Skriptverzeichnis
MEMORY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "output/memory"))
Path(MEMORY_DIR).mkdir(parents=True, exist_ok=True)

SUCCESS_FILE = os.path.join(MEMORY_DIR, "successful_queries.jsonl")
FAILED_FILE = os.path.join(MEMORY_DIR, "failed_queries.jsonl")
CORRECTIONS_FILE = os.path.join(MEMORY_DIR, "prompt_corrections.jsonl")


def append_to_memory(path, prompt, sql, comment=None):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "prompt": prompt,
        "sql": sql,
        "comment": comment,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_success(prompt, sql, comment=None):
    append_to_memory(SUCCESS_FILE, prompt, sql, comment)


def log_failure(prompt, sql, error):
    append_to_memory(FAILED_FILE, prompt, sql, comment=error)


def log_manual_correction(original_prompt, corrected_sql):
    append_to_memory(
        CORRECTIONS_FILE, original_prompt, corrected_sql, comment="manual correction"
    )
