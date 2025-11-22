# Pinecone Upload Information

## Upload Status

The nelson_textbook_structured_final.csv file is currently being uploaded to Pinecone.

### Process Details

- **CSV File**: nelson_textbook_structured_final.csv
- **Total Records**: 31,009 medical text chunks
- **Pinecone Index**: nelson-textbook
- **API Key**: pcsk_39ZEMz_LbNYBJVtxJT7unE8ctWFyiKyodkcJs6kas9ecbKdYTADyPKCwaa1LbJD73GHavB
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Embedding Method**: Local CPU-based using sentence-transformers
- **Batch Size**: 100 vectors per upload batch

### Script Details

The upload script (`upload_to_pinecone.py`) performs the following steps:

1. **Initialize Pinecone**: Connects to Pinecone using the provided API key
2. **Create/Get Index**: Creates a new index "nelson-textbook" or uses existing one
   - Dimension: 384
   - Metric: Cosine similarity
   - Cloud: AWS
   - Region: us-east-1
3. **Load Embedding Model**: Loads the sentence-transformers model for generating embeddings
4. **Read CSV**: Reads all 31,009 records from the CSV file
5. **Generate Embeddings**: Converts each content chunk into a 384-dimensional vector
6. **Upload to Pinecone**: Uploads vectors in batches of 100 with metadata

### Metadata Stored in Pinecone

Each vector includes the following metadata:
- book_title
- book_edition
- chapter_number
- chapter_title
- section_number
- section_title
- subsection_number
- subsection_title
- chunk_number
- summary
- content_preview (first 500 characters)
- content_length

### Progress Monitoring

To check the progress of the upload:

```bash
./check_progress.sh
```

Or check the log directly:

```bash
tail -f pinecone_upload.log
```

### Estimated Time

- **Embedding Generation**: ~25-30 minutes (CPU-based)
- **Upload to Pinecone**: ~5-10 minutes
- **Total**: ~30-40 minutes

### Process Status

The upload script is running in the background:

```bash
ps aux | grep upload_to_pinecone.py
```

### After Completion

Once the upload is complete, you can query the Pinecone index using the Pinecone client or API.

Example query code:

```python
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Initialize
pc = Pinecone(api_key="pcsk_39ZEMz_LbNYBJVtxJT7unE8ctWFyiKyodkcJs6kas9ecbKdYTADyPKCwaa1LbJD73GHavB")
index = pc.Index("nelson-textbook")

# Load the same embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Query
query = "What are the symptoms of asthma in children?"
query_embedding = model.encode(query).tolist()

results = index.query(
    vector=query_embedding,
    top_k=5,
    include_metadata=True
)

# Print results
for match in results.matches:
    print(f"Score: {match.score}")
    print(f"Chapter: {match.metadata['chapter_title']}")
    print(f"Content: {match.metadata['content_preview']}")
    print("---")
```

### Troubleshooting

If the process fails or needs to be restarted:

```bash
# Check if running
ps aux | grep upload_to_pinecone.py

# Kill if needed
pkill -f upload_to_pinecone.py

# Restart
cd /home/engine/project
source venv/bin/activate
nohup python upload_to_pinecone.py > pinecone_upload.log 2>&1 &
```

### Index Configuration

The Pinecone index is configured with:
- **Name**: nelson-textbook
- **Dimension**: 384 (matching all-MiniLM-L6-v2 embeddings)
- **Metric**: cosine (best for semantic similarity)
- **Spec**: Serverless (AWS us-east-1)

This configuration is optimized for semantic search over medical textbook content.
