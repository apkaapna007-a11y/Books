#!/usr/bin/env python3
"""
Nelson Textbook of Pediatrics - Structured CSV Converter
Converts raw text files into hierarchical, chunked CSV format for vector search and RAG.
"""

import csv
import re
import os
import glob
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Generator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NelsonTextbookConverter:
    def __init__(self, min_chunk_tokens: int = 50, max_chunk_tokens: int = 300):
        self.min_chunk_tokens = min_chunk_tokens
        self.max_chunk_tokens = max_chunk_tokens
        self.book_title = "Nelson Textbook of Pediatrics"
        self.book_edition = "22"  # Assuming 22nd edition based on common usage
        
        # Character cleaning patterns
        self.char_replacements = {
            'M-bM-^@M-^Y': "'",  # Apostrophe
            'M-bM-^@M-^S': "–",  # En dash
            'M-bM-^@M-^T': "—",  # Em dash
            'M-BM--': "—",       # Em dash variant
            'M-bM-^@M-^\\': '"', # Opening quote
            'M-bM-^@M-^]': '"',  # Closing quote
            'M-bM-^@M-^[': '"',  # Opening quote variant
            'M-bM-^@M-^C': '™',  # Trademark
            'M-bM-^@M-^B': '•',  # Bullet point
            'M-bM-^@M-^I': ' ',  # Non-breaking space
            'M-NM-1': 'α',       # Alpha
            'M-NM-2': 'β',       # Beta
            'M-NM-<': 'μ',       # Mu (micro)
            'M-IM-%': '≥',       # Greater than or equal
            'M-IM-$': '≤',       # Less than or equal
        }
        
        # Regex patterns for structure detection - simplified and more robust
        self.part_pattern = re.compile(r'PART\s+([IVXLCDM]+)\s+([^0-9]+?)(?=\s+Section|\s+\d+|\s*$)', re.IGNORECASE)
        self.chapter_pattern = re.compile(r'Chapter\s+(\d+)\s+([A-Za-z][^0-9]*?)(?=\s+[A-Z][a-z]|\s*$)', re.IGNORECASE)
        self.section_pattern = re.compile(r'^(\d+(?:\.\d+)?)\s+([A-Z][A-Za-z\s,\-:()]+?)(?=\s+[A-Z][a-z]|\s*$)')
        self.subsection_pattern = re.compile(r'^(\d+\.\d+(?:\.\d+)?)\s+([A-Z][A-Za-z\s,\-:()]+?)(?=\s+[A-Z][a-z]|\s*$)')
        
    def clean_text(self, text: str) -> str:
        """Clean special characters while preserving medical terminology."""
        cleaned = text
        for old_char, new_char in self.char_replacements.items():
            cleaned = cleaned.replace(old_char, new_char)
        
        # Remove excessive whitespace but preserve paragraph breaks
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 3.5 characters)."""
        return len(text) // 3
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences, handling medical abbreviations."""
        # Simple sentence splitting that avoids complex lookbehind
        # Split on sentence endings followed by whitespace and capital letter
        sentences = re.split(r'[.!?]+\s+(?=[A-Z])', text)
        
        # Clean up and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Filter very short fragments
                # Ensure sentence ends properly
                if not sentence.endswith(('.', '!', '?')):
                    sentence += '.'
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def chunk_content(self, content: str, context: Dict) -> List[Dict]:
        """Chunk content into token-appropriate sizes while preserving sentence boundaries."""
        if not content.strip():
            return []
        
        sentences = self.split_into_sentences(content)
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_number = 1
        
        for sentence in sentences:
            sentence_tokens = self.estimate_tokens(sentence)
            
            # If adding this sentence would exceed max tokens, finalize current chunk
            if current_tokens + sentence_tokens > self.max_chunk_tokens and current_chunk:
                chunk_text = ' '.join(current_chunk)
                # Add chunk if it has reasonable content
                if len(chunk_text.strip()) > 50:
                    chunks.append(self.create_chunk_dict(chunk_text, context, chunk_number))
                    chunk_number += 1
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add final chunk if it exists
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            # Always add the final chunk if it has reasonable content
            if len(chunk_text.strip()) > 50:
                chunks.append(self.create_chunk_dict(chunk_text, context, chunk_number))
        
        return chunks
    
    def create_chunk_dict(self, content: str, context: Dict, chunk_number: int) -> Dict:
        """Create a chunk dictionary with all required fields."""
        summary = self.generate_summary(content)
        
        return {
            'book_title': self.book_title,
            'book_edition': self.book_edition,
            'chapter_number': context.get('chapter_number', ''),
            'chapter_title': context.get('chapter_title', ''),
            'section_number': context.get('section_number', ''),
            'section_title': context.get('section_title', ''),
            'subsection_number': context.get('subsection_number', ''),
            'subsection_title': context.get('subsection_title', ''),
            'chunk_number': chunk_number,
            'content': content,
            'summary': summary
        }
    
    def generate_summary(self, content: str) -> str:
        """Generate a concise summary from the content."""
        sentences = self.split_into_sentences(content)
        if not sentences:
            return ""
        
        # Take first 1-2 sentences, up to ~150 characters
        summary_parts = []
        char_count = 0
        
        for sentence in sentences[:3]:  # Max 3 sentences
            if char_count + len(sentence) > 150 and summary_parts:
                break
            summary_parts.append(sentence)
            char_count += len(sentence)
            
            if char_count >= 80:  # Minimum reasonable summary length
                break
        
        summary = ' '.join(summary_parts)
        
        # Ensure summary ends properly
        if summary and not summary.endswith(('.', '!', '?', ':')):
            summary += '...'
        
        return summary
    
    def parse_file_structure(self, filepath: str) -> Generator[Dict, None, None]:
        """Parse a file and yield structured content chunks."""
        logger.info(f"Processing file: {filepath}")
        
        current_context = {
            'part_number': '',
            'part_title': '',
            'chapter_number': '',
            'chapter_title': '',
            'section_number': '',
            'section_title': '',
            'subsection_number': '',
            'subsection_title': ''
        }
        
        current_content = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                content = self.clean_text(content)
                
                # Since the text might be one long line, we need to split it differently
                # Look for structural markers and split the content accordingly
                
                # First, find all structural markers and their positions
                markers = []
                
                # Find PART markers
                for match in self.part_pattern.finditer(content):
                    markers.append(('PART', match.start(), match.end(), match.groups()))
                
                # Find Chapter markers
                for match in self.chapter_pattern.finditer(content):
                    markers.append(('CHAPTER', match.start(), match.end(), match.groups()))
                
                # Sort markers by position
                markers.sort(key=lambda x: x[1])
                
                # Process content between markers
                last_pos = 0
                
                for i, (marker_type, start_pos, end_pos, groups) in enumerate(markers):
                    # Process content before this marker
                    if last_pos < start_pos:
                        content_text = content[last_pos:start_pos].strip()
                        if len(content_text) > 100:
                            chunks = self.chunk_content(content_text, current_context)
                            for chunk in chunks:
                                yield chunk
                    
                    # Update context based on marker
                    if marker_type == 'PART':
                        part_title = groups[1].strip()
                        # Clean up part title - remove extra content after the main title
                        if 'The field of' in part_title:
                            part_title = part_title.split('The field of')[0].strip()
                        
                        current_context.update({
                            'part_number': groups[0],
                            'part_title': part_title,
                            'chapter_number': '',
                            'chapter_title': '',
                            'section_number': '',
                            'section_title': '',
                            'subsection_number': '',
                            'subsection_title': ''
                        })
                        logger.info(f"Found PART: {groups[0]} - {part_title}")
                        
                    elif marker_type == 'CHAPTER':
                        chapter_title = groups[1].strip()
                        # Clean up chapter title
                        if len(chapter_title) > 100:
                            chapter_title = chapter_title[:100].strip()
                        
                        current_context.update({
                            'chapter_number': groups[0],
                            'chapter_title': chapter_title,
                            'section_number': '',
                            'section_title': '',
                            'subsection_number': '',
                            'subsection_title': ''
                        })
                        logger.info(f"Found Chapter: {groups[0]} - {chapter_title}")
                    
                    last_pos = end_pos
                
                # Process any remaining content after the last marker
                if last_pos < len(content):
                    content_text = content[last_pos:].strip()
                    if len(content_text) > 100:
                        chunks = self.chunk_content(content_text, current_context)
                        for chunk in chunks:
                            yield chunk
                        
        except Exception as e:
            logger.error(f"Error processing file {filepath}: {str(e)}")
    
    def convert_files_to_csv(self, input_pattern: str, output_file: str):
        """Convert all matching files to structured CSV."""
        files = sorted(glob.glob(input_pattern))
        logger.info(f"Found {len(files)} files to process")
        
        fieldnames = [
            'book_title', 'book_edition', 'chapter_number', 'chapter_title',
            'section_number', 'section_title', 'subsection_number', 'subsection_title',
            'chunk_number', 'content', 'summary'
        ]
        
        total_chunks = 0
        
        with open(output_file, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            for filepath in files:
                file_chunks = 0
                try:
                    for chunk in self.parse_file_structure(filepath):
                        writer.writerow(chunk)
                        file_chunks += 1
                        total_chunks += 1
                        
                        if total_chunks % 100 == 0:
                            logger.info(f"Processed {total_chunks} chunks so far...")
                            
                    logger.info(f"Completed {Path(filepath).name}: {file_chunks} chunks")
                    
                except Exception as e:
                    logger.error(f"Failed to process {filepath}: {str(e)}")
        
        logger.info(f"Conversion complete! Generated {total_chunks} chunks in {output_file}")

def main():
    """Main execution function."""
    converter = NelsonTextbookConverter()
    
    # Convert all .txt files in current directory
    input_pattern = "*.txt"
    output_file = "nelson_textbook_structured.csv"
    
    logger.info("Starting Nelson Textbook conversion to structured CSV...")
    converter.convert_files_to_csv(input_pattern, output_file)
    logger.info("Conversion completed successfully!")

if __name__ == "__main__":
    main()
