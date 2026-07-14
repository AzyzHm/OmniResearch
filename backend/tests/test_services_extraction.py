import backend.services.extraction as extraction
from backend.services.extraction import extract_pdf, extract_txt


def _make_pdf(texts: list[str]) -> bytes:
    """
    Build a minimal, hand-crafted multi-page PDF (one Helvetica text line per
    page) so extract_pdf can be tested against a real PdfReader instead of a
    mock. No external PDF-writing library required.
    """
    n_pages = len(texts)
    font_obj_num = 3 + 2 * n_pages
    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")  # obj 1
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n_pages))
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>".encode())  # obj 2

    for i, text in enumerate(texts):
        page_num = 3 + 2 * i
        content_num = page_num + 1
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 {font_obj_num} 0 R >> >> "
            f"/MediaBox [0 0 200 200] /Contents {content_num} 0 R >>".encode()
        )
        stream = f"BT /F1 24 Tf 10 100 Td ({text}) Tj ET".encode()
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    body = b"%PDF-1.4\n"
    for idx, obj in enumerate(objects, start=1):
        body += f"{idx} 0 obj\n".encode() + obj + b"\nendobj\n"
    body += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n0\n%%EOF\n".encode()
    return body


class _FakePage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class _FakeReader:
    def __init__(self, pages_text):
        self.pages = [_FakePage(t) for t in pages_text]


class TestExtractTxt:
    def test_decodes_valid_utf8(self):
        assert extract_txt("hello world".encode("utf-8")) == "hello world"

    def test_decodes_utf8_with_special_characters(self):
        text = "café — naïve résumé"
        assert extract_txt(text.encode("utf-8")) == text

    def test_falls_back_to_latin1_on_invalid_utf8(self):
        raw = b"caf\xe9"
        result = extract_txt(raw)
        assert result == "caf\xe9".encode("latin-1").decode("latin-1")

    def test_falls_back_silently_without_raising(self):
        raw = b"\xff\xfe\x00\x01broken"
        result = extract_txt(raw)
        assert isinstance(result, str)

    def test_empty_bytes_returns_empty_string(self):
        assert extract_txt(b"") == ""


class TestExtractPdf:
    def test_extracts_text_from_single_page(self):
        pdf_bytes = _make_pdf(["Hello World"])
        assert extract_pdf(pdf_bytes) == "Hello World"

    def test_joins_multiple_pages_with_double_newline(self):
        pdf_bytes = _make_pdf(["Page one text", "Page two text"])
        assert extract_pdf(pdf_bytes) == "Page one text\n\nPage two text"

    def test_result_is_stripped_of_surrounding_whitespace(self, monkeypatch):
        monkeypatch.setattr(
            extraction, "PdfReader", lambda _stream: _FakeReader(["  leading and trailing  "])
        )
        assert extract_pdf(b"irrelevant") == "leading and trailing"

    def test_page_with_no_extractable_text_falls_back_to_empty_string(self, monkeypatch):
        monkeypatch.setattr(
            extraction, "PdfReader", lambda _stream: _FakeReader([None, "Real text"])
        )
        assert extract_pdf(b"irrelevant") == "Real text"

    def test_blank_page_between_real_pages_leaves_empty_gap(self, monkeypatch):
        monkeypatch.setattr(
            extraction, "PdfReader", lambda _stream: _FakeReader(["First", None, "Third"])
        )
        assert extract_pdf(b"irrelevant") == "First\n\n\n\nThird"

    def test_all_pages_empty_returns_empty_string(self, monkeypatch):
        monkeypatch.setattr(extraction, "PdfReader", lambda _stream: _FakeReader([None, None]))
        assert extract_pdf(b"irrelevant") == ""

    def test_no_pages_returns_empty_string(self, monkeypatch):
        monkeypatch.setattr(extraction, "PdfReader", lambda _stream: _FakeReader([]))
        assert extract_pdf(b"irrelevant") == ""