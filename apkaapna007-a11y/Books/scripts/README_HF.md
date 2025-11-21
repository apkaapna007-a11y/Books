# Hugging Face Embeddings (free)

This pipeline computes free embeddings using a Hugging Face model (default: `BAAI/bge-small-en-v1.5`, 384-d) and stores them in `embedding vector(384)`.

## Setup

1) Apply schema change to use 384-d vectors (only needed once):

```
\i sql/pgvector_switch_to_384.sql
```

2) Install dependencies (CPU):

```
pip install -r scripts/requirements_hf.txt
```

3) Environment

```
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DB
HF_MODEL=BAAI/bge-small-en-v1.5   # or sentence-transformers/all-MiniLM-L6-v2
BATCH_SIZE=128
SLEEP_BETWEEN=0.2
TABLE=public.nelson_book_contents
```

## Compute embeddings

```
python scripts/compute_embeddings_hf.py
```

## Validate

```
python scripts/validate_similarity_hf.py "asthma corticosteroid"
```

Notes
- 384 dims are typical for efficient HF models. If you prefer 768 dims, switch to `BAAI/bge-base-en-v1.5` and change the column to `vector(768)`.
- Embeddings are normalized for cosine similarity. The pgvector operator `<=>` computes Euclidean distance; with normalized vectors, ordering matches cosine similarity.
