import os
import streamlit as st
from ingestion.pdf_parser import parse_pdf
from ingestion.chunker import chunk_law, chunk_plain
from ingestion.embeddings import build_index
from llm.answer import classify_case, map_to_law, ask

st.set_page_config(page_title="Legal AI Assistant", layout="wide")
st.title("⚖️ Legal AI Assistant (BNS)")

UP = "data/uploaded_pdfs"
os.makedirs(UP, exist_ok=True)


def save(f):
    path = os.path.join(UP, f.name)
    with open(path, "wb") as out:
        out.write(f.getbuffer())
    return path


@st.cache_resource(show_spinner="Indexing law PDF...")
def load_law(path):
    pages = parse_pdf(path)
    chunks = chunk_law(pages, source="BNS")
    return chunks, build_index(chunks)


@st.cache_resource(show_spinner="Indexing case PDF...")
def load_case(path):
    pages = parse_pdf(path)
    chunks = chunk_plain(pages, source="CASE")
    return pages, chunks, build_index(chunks)


with st.sidebar:
    st.header("📄 Upload PDFs")
    law_file = st.file_uploader("Law PDF (BNS)", type="pdf", key="law")
    case_file = st.file_uploader("Case / FIR PDF", type="pdf", key="case")

law = load_law(save(law_file)) if law_file else None
case = load_case(save(case_file)) if case_file else None

tab1, tab2 = st.tabs(["🔎 Classify case", "💬 Ask a question"])

with tab1:
    if not (law and case):
        st.info("Upload both the BNS PDF and a case/FIR PDF.")
    elif st.button("Classify this case"):
        case_pages, _, _ = case
        law_chunks, law_index = law
        with st.spinner("Analysing..."):
            res = classify_case(case_pages)
        if not res["offences"]:
            st.warning("No supported offence found in this document.")
        for i, o in enumerate(res["offences"], 1):
            st.subheader(f"{i}. {o['category']}")
            st.write(f"**Why:** {o['why']}")
            st.caption(f"Case evidence (Page {o['case_page']}): “{o['case_quote']}”")
            matches = map_to_law(o, law_index, law_chunks)
            if not matches:
                st.write("BNS Section: _Cannot verify from the uploaded law PDF._")
            for m in matches:
                st.markdown(f"**BNS Section {m['section']}** — {m['why']}")
                st.caption(f"Source: {m['citation']} — “{m['quote']}”")
        for c in res["contradictions"]:
            st.error(f"⚠️ Contradiction: {c['explanation']}")
            st.write(f"A (page {c['page_a']}): “{c['statement_a']}”")
            st.write(f"B (page {c['page_b']}): “{c['statement_b']}”")

with tab2:
    target = st.radio("Ask about", ["Law PDF", "Case PDF"], horizontal=True)
    q = st.text_input("Your question")
    if q:
        if target == "Law PDF" and law:
            chunks, index = law
        elif target == "Case PDF" and case:
            _, chunks, index = case
        else:
            st.info("Upload that PDF first.")
            st.stop()
        res = ask(q, index, chunks)
        if res["answerable"]:
            st.success(res["answer"])
            for c in res["citations"]:
                st.caption(f"📌 {c['source']}: “{c['quote']}”")
        else:
            st.error("🛑 " + res["answer"])
        for c in res.get("contradictions", []):
            st.warning(f"⚠️ Conflict: {c['explanation']}")
            for s in c.get("sources", []):
                st.write(f"- {s}")
