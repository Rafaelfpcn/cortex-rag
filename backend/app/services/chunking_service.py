from typing import List, Dict, Any
from app.config import settings

class RecursiveTextChunker:
    """
    Recursively splits text into semantically coherent chunks with overlap,
    tracking offset and page metadata for exact citation audits.
    """
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def split_text(self, text: str, page_estimate_chars: int = 1800) -> List[Dict[str, Any]]:
        if not text:
            return []

        paragraphs = text.split("\n\n")
        chunks: List[Dict[str, Any]] = []
        current_chunk = ""
        current_char_start = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    chunks.append(self._format_chunk(current_chunk, len(chunks), current_char_start, page_estimate_chars))
                    # Retain overlap from end of previous chunk
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                    current_char_start += max(1, len(current_chunk) - len(overlap_text))
                    current_chunk = overlap_text + "\n" + para if overlap_text else para
                else:
                    # Single paragraph exceeds chunk_size, split by sentences
                    sentences = para.split(". ")
                    for s in sentences:
                        if len(current_chunk) + len(s) + 2 <= self.chunk_size:
                            current_chunk += (". " + s if current_chunk else s)
                        else:
                            if current_chunk:
                                chunks.append(self._format_chunk(current_chunk, len(chunks), current_char_start, page_estimate_chars))
                                current_char_start += len(current_chunk)
                            current_chunk = s

        if current_chunk:
            chunks.append(self._format_chunk(current_chunk, len(chunks), current_char_start, page_estimate_chars))

        return chunks

    def _format_chunk(self, content: str, index: int, start_offset: int, page_chars: int) -> Dict[str, Any]:
        estimated_page = (start_offset // page_chars) + 1
        return {
            "chunk_index": index,
            "content": content,
            "metadata": {
                "estimated_page": estimated_page,
                "char_offset": start_offset,
                "char_length": len(content),
            }
        }

chunker = RecursiveTextChunker()
