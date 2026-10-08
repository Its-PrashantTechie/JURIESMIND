def _norm(s):
    return " ".join(s.lower().split())


def quote_in_text(quote, text):
    return bool(quote) and _norm(quote) in _norm(text)


def find_page(quote, pages):
    """Page number of a quote inside a parsed PDF, else None."""
    for p in pages:
        if quote_in_text(quote, p["text"]):
            return p["page"]
    return None


def format_chunk_citation(chunk):
    return f'{chunk["source"]}, Page {chunk["page"]}, Section {chunk["section"]}'
