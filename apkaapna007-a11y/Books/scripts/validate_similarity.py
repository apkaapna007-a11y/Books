import os
import sys
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    print("Please 'pip install openai'", file=sys.stderr)
    raise

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
TABLE = os.getenv("TABLE", "public.nelson_book_contents")

if len(sys.argv) < 2:
    print("Usage: python validate_similarity.py \"your query text\"")
    sys.exit(1)

q = sys.argv[1]

client = OpenAI(api_key=OPENAI_API_KEY)

resp = client.embeddings.create(model=MODEL, input=q)
query_vec = resp.data[0].embedding

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
