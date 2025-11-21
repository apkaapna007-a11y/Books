# Embedding pipeline for nelson_book_contents

This folder contains scripts to compute 1536‑d embeddings for each chunk and validate similarity search.

## Setup

1) Install deps:

```
pip install -r scripts/requirements.txt
```

2) Set environment variables (e.g. in a `.env` file):

```
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
# Optional tuning
BATCH_SIZE=100
SLEEP_BETWEEN=0.5
MAX_RETRIES=5
TABLE=public.nelson_book_contents
```

## Compute embeddings

This fills the `embedding vector(1536)` column for any rows where it is NULL.

```
python scripts/compute_embeddings.py
```

You can test run without updating by setting `DRY_RUN=true`.

## Validate similarity

Run a quick top‑K vector similarity query:

```
python scripts/validate_similarity.py "asthma corticosteroid"
```

This prints top matches using `1 - (embedding <=> query_embedding)` as the score.

## Notes
- Ensure you've run `sql/pgvector_setup.sql` and imported `uploads/chunks.csv` into `public.nelson_book_contents`.
- Indexes in `sql/add_search_indexes.sql` improve search performance for JSONB, trigram, and FTS.
