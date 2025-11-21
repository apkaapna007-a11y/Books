-- Similarity search with pgvector (provide a 1536-d embedding as :query_embedding)
-- order by smaller distance is closer; convert to a cosine-like score if desired
select id, title, chunk_no,
       1 - (embedding <=> :query_embedding) as similarity_score
from public.nelson_book_contents
where embedding is not null
order by embedding <=> :query_embedding
limit 10;

-- Full-text search using plainto_tsquery (best for user-entered text)
select id, title, chunk_no,
       ts_rank_cd(search_fts, plainto_tsquery('english', :q)) as rank
from public.nelson_book_contents
where search_fts @@ plainto_tsquery('english', :q)
order by rank desc
limit 20;

-- Full-text search using to_tsquery (supports operators: & | ! and * for prefix)
-- Example :q => 'asthma & corticosteroid'
select id, title, chunk_no,
       ts_rank(search_fts, to_tsquery('english', :q)) as rank
from public.nelson_book_contents
where search_fts @@ to_tsquery('english', :q)
order by rank desc
limit 20;

-- Trigram fuzzy match (substring / misspellings)
-- Adjust threshold: select set_limit(0.2); -- or set pg_trgm.similarity_threshold = 0.2;
select id, title, chunk_no,
       greatest(similarity(content, :q), similarity(summary, :q)) as trigram_sim
from public.nelson_book_contents
where content ilike '%' || :q || '%' or summary ilike '%' || :q || '%'
order by trigram_sim desc nulls last
limit 20;

-- Filter by JSONB meta
select id, title, chunk_no
from public.nelson_book_contents
where meta->>'source_file' = :source_file
limit 10;

-- Hybrid: FTS prefilter then vector rerank
with fts as (
  select id
  from public.nelson_book_contents
  where search_fts @@ plainto_tsquery('english', :q)
  limit 100
)
select n.id, n.title, n.chunk_no,
       1 - (n.embedding <=> :query_embedding) as similarity_score
from fts
join public.nelson_book_contents n using (id)
where n.embedding is not null
order by similarity_score desc
limit 10;
