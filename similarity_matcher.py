# similarity_matcher.py
import json
import os
import numpy as np
from embedding_interface import EmbeddingInterface
from pathlib import Path

# Speicherpfade
base_dir = os.path.dirname(__file__)
memory_dir = os.path.abspath(os.path.join(base_dir, "../memory"))

success_file = os.path.join(memory_dir, "successful_queries.jsonl")
failed_file = os.path.join(memory_dir, "failed_queries.jsonl")
suggestions_file = os.path.join(memory_dir, "suggested_corrections.jsonl")

# Cosine Similarity ohne sklearn
def cosine_similarity_vec(a, b):
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# Embedding-Modul laden
embedder = EmbeddingInterface()

# Lade erfolgreiche Prompts
with open(success_file, "r", encoding="utf-8") as f:
    successful = [json.loads(line) for line in f if line.strip()]

# Lade fehlgeschlagene Prompts
with open(failed_file, "r", encoding="utf-8") as f:
    failed = [json.loads(line) for line in f if line.strip()]

# Embedding aller erfolgreichen Prompts vorbereiten
success_embeddings = []
success_prompts = []
success_sqls = []

for entry in successful:
    emb = embedder.embed(entry["prompt"])
    success_embeddings.append(emb)
    success_prompts.append(entry["prompt"])
    success_sqls.append(entry["sql"])

# Ergebnisse schreiben
Path(suggestions_file).parent.mkdir(parents=True, exist_ok=True)

with open(suggestions_file, "w", encoding="utf-8") as out:
    for entry in failed:
        fail_prompt = entry["prompt"]
        fail_emb = embedder.embed(fail_prompt)

        # Ähnlichkeitsvergleich
        sims = [cosine_similarity_vec(fail_emb, s_emb) for s_emb in success_embeddings]
        best_idx = int(np.argmax(sims))
        best_prompt = success_prompts[best_idx]
        best_sql = success_sqls[best_idx]
        best_score = sims[best_idx]

        suggestion = {
            "prompt": fail_prompt,
            "match_prompt": best_prompt,
            "similarity": round(best_score, 4),
            "suggested_sql": best_sql,
            "comment": "Basierend auf ähnlichstem erfolgreichen Prompt"
        }
        out.write(json.dumps(suggestion, ensure_ascii=False) + "\n")
        print(f"✅ Vorschlag für: {fail_prompt}\n→ {best_prompt} (Score: {best_score:.2f})\n")