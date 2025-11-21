# Nelson Textbook of Pediatrics - Structured Dataset

## Overview

This dataset contains structured, chunked content from the Nelson Textbook of Pediatrics, 22nd Edition, optimized for vector search and Retrieval-Augmented Generation (RAG) applications.

## Dataset Statistics

- **Total Chunks**: 27,624
- **Source Files**: 27 text files
- **Book Title**: Nelson Textbook of Pediatrics
- **Edition**: 22nd Edition
- **Output Format**: CSV with UTF-8 encoding

## CSV Schema

The dataset is structured with the following columns:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `book_title` | String | Title of the textbook | "Nelson Textbook of Pediatrics" |
| `book_edition` | String | Edition number | "22" |
| `chapter_number` | String | Chapter number (if identified) | "182", "19" |
| `chapter_title` | String | Chapter title (if identified) | "Allergy", "Developmental" |
| `section_number` | String | Section number (if identified) | "182.1", "19.2" |
| `section_title` | String | Section title (if identified) | "Introduction", "Clinical Manifestations" |
| `subsection_number` | String | Subsection number (if identified) | "182.1.1" |
| `subsection_title` | String | Subsection title (if identified) | "Pathophysiology" |
| `chunk_number` | Integer | Sequential chunk number within section | 1, 2, 3... |
| `content` | String | Main content text (200-800 tokens) | Medical text content |
| `summary` | String | Auto-generated summary (1-2 sentences) | Brief description of chunk content |

## Content Processing

### Chunking Strategy
- **Target Size**: 200-800 tokens per chunk
- **Boundary Respect**: Chunks respect sentence boundaries
- **Minimum Length**: 50 characters minimum content length
- **Token Estimation**: ~3 characters per token

### Text Cleaning
- Special character encoding fixed (M-bM-^@M-^Y → apostrophe, M-BM-- → em-dash, etc.)
- Excessive whitespace normalized
- Medical terminology and drug names preserved exactly
- References and citations maintained where critical

### Hierarchical Structure Extraction
- **PART**: Roman numerals (I, II, III, etc.) with titles
- **Chapter**: Numeric chapters with titles
- **Section**: Numbered sections within chapters
- **Subsection**: Multi-level numbered subsections

## Usage for Supabase Vector Search

### 1. Database Setup

```sql
-- Create table for the textbook content
CREATE TABLE nelson_textbook (
  id BIGSERIAL PRIMARY KEY,
  book_title TEXT,
  book_edition TEXT,
  chapter_number TEXT,
  chapter_title TEXT,
  section_number TEXT,
  section_title TEXT,
  subsection_number TEXT,
  subsection_title TEXT,
  chunk_number INTEGER,
  content TEXT,
  summary TEXT,
  embedding VECTOR(1536), -- For OpenAI embeddings
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX ON nelson_textbook USING GIN (to_tsvector('english', content));
CREATE INDEX ON nelson_textbook (chapter_number);
CREATE INDEX ON nelson_textbook (section_number);
```

### 2. Import Data

```bash
# Import CSV into Supabase
psql -h your-supabase-host -U postgres -d your-database \
  -c "\COPY nelson_textbook(book_title, book_edition, chapter_number, chapter_title, section_number, section_title, subsection_number, subsection_title, chunk_number, content, summary) FROM 'nelson_textbook_structured.csv' WITH CSV HEADER;"
```

### 3. Generate Embeddings

```python
import openai
import pandas as pd
from supabase import create_client

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

# Function to generate embeddings
def generate_embedding(text):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']

# Update records with embeddings
def update_embeddings():
    # Get records without embeddings
    result = supabase.table('nelson_textbook').select('id, content').is_('embedding', 'null').execute()
    
    for record in result.data:
        embedding = generate_embedding(record['content'])
        supabase.table('nelson_textbook').update({
            'embedding': embedding
        }).eq('id', record['id']).execute()
```

### 4. Vector Search Queries

```sql
-- Semantic search function
CREATE OR REPLACE FUNCTION search_nelson_textbook(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.8,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id BIGINT,
  content TEXT,
  summary TEXT,
  chapter_title TEXT,
  section_title TEXT,
  similarity FLOAT
)
LANGUAGE SQL
AS $$
  SELECT
    id,
    content,
    summary,
    chapter_title,
    section_title,
    1 - (embedding <=> query_embedding) AS similarity
  FROM nelson_textbook
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
```

## RAG Pipeline Integration

### Example Query Processing

```python
def query_nelson_textbook(question: str, max_results: int = 5):
    # Generate embedding for the question
    question_embedding = generate_embedding(question)
    
    # Search for relevant chunks
    results = supabase.rpc('search_nelson_textbook', {
        'query_embedding': question_embedding,
        'match_threshold': 0.7,
        'match_count': max_results
    }).execute()
    
    # Format context for LLM
    context = "\n\n".join([
        f"Chapter: {r['chapter_title']}\nSection: {r['section_title']}\nContent: {r['content']}"
        for r in results.data
    ])
    
    return context

# Example usage
question = "What are the symptoms of asthma in children?"
context = query_nelson_textbook(question)
```

### Prompt Template

```python
SYSTEM_PROMPT = """You are a pediatric medical assistant with access to the Nelson Textbook of Pediatrics. 
Provide accurate, evidence-based answers using the provided context. Always cite the relevant chapter/section when possible.
If the context doesn't contain sufficient information, clearly state this limitation."""

def generate_response(question: str, context: str):
    prompt = f"""
Context from Nelson Textbook of Pediatrics:
{context}

Question: {question}

Please provide a comprehensive answer based on the context above.
"""
    
    # Send to your preferred LLM (OpenAI, Anthropic, etc.)
    return llm_response
```

## Quality Considerations

### Strengths
- Hierarchical structure preserved for better context
- Medical terminology maintained accurately
- Appropriate chunk sizes for embedding models
- Comprehensive coverage of pediatric medicine topics

### Limitations
- Some structural elements may be missed due to formatting variations
- Tables and figures are converted to text descriptions
- Cross-references between sections may be incomplete
- OCR artifacts may remain in some content

## File Structure

```
├── nelson_textbook_structured.csv    # Main dataset
├── convert_to_structured_csv.py       # Processing script
├── requirements.txt                   # Dependencies
└── DATASET_README.md                 # This documentation
```

## License and Usage

This dataset is derived from the Nelson Textbook of Pediatrics and should be used in accordance with appropriate medical and educational guidelines. Ensure compliance with copyright and licensing requirements for your specific use case.

## Support

For questions about the dataset structure or processing methodology, refer to the conversion script `convert_to_structured_csv.py` which contains detailed documentation of the processing pipeline.

