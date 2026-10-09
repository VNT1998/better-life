import io
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
import pdfplumber
import filetype
from PIL import Image

from app.db.session import SessionLocal
from app.db.models import Document, DocumentPage
from app.config import MAX_UPLOAD_SIZE_MB, MAX_PDF_PAGES

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Multimodal document ingestion engine supporting PDF, Text, and Images.
    Extracts text with page segmentation, character counts, and provenance tracking.
    """

    def validate_file(self, content: bytes, filename: str) -> Tuple[bool, Optional[str], str]:
        """Validates file size and format."""
        max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            return False, f"File size exceeds maximum allowed {MAX_UPLOAD_SIZE_MB}MB", ""

        if len(content) == 0:
            return False, "Uploaded file is empty", ""

        fn_lower = filename.lower()
        if fn_lower.endswith(".pdf"):
            return True, None, "pdf"
        elif fn_lower.endswith((".txt", ".md", ".csv")):
            return True, None, "text"
        elif fn_lower.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
            return True, None, "image"

        # Guess from magic bytes
        kind = filetype.guess(content)
        if kind:
            if kind.mime == "application/pdf":
                return True, None, "pdf"
            elif kind.mime.startswith("image/"):
                return True, None, "image"
            elif kind.mime.startswith("text/"):
                return True, None, "text"

        return False, f"Unsupported file type. Please upload a PDF, text, or image document.", ""

    def process_and_store_document(
        self,
        content: bytes,
        filename: str,
        db_session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Parses document with page segmentation and persists it to the database.
        Returns document metadata and extracted pages.
        """
        is_valid, err, file_type = self.validate_file(content, filename)
        if not is_valid:
            return {"success": False, "error": err}

        pages_data: List[Dict[str, Any]] = []

        if file_type == "pdf":
            pages_data = self._parse_pdf(content)
        elif file_type == "text":
            pages_data = self._parse_text(content)
        elif file_type == "image":
            pages_data = self._parse_image(content, filename)

        if not pages_data:
            return {
                "success": False,
                "error": "Could not extract readable text or pages from document.",
            }

        total_pages = len(pages_data)
        if total_pages > MAX_PDF_PAGES:
            return {
                "success": False,
                "error": f"Document exceeds maximum page limit of {MAX_PDF_PAGES} pages.",
            }

        should_close_db = False
        db = db_session
        if db is None:
            db = SessionLocal()
            should_close_db = True

        try:
            doc_id = str(uuid.uuid4())
            doc_record = Document(
                id=doc_id,
                filename=filename,
                file_type=file_type,
                file_size_bytes=len(content),
                page_count=total_pages,
                metadata_json={
                    "total_chars": sum(p["char_count"] for p in pages_data),
                    "file_type": file_type,
                },
            )
            db.add(doc_record)
            db.flush()

            for p in pages_data:
                page_record = DocumentPage(
                    id=str(uuid.uuid4()),
                    document_id=doc_id,
                    page_number=p["page_number"],
                    char_count=p["char_count"],
                    text_content=p["text_content"],
                )
                db.add(page_record)

            db.commit()

            return {
                "success": True,
                "document_id": doc_id,
                "filename": filename,
                "file_type": file_type,
                "page_count": total_pages,
                "total_chars": sum(p["char_count"] for p in pages_data),
                "pages": [
                    {
                        "page_number": p["page_number"],
                        "char_count": p["char_count"],
                        "text_preview": p["text_content"][:300].strip(),
                    }
                    for p in pages_data
                ],
                "full_text": "\n\n--- PAGE BREAK ---\n\n".join(
                    f"### [Page {p['page_number']}]\n{p['text_content']}" for p in pages_data
                ),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to persist document {filename}: {e}")
            return {"success": False, "error": f"Database error storing document: {str(e)}"}
        finally:
            if should_close_db:
                db.close()

    def _parse_pdf(self, content: bytes) -> List[Dict[str, Any]]:
        pages = []
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for idx, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text(layout=True) or page.extract_text() or ""
                    clean_text = text.strip()
                    pages.append({
                        "page_number": idx,
                        "text_content": clean_text if clean_text else f"[Empty or non-text page {idx}]",
                        "char_count": len(clean_text),
                    })
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
        return pages

    def _parse_text(self, content: bytes) -> List[Dict[str, Any]]:
        pages = []
        try:
            text = content.decode("utf-8", errors="replace")
            # Segment text into simulated 3000-character pages for provenance tracking
            chunk_size = 3000
            chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
            if not chunks:
                chunks = [""]
            for idx, chunk in enumerate(chunks, start=1):
                pages.append({
                    "page_number": idx,
                    "text_content": chunk.strip(),
                    "char_count": len(chunk.strip()),
                })
        except Exception as e:
            logger.error(f"Error parsing text file: {e}")
        return pages

    def _parse_image(self, content: bytes, filename: str) -> List[Dict[str, Any]]:
        try:
            image = Image.open(io.BytesIO(content))
            width, height = image.size
            img_format = image.format or "IMAGE"
            # Note: For full OCR, tesseract or a vision model can be called.
            # Here we provide image metadata provenance with graceful description
            text_desc = f"[Medical Document Image: {filename} ({img_format}, {width}x{height}px)]"
            return [{
                "page_number": 1,
                "text_content": text_desc,
                "char_count": len(text_desc),
            }]
        except Exception as e:
            logger.error(f"Error reading image: {e}")
            return []


ingestion_service = IngestionService()
