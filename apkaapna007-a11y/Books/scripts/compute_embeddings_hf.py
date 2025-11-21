import os
import sys
import time
from typing import List, Tuple

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
MODEL_NAME = os.getenv("HF_MODEL", "BAAI/bge-small-en-v1.5")  # 384-d
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "128"))
SLEEP_BETWEEN = float(os.getenv("SLEEP_BETWEEN", "0.2"))
TABLE = os.getenv("TABLE", "public.nelson_book_contents")
CONTENT_COL = os.getenv("CONTENT_COL", "content")
ID_COL = os.getenv("ID_COL", "id")
EMBED_COL = os.getenv("EMBED_COL", "embedding")
NORMALIZE = os.getenv("NORMALIZE", "true").lower() == "true"
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

if not DATABASE_URL:
    print("DATABASE_URL is required", file=sys.stderr)
    sys.exit(1)

print(f"Loading model {MODEL_NAME} ...", file=sys.stderr)
model = SentenceTransformer(MODEL_NAME)


def fetch_batch(conn) -> List[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            select {ID_COL} as id, {CONTENT_COL} as content
            from {TABLE}
            where {EMBED_COL} is null and coalesce(length({CONTENT_COL}),0) > 0
            order by {ID_COL}
            limit %s
            """,
            (BATCH_SIZE,),
        )
        return list(cur.fetchall())


def embed_texts(texts: List[str]) -> List[List[float]]:
    embs = model.encode(texts, batch_size=min(32, len(texts)), show_progress_bar=False, normalize_embeddings=NORMALIZE)
    if isinstance(embs, np.ndarray):
        embs = embs.tolist()
    return embs


def update_embeddings(conn, pairs: List[Tuple[int, List[float]]]):
    with conn.cursor() as cur:
        cur.executemany(
            f"update {TABLE} set {EMBED_COL} = %s where {ID_COL} = %s",
            [(emb, _id) for _id, emb in pairs],
        )
    conn.commit()


def main():
    total = 0
    with psycopg.connect(DATABASE_URL) as conn:
        while True:
            batch = fetch_batch(conn)
            if not batch:
                break
            ids = [r["id"] for r in batch]
            texts = [r["content"] for r in batch]
            if DRY_RUN:
                print(f"[DRY_RUN] Would embed {len(ids)} rows; first id={ids[0]}")
                break
            embs = embed_texts(texts)
            update_embeddings(conn, list(zip(ids, embs)))
            total += len(ids)
            print(f"Updated {len(ids)} rows (total {total})")
            time.sleep(SLEEP_BETWEEN)
    print(f"Done. Total updated: {total}")

if __name__ == "__main__":
    main()
