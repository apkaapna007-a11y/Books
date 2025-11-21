-- Enable required extensions
create extension if not exists vector;
create extension if not exists moddatetime;

-- Create table if it does not exist
create table if not exists public.nelson_book_contents (
  id bigint generated always as identity primary key,
  meta jsonb,
  index_path text,
  title text,
  topic text,
  subtopic text,
  content text,
  summary text,
  chunk_no int,
  embedding vector(1536),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Ensure embedding column exists with correct dimension
alter table public.nelson_book_contents
  add column if not exists embedding vector(1536);

-- Trigger to auto-update updated_at
do $$ begin
  if not exists (
    select 1 from pg_trigger where tgname = 'handle_updated_at') then
    create trigger handle_updated_at
    before update on public.nelson_book_contents
    for each row execute procedure moddatetime (updated_at);
  end if;
end $$;
