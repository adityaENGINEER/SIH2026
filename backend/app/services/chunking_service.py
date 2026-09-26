import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ChunkingService:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(self, content_cache: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Takes the content.json dictionary and returns a list of chunk dictionaries.
        """
        document_id = content_cache.get("document_id")
        doc_type = content_cache.get("document_type", "unknown")
        chunks = []
        chunk_index = 0

        # OCR pages or standard PDF pages
        if "pages" in content_cache and content_cache["pages"]:
            for page in content_cache["pages"]:
                page_text = page.get("text", "")
                page_number = page.get("page_number", 1)
                if not page_text.strip():
                    continue
                
                page_chunks = self._split_text(page_text)
                for text_chunk in page_chunks:
                    chunks.append({
                        "chunk_id": f"{document_id}_chunk_{chunk_index:04d}",
                        "document_id": document_id,
                        "chunk_index": chunk_index,
                        "text": text_chunk,
                        "source": {
                            "filename": content_cache.get("metadata", {}).get("original_filename", f"{document_id}.{doc_type}"),
                            "page": page_number,
                            "type": doc_type
                        }
                    })
                    chunk_index += 1
        
        # DOCX or TXT with paragraphs
        elif "paragraphs" in content_cache and content_cache["paragraphs"]:
            # Combine paragraphs intelligently
            current_text = ""
            for para in content_cache["paragraphs"]:
                if len(current_text) + len(para) > self.chunk_size and current_text:
                    chunks.append(self._create_chunk_dict(document_id, chunk_index, current_text, doc_type, content_cache))
                    chunk_index += 1
                    current_text = para
                else:
                    current_text += "\n" + para if current_text else para
            
            if current_text:
                chunks.append(self._create_chunk_dict(document_id, chunk_index, current_text, doc_type, content_cache))
                chunk_index += 1
                
        # CSV or XLSX with rows
        elif "rows" in content_cache or "sheets" in content_cache:
            # For simplicity in MVP, chunk the combined text representation
            text = content_cache.get("text", "")
            if text:
                split_chunks = self._split_text(text)
                for text_chunk in split_chunks:
                    chunks.append(self._create_chunk_dict(document_id, chunk_index, text_chunk, doc_type, content_cache))
                    chunk_index += 1
                    
        # Fallback to plain text
        else:
            text = content_cache.get("text", "")
            if text:
                split_chunks = self._split_text(text)
                for text_chunk in split_chunks:
                    chunks.append(self._create_chunk_dict(document_id, chunk_index, text_chunk, doc_type, content_cache))
                    chunk_index += 1

        return chunks

    def _create_chunk_dict(self, document_id, chunk_index, text, doc_type, content_cache):
        return {
            "chunk_id": f"{document_id}_chunk_{chunk_index:04d}",
            "document_id": document_id,
            "chunk_index": chunk_index,
            "text": text,
            "source": {
                "filename": content_cache.get("metadata", {}).get("original_filename", f"{document_id}.{doc_type}"),
                "type": doc_type
            }
        }

    def _split_text(self, text: str) -> List[str]:
        """
        Splits text into chunks respecting boundaries using a simple sliding window over words/sentences.
        """
        # Split by double newline first to respect paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            if len(current_chunk) + len(para) < self.chunk_size:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    # Simple overlap by keeping the last portion of the previous chunk
                    # Roughly overlap characters by grabbing the end of current_chunk
                    if len(current_chunk) > self.overlap:
                        current_chunk = current_chunk[-self.overlap:] + "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    # Paragraph itself is too large, need to split by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    sub_chunk = ""
                    for sent in sentences:
                        if len(sub_chunk) + len(sent) < self.chunk_size:
                            sub_chunk += " " + sent if sub_chunk else sent
                        else:
                            if sub_chunk:
                                chunks.append(sub_chunk.strip())
                            sub_chunk = sent
                    current_chunk = sub_chunk.strip()
                    
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

chunking_service = ChunkingService()
