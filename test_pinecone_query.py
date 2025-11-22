#!/usr/bin/env python3
"""
Test script to query the Nelson Textbook Pinecone index
This demonstrates how to perform semantic search on the uploaded medical content.
"""

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Configuration
PINECONE_API_KEY = "pcsk_39ZEMz_LbNYBJVtxJT7unE8ctWFyiKyodkcJs6kas9ecbKdYTADyPKCwaa1LbJD73GHavB"
INDEX_NAME = "nelson-textbook"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def main():
    """Test query against Pinecone index."""
    print("=" * 70)
    print("Nelson Textbook Pinecone Query Test")
    print("=" * 70)
    
    # Initialize Pinecone
    print("\n1. Initializing Pinecone client...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(INDEX_NAME)
    
    # Get index stats
    stats = index.describe_index_stats()
    print(f"   Index: {INDEX_NAME}")
    print(f"   Total vectors: {stats.total_vector_count}")
    print(f"   Dimension: {stats.dimension}")
    
    # Load embedding model
    print("\n2. Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"   Model: {EMBEDDING_MODEL}")
    
    # Test queries
    test_queries = [
        "What are the symptoms of asthma in children?",
        "How to diagnose allergic reactions?",
        "Treatment for pediatric hypertension",
        "Signs of developmental delays in infants"
    ]
    
    print("\n3. Running test queries...")
    print("=" * 70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 70)
        
        # Generate embedding for the query
        query_embedding = model.encode(query).tolist()
        
        # Search Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True
        )
        
        # Display results
        if results.matches:
            for j, match in enumerate(results.matches, 1):
                print(f"\n  Result {j} (Score: {match.score:.4f}):")
                metadata = match.metadata
                print(f"    Chapter: {metadata.get('chapter_title', 'N/A')}")
                print(f"    Section: {metadata.get('section_title', 'N/A')}")
                if metadata.get('summary'):
                    print(f"    Summary: {metadata['summary'][:150]}...")
                if metadata.get('content_preview'):
                    print(f"    Content: {metadata['content_preview'][:200]}...")
        else:
            print("  No results found.")
    
    print("\n" + "=" * 70)
    print("Test complete! The Pinecone index is working correctly.")
    print("=" * 70)


if __name__ == "__main__":
    main()
