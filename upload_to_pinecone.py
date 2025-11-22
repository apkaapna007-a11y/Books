#!/usr/bin/env python3
"""
Upload Nelson Textbook structured CSV to Pinecone Vector Database
This script reads the structured CSV, generates embeddings, and uploads to Pinecone.
"""

import csv
import os
import time
import logging
from typing import List, Dict, Any
from pathlib import Path

try:
    from pinecone import Pinecone, ServerlessSpec
    from sentence_transformers import SentenceTransformer
    from tqdm import tqdm
    import pandas as pd
except ImportError as e:
    print(f"Error importing required libraries: {e}")
    print("Please install: pip install pinecone-client sentence-transformers pandas tqdm")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PINECONE_API_KEY = "pcsk_39ZEMz_LbNYBJVtxJT7unE8ctWFyiKyodkcJs6kas9ecbKdYTADyPKCwaa1LbJD73GHavB"
CSV_FILE = "nelson_textbook_structured_final.csv"
INDEX_NAME = "nelson-textbook"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384-dimensional embeddings
BATCH_SIZE = 100  # Pinecone batch size
DIMENSION = 384  # Dimension for all-MiniLM-L6-v2


def initialize_pinecone():
    """Initialize Pinecone client and return the client object."""
    logger.info("Initializing Pinecone client...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    return pc


def create_or_get_index(pc: Pinecone, index_name: str, dimension: int):
    """Create a new index or get existing index."""
    logger.info(f"Checking for index '{index_name}'...")
    
    # List existing indexes
    existing_indexes = pc.list_indexes()
    index_names = [index.name for index in existing_indexes]
    
    if index_name in index_names:
        logger.info(f"Index '{index_name}' already exists. Using existing index.")
    else:
        logger.info(f"Creating new index '{index_name}' with dimension {dimension}...")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        # Wait for index to be ready
        logger.info("Waiting for index to be ready...")
        time.sleep(10)
    
    return pc.Index(index_name)


def load_embedding_model():
    """Load the sentence transformer model for generating embeddings."""
    logger.info(f"Loading embedding model '{EMBEDDING_MODEL}'...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    logger.info("Model loaded successfully.")
    return model


def read_csv_file(csv_path: str) -> List[Dict[str, Any]]:
    """Read the CSV file and return a list of records."""
    logger.info(f"Reading CSV file: {csv_path}")
    records = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    
    logger.info(f"Loaded {len(records)} records from CSV.")
    return records


def prepare_vectors(records: List[Dict[str, Any]], model: SentenceTransformer) -> List[tuple]:
    """
    Generate embeddings for all records and prepare vectors for Pinecone.
    Returns list of (id, embedding, metadata) tuples.
    """
    logger.info("Generating embeddings for all records...")
    vectors = []
    
    # Extract content for batch embedding generation
    contents = [record['content'] for record in records]
    
    # Generate embeddings in batches
    batch_size = 32  # Embedding model batch size
    all_embeddings = []
    
    for i in tqdm(range(0, len(contents), batch_size), desc="Embedding"):
        batch_contents = contents[i:i + batch_size]
        batch_embeddings = model.encode(batch_contents, show_progress_bar=False)
        all_embeddings.extend(batch_embeddings)
    
    # Prepare vectors with metadata
    logger.info("Preparing vectors with metadata...")
    for idx, (record, embedding) in enumerate(tqdm(zip(records, all_embeddings), 
                                                     total=len(records), 
                                                     desc="Preparing")):
        vector_id = f"chunk_{idx}"
        
        # Prepare metadata (Pinecone has limits on metadata size)
        metadata = {
            "book_title": record.get('book_title', ''),
            "book_edition": record.get('book_edition', ''),
            "chapter_number": record.get('chapter_number', ''),
            "chapter_title": record.get('chapter_title', ''),
            "section_number": record.get('section_number', ''),
            "section_title": record.get('section_title', ''),
            "subsection_number": record.get('subsection_number', ''),
            "subsection_title": record.get('subsection_title', ''),
            "chunk_number": record.get('chunk_number', ''),
            "summary": record.get('summary', ''),
            # Store a preview of content (first 500 chars) to avoid metadata size limits
            "content_preview": record.get('content', '')[:500],
            # Store full content length
            "content_length": len(record.get('content', ''))
        }
        
        vectors.append((vector_id, embedding.tolist(), metadata))
    
    return vectors


def upload_to_pinecone(index, vectors: List[tuple], batch_size: int = 100):
    """Upload vectors to Pinecone in batches."""
    logger.info(f"Uploading {len(vectors)} vectors to Pinecone in batches of {batch_size}...")
    
    total_batches = (len(vectors) + batch_size - 1) // batch_size
    
    for i in tqdm(range(0, len(vectors), batch_size), desc="Uploading", total=total_batches):
        batch = vectors[i:i + batch_size]
        try:
            index.upsert(vectors=batch)
        except Exception as e:
            logger.error(f"Error uploading batch {i // batch_size + 1}: {e}")
            logger.info("Retrying after 5 seconds...")
            time.sleep(5)
            try:
                index.upsert(vectors=batch)
            except Exception as e2:
                logger.error(f"Retry failed: {e2}")
                raise
    
    logger.info("Upload complete!")


def verify_upload(index, expected_count: int):
    """Verify that vectors were uploaded successfully."""
    logger.info("Verifying upload...")
    time.sleep(2)  # Wait for indexing to complete
    
    stats = index.describe_index_stats()
    actual_count = stats.total_vector_count
    
    logger.info(f"Expected vectors: {expected_count}")
    logger.info(f"Actual vectors in index: {actual_count}")
    
    if actual_count >= expected_count:
        logger.info("✓ Upload verification successful!")
    else:
        logger.warning(f"⚠ Upload may be incomplete. Missing {expected_count - actual_count} vectors.")


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("Nelson Textbook to Pinecone Upload Script")
    logger.info("=" * 60)
    
    # Check if CSV file exists
    if not Path(CSV_FILE).exists():
        logger.error(f"CSV file not found: {CSV_FILE}")
        exit(1)
    
    try:
        # Initialize Pinecone
        pc = initialize_pinecone()
        
        # Load embedding model
        model = load_embedding_model()
        
        # Create or get index
        index = create_or_get_index(pc, INDEX_NAME, DIMENSION)
        
        # Read CSV file
        records = read_csv_file(CSV_FILE)
        
        # Prepare vectors with embeddings
        vectors = prepare_vectors(records, model)
        
        # Upload to Pinecone
        upload_to_pinecone(index, vectors, BATCH_SIZE)
        
        # Verify upload
        verify_upload(index, len(vectors))
        
        logger.info("=" * 60)
        logger.info("Process completed successfully!")
        logger.info(f"Index name: {INDEX_NAME}")
        logger.info(f"Total vectors uploaded: {len(vectors)}")
        logger.info(f"Embedding dimension: {DIMENSION}")
        logger.info(f"Embedding model: {EMBEDDING_MODEL}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
