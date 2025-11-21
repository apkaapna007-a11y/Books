import os
import sys
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
MODEL_NAME = os.getenv("HF_MODEL", "BAAI/bge-small-en-v1.5")
TABLE = os.getenv("TABLE", "public.nelson_book_contents")

if len(sys.argv) < 2:
    print("Usage: python validate_similarity_hf.py \"your query text\"")
    sys.exit(1)

q = sys.argv[1]
model = SentenceTransformer(MODEL_NAME)
query_vec = model.encode([q], normalize_embeddings=True)[0].tolist()

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            select id, title, chunk_no,
                   1 - (embedding <=> %s) as similarity_score
            from {TABLE}
            where embedding is not null
            order by embedding <=> %s
            limit 10
            """,
            (query_vec, query_vec),
        )
        rows = cur.fetchall()
        for r in rows:
            print(f"id={r['id']}, chunk={r['chunk_no']}, score={r['similarity_score']:.4f}, title={r['title']}")
