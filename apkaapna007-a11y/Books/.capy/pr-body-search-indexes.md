This PR adds search indexing and query examples for the nelson_book_contents table.

Files
- sql/add_search_indexes.sql
  - Enables pg_trgm and unaccent
  - GIN index on meta (jsonb)
  - GIN trigram indexes on content and summary
  - Generated column search_fts (weighted tsvector over title/topic/subtopic/summary/content)
  - GIN index on search_fts
- sql/search_examples.sql
  - Vector similarity with pgvector
  - Full-text search (plainto_tsquery and to_tsquery examples)
  - Trigram fuzzy matching
  - JSONB meta filters
  - Hybrid FTS prefilter + vector rerank

Usage
1) Run sql/add_search_indexes.sql on your Supabase database (after pgvector_setup.sql).
2) Use queries from sql/search_examples.sql to test search flows.

No data changes.
