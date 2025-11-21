import os
import sys
import time
import json
import math
from typing import List, Tuple

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception as e:
    print("Please 'pip install openai'", file=sys.stderr)
    raise

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")  # 1536-d
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
SLEEP_BETWEEN = float(os.getenv("SLEEP_BETWEEN", "0.5"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
TABLE = os.getenv("TABLE", "public.nelson_book_contents")
CONTENT_COL = os.getenv("CONTENT_COL", "content")
ID_COL = os.getenv("ID_COL", "id")
EMBED_COL = os.getenv("EMBED_COL", "embedding")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"

if not DATABASE_URL:
    print("DATABASE_URL is required", file=sys.stderr)
    sys.exit(1)
if not OPENAI_API_KEY:
    print("OPENAI_API_KEY is required", file=sys.stderr)
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)


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
    # Backoff on rate limits
    delay = 1.0
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.embeddings.create(model=MODEL, input=texts)
            # Ensure correct ordering
            embs = [d.embedding for d in resp.data]
            return embs
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            time.sleep(delay)
            delay = min(delay * 2, 20)


def update_embeddings(conn, pairs: List[Tuple[int, List[float]]]):
    # Update using executemany
    with conn.cursor() as cur:
        cur.executemany(
            f"update {TABLE} set {EMBED_COL} = %s where {ID_COL} = %s",
            [(emb, _id) for _id, emb in pairs],
        )
    conn.commit()


def main():
    total_updated = 0
    with psycopg.connect(DATABASE_URL) as conn:
        while True:
            batch = fetch_batch(conn)
            if not batch:
                break
            ids = [row["id"] for row in batch]
            texts = [row["content"] for row in batch]
            if DRY_RUN:
                print(f"[DRY_RUN] Would embed and update {len(ids)} rows; first id={ids[0]}")
                total_updated += len(ids)
                break
            # Create embeddings in one request (batched)
            embs = embed_texts(texts)
            pairs = list(zip(ids, embs))
            update_embeddings(conn, pairs)
            total_updated += len(ids)
            print(f"Updated {len(ids)} rows (total {total_updated})")
            time.sleep(SLEEP_BETWEEN)
    print(f"Done. Total updated: {total_updated}")


if __name__ == "__main__":
    main()
