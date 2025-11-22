# Nelson Textbook of Pediatrics - Structured Dataset & Pinecone Upload

This repository contains structured medical content from the Nelson Textbook of Pediatrics (22nd Edition), optimized for vector search and RAG applications.

## 🎉 Pinecone Upload Complete

The dataset has been successfully uploaded to Pinecone! See **[UPLOAD_COMPLETE_SUMMARY.md](UPLOAD_COMPLETE_SUMMARY.md)** for complete details.

### Quick Stats
- ✅ **31,009 vectors** uploaded and verified
- 📊 **Index**: `nelson-textbook`
- 🔑 **API Key**: `pcsk_39ZEMz_LbNYBJVtxJT7unE8ctWFyiKyodkcJs6kas9ecbKdYTADyPKCwaa1LbJD73GHavB`
- 🤖 **Model**: all-MiniLM-L6-v2 (384 dimensions)
- 🎯 **Test Query Script**: `python test_pinecone_query.py`

## 📚 Documentation

- **[UPLOAD_COMPLETE_SUMMARY.md](UPLOAD_COMPLETE_SUMMARY.md)** - Complete upload report and usage guide
- **[PINECONE_UPLOAD_INFO.md](PINECONE_UPLOAD_INFO.md)** - Detailed technical documentation
- **[DATASET_README.md](DATASET_README.md)** - Dataset structure and usage
- **[DATASET_DOCUMENTATION.md](DATASET_DOCUMENTATION.md)** - Processing methodology
- **[QUALITY_REPORT.md](QUALITY_REPORT.md)** - Quality metrics

## 🚀 Quick Start

### Test the Pinecone Index

```bash
# Activate virtual environment
source venv/bin/activate

# Run test queries
python test_pinecone_query.py
```

### Query from Python

```python
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Initialize
pc = Pinecone(api_key="pcsk_39ZEMz_LbNYBJVtxJT7unE8ctWFyiKyodkcJs6kas9ecbKdYTADyPKCwaa1LbJD73GHavB")
index = pc.Index("nelson-textbook")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Query
query = "What are the symptoms of asthma in children?"
results = index.query(
    vector=model.encode(query).tolist(),
    top_k=5,
    include_metadata=True
)
```

## 📂 Repository Structure

```
├── nelson_textbook_structured_final.csv  # Main dataset (31,009 chunks)
├── upload_to_pinecone.py                 # Upload script
├── test_pinecone_query.py               # Test query script
├── convert_to_structured_csv.py         # Data processing pipeline
├── UPLOAD_COMPLETE_SUMMARY.md           # Upload report
├── PINECONE_UPLOAD_INFO.md              # Technical docs
├── DATASET_README.md                    # Dataset guide
└── pinecone_upload.log                  # Upload logs
```

## 🛠️ Scripts

- **upload_to_pinecone.py** - Uploads CSV to Pinecone with embeddings
- **test_pinecone_query.py** - Tests semantic search with sample queries
- **convert_to_structured_csv.py** - Processes raw textbook files into structured CSV
- **build_dataset.py** - Dataset building utilities

## 🎯 Use Cases

- Medical Q&A chatbots
- Pediatric diagnostic assistance
- Medical education tools
- RAG-powered medical search
- Clinical decision support systems

## 📊 Dataset Details

- **Total Chunks**: 31,009
- **Source Files**: 27 medical textbook chapters
- **Chunk Size**: 200-800 tokens
- **Hierarchical Structure**: Book → Chapter → Section → Subsection → Chunk

## 🔧 Technical Stack

- **Embedding**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector DB**: Pinecone (Serverless, AWS us-east-1)
- **Processing**: Python 3 (csv, regex, pathlib)
- **Optional**: PostgreSQL with pgvector

## 📝 License

This dataset is derived from the Nelson Textbook of Pediatrics. Ensure compliance with appropriate medical and educational licensing for your use case.
