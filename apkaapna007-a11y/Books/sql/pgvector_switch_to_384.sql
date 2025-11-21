-- Switch embedding column to vector(384) for Hugging Face models like BAAI/bge-small-en-v1.5 or all-MiniLM-L6-v2
-- Safe if column is currently NULL everywhere; otherwise, back up values if needed.

alter table public.nelson_book_contents
  drop column if exists embedding;

alter table public.nelson_book_contents
  add column embedding vector(384);
