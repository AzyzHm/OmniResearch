import io

from pypdf import PdfReader


def extract_txt(file_bytes: bytes) -> str:
    """Decode a plain text file, falling back to latin-1 for odd encodings."""
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1", errors="ignore")


def extract_pdf(file_bytes: bytes) -> str:
    """Extract text from every page of a PDF and join it into one string."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages_text).strip()