import io

import pdfplumber

from app.config import MAX_PDF_PAGES, MAX_UPLOAD_SIZE_MB
from app.utils.validators import validate_pdf_content


def extract_text_from_pdf(pdf_file, filename: str = "report.pdf"):
    """
    Extract and validate text content from a PDF document.
    Supports bytes, stream, or file path.
    """
    try:
        if isinstance(pdf_file, (bytes, bytearray)):
            size_mb = len(pdf_file) / (1024 * 1024)
            if size_mb > MAX_UPLOAD_SIZE_MB:
                return f"File size ({size_mb:.1f}MB) exceeds the {MAX_UPLOAD_SIZE_MB}MB limit"
            file_stream = io.BytesIO(pdf_file)
        elif hasattr(pdf_file, "read"):
            content = pdf_file.read()
            size_mb = len(content) / (1024 * 1024)
            if size_mb > MAX_UPLOAD_SIZE_MB:
                return f"File size ({size_mb:.1f}MB) exceeds the {MAX_UPLOAD_SIZE_MB}MB limit"
            file_stream = io.BytesIO(content)
        else:
            file_stream = pdf_file

        text = ""
        with pdfplumber.open(file_stream) as pdf:
            if len(pdf.pages) > MAX_PDF_PAGES:
                return f"PDF exceeds maximum page limit of {MAX_PDF_PAGES}"

            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        if not text.strip():
            return "Could not extract text from the PDF. Please ensure the document is not an unreadable scanned image."

        is_valid, error = validate_pdf_content(text)
        if not is_valid:
            return error

        return text
    except Exception as e:
        return f"Error extracting text from PDF: {e!s}"
