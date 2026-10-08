import fitz  # PyMuPDF


def parse_pdf(path):
    """Returns list of {"page": int, "text": str}."""
    doc = fitz.open(path)
    return [{"page": i, "text": p.get_text()} for i, p in enumerate(doc, start=1)]
