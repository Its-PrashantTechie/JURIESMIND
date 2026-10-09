# Legal AI Assistant

A Streamlit prototype for reviewing Indian criminal-law documents. Upload a
Bharatiya Nyaya Sanhita (BNS) PDF and a case or FIR PDF to classify supported
offence categories, find potentially relevant BNS sections, ask questions about
either document, and view document citations and detected contradictions.

The application uses Anthropic for language-model responses and a
Sentence Transformers embedding model with FAISS for document search. Answers
and section matches are checked against text from the uploaded documents.

## Requirements

- Python 3.10 or newer
- An Anthropic API key
- The packages listed in [`requirements.txt`](requirements.txt)

## Setup and run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-api-key"
streamlit run app.py
```

On Windows PowerShell, set the key for the current terminal with:

```powershell
$env:ANTHROPIC_API_KEY = "your-api-key"
```

The first document indexing run downloads the configured embedding model.
Upload the BNS PDF and case/FIR PDF in the sidebar. Use **Classify case** to
review offence categories and matching BNS excerpts, or **Ask a question** to
query either uploaded PDF.

## Project files

- `app.py` — Streamlit user interface and document workflow
- `answer.py` — case classification, BNS section matching, and document Q&A
- `pdf_parser.py` — PDF text extraction
- `chunker.py` — law-section and fixed-size document chunking
- `embeddings.py` — embedding model and FAISS index creation
- `search.py` — vector retrieval and relevance threshold
- `citation.py` — quote verification and citation formatting
-

## Current checkout note

The Python files are at the repository root, but `app.py` and the supporting
modules import them using package paths such as `ingestion.pdf_parser`,
`llm.answer`, `retrieval.search`, and `citations.citation`. Those package
directories are not present in this checkout, so the run command will fail
until the files are moved into the matching packages or the imports are
updated to match the root-level layout.
