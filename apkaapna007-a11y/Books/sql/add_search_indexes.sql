-- Enable helpful extensions
create extension if not exists pg_trgm;
create extension if not exists unaccent;

-- 1) JSONB GIN index for meta queries
create index if not exists nelson_meta_gin on public.nelson_book_contents using gin (meta);

-- 2) Trigram GIN indexes for fuzzy substring/similarity search
create index if not exists nelson_content_trgm_gin on public.nelson_book_contents using gin (content gin_trgm_ops);
create index if not exists nelson_summary_trgm_gin on public.nelson_book_contents using gin (summary gin_trgm_ops);

-- 3) Full-text search: generated tsvector over weighted fields
alter table public.nelson_book_contents
  add column if not exists search_fts tsvector
  generated always as (
    setweight(to_tsvector('english', coalesce(unaccent(title),'')),   'A') ||
    setweight(to_tsvector('english', coalesce(unaccent(topic),'')),   'B') ||
    setweight(to_tsvector('english', coalesce(unaccent(subtopic),'')),'B') ||
    setweight(to_tsvector('english', coalesce(unaccent(summary),'')), 'C') ||
    setweight(to_tsvector('english', coalesce(unaccent(content),'')), 'D')
  ) stored;

-- 4) GIN index for full-text search
create index if not exists nelson_search_fts_gin on public.nelson_book_contents using gin (search_fts);
