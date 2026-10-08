import json
import re
import anthropic
from retrieval.search import search, is_supported
from citations.citation import quote_in_text, find_page, format_chunk_citation

client = anthropic.Anthropic()
MODEL = "claude-sonnet-5-5"

CATEGORIES = [
    "Theft", "Trespass", "Property damage", "Assault", "Breach of trust",
    "Cheating", "Cybercrime", "Domestic violence", "Drug use",
    "Outraging modesty", "Sexual assault", "Riots", "Murder", "Abduction",
]

REFUSAL = "Cannot verify from the uploaded document."


def _call(system, user):
    r = client.messages.create(model=MODEL, max_tokens=2000, temperature=0,
                               system=system,
                               messages=[{"role": "user", "content": user}])
    txt = re.sub(r"```json|```", "", r.content[0].text).strip()
    return json.loads(txt)


# ---------- 1. Classify a case/FIR PDF ----------
CLASSIFY_SYS = f"""You are a legal case classifier for Indian criminal law.
Read the case document and decide which of these categories apply:
{CATEGORIES}
Use ONLY facts stated in the document. Return JSON only:
{{"offences":[{{"category":"<one of the list>","why":"short reason",
"case_quote":"exact verbatim text from the document supporting this"}}],
"contradictions":[{{"statement_a":"verbatim quote","statement_b":"verbatim quote",
"explanation":"..."}}]}}
Rules: a case may have several categories. If none apply return empty offences.
Contradictions = facts inside the document that conflict (dates, names, amounts, sequence)."""


def classify_case(case_pages):
    full = "\n".join(f"[Page {p['page']}]\n{p['text']}" for p in case_pages)[:15000]
    res = _call(CLASSIFY_SYS, full)
    for o in res.get("offences", []):
        pg = find_page(o.get("case_quote", ""), case_pages)
        o["case_page"] = pg
        o["quote_verified"] = pg is not None
    for c in res.get("contradictions", []):
        c["page_a"] = find_page(c.get("statement_a", ""), case_pages)
        c["page_b"] = find_page(c.get("statement_b", ""), case_pages)
        c["verified"] = c["page_a"] is not None and c["page_b"] is not None
    res["offences"] = [o for o in res.get("offences", []) if o["quote_verified"]]
    res["contradictions"] = [c for c in res.get("contradictions", []) if c["verified"]]
    return res


# ---------- 2. Map an offence to BNS sections ----------
MAP_SYS = """You map an offence to sections of a law, using ONLY the excerpts given.
Return JSON only:
{"matches":[{"chunk_id":"...","section":"...","why":"...","quote":"exact verbatim text from that excerpt"}]}
If no excerpt fits, return {"matches":[]}. Never cite a section not in the excerpts."""


def map_to_law(offence, law_index, law_chunks):
    query = f'{offence["category"]}: {offence["why"]}'
    hits = search(law_index, law_chunks, query, k=5)
    if not is_supported(hits):
        return []
    ctx = "\n\n".join(f"[{c['id']} | Section {c['section']} | page {c['page']}]\n{c['text']}"
                      for c, _ in hits)
    res = _call(MAP_SYS, f"OFFENCE: {query}\n\nEXCERPTS:\n{ctx}")
    by_id = {c["id"]: c for c, _ in hits}
    out = []
    for m in res.get("matches", []):
        ch = by_id.get(m.get("chunk_id"))
        if ch and quote_in_text(m.get("quote", ""), ch["text"]):
            m["citation"] = format_chunk_citation(ch)
            out.append(m)
    return out


# ---------- 3. Q&A with refusal + contradiction flagging ----------
QA_SYS = f"""You are a legal document review assistant.
Answer ONLY from the excerpts. No outside knowledge. Return JSON only:
{{"answerable":true/false,"answer":"...",
"citations":[{{"chunk_id":"...","quote":"exact verbatim text"}}],
"contradictions":[{{"chunk_ids":["..",".."],"explanation":"..."}}]}}
If excerpts do not contain the answer: answerable=false, answer="{REFUSAL}".
If two excerpts conflict, list both in contradictions instead of picking one."""


def ask(question, index, chunks):
    hits = search(index, chunks, question, k=6)
    if not is_supported(hits):
        return {"answerable": False, "answer": REFUSAL, "citations": [], "contradictions": []}
    ctx = "\n\n".join(f"[{c['id']} | {format_chunk_citation(c)}]\n{c['text']}" for c, _ in hits)
    res = _call(QA_SYS, f"EXCERPTS:\n{ctx}\n\nQUESTION: {question}")
    by_id = {c["id"]: c for c, _ in hits}

    if not res.get("answerable"):
        return {"answerable": False, "answer": REFUSAL, "citations": [], "contradictions": []}

    good = []
    for cit in res.get("citations", []):
        ch = by_id.get(cit.get("chunk_id"))
        if ch and quote_in_text(cit.get("quote", ""), ch["text"]):
            cit["source"] = format_chunk_citation(ch)
            good.append(cit)
    if not good:  # no verifiable evidence -> refuse
        return {"answerable": False, "answer": REFUSAL, "citations": [], "contradictions": []}
    res["citations"] = good
    for c in res.get("contradictions", []):
        c["sources"] = [format_chunk_citation(by_id[i]) for i in c.get("chunk_ids", []) if i in by_id]
    return res
