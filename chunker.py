import re

# BNS sections start like "303. Theft.—" or "331. (1) Whoever..."
SECTION_RE = re.compile(r"^\s*(\d{1,3}[A-Z]?)\.\s+\S")
MAX_LEN = 2500


def chunk_law(pages, source="BNS"):
    """Section-wise chunks with page + section metadata."""
    chunks, cur = [], None

    def flush():
        nonlocal cur
        if cur and cur["text"].strip():
            t = cur["text"]
            for i in range(0, len(t), MAX_LEN):  # split very long sections
                chunks.append({**cur, "text": t[i:i + MAX_LEN],
                               "id": f"c{len(chunks)}"})
        cur = None

    for p in pages:
        for line in p["text"].splitlines():
            m = SECTION_RE.match(line)
            if m:
                flush()
                cur = {"section": m.group(1), "page": p["page"],
                       "source": source, "text": ""}
            if cur is None:
                cur = {"section": "?", "page": p["page"],
                       "source": source, "text": ""}
            cur["text"] += line + "\n"
    flush()
    return chunks


def chunk_plain(pages, source="DOC", size=900, overlap=150):
    """Fallback fixed-size chunks (for non-statute docs)."""
    chunks = []
    for p in pages:
        t = p["text"]
        for i in range(0, len(t), size - overlap):
            piece = t[i:i + size]
            if piece.strip():
                chunks.append({"id": f"c{len(chunks)}", "section": "-",
                               "page": p["page"], "source": source, "text": piece})
    return chunks
