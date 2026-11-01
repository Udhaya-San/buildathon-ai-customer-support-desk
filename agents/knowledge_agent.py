"""Agent 2 - Knowledge Base Agent: searches the company documents with the search_kb tool."""

import math
import re

from autogen_agentchat.agents import AssistantAgent

import config
from state import STATE

# ---------------------------------------------------------------- search tool
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "of", "to", "in", "on", "at", "for", "from", "by",
    "with", "about", "as", "is", "are", "was", "were", "be", "been", "am", "it", "its", "this",
    "that", "these", "those", "i", "me", "my", "we", "our", "you", "your", "he", "she", "they",
    "them", "their", "do", "does", "did", "can", "could", "will", "would", "should", "may",
    "have", "has", "had", "not", "no", "yes", "so", "than", "then", "there", "here", "what",
    "when", "where", "which", "who", "how", "why", "any", "some", "get", "got", "need", "want",
    "please", "help", "sell", "company", "ever", "just", "also", "very", "more", "most", "up",
    "out", "into", "over", "after", "before", "once", "per", "all", "one", "two", "three",
}
# Words that appear in almost every document: they help a little but never count as a real match.
_WEAK = {"order", "product", "item", "purchase", "buy", "bought", "customer", "shopnest", "support"}

_CANONICAL = {
    # delivery
    "late": "delay", "delayed": "delay", "delay": "delay", "delays": "delay", "overdue": "delay",
    "slow": "delay", "yesterday": "delay",
    "arrive": "deliver", "arrives": "deliver", "arrived": "deliver", "arrival": "deliver",
    "delivery": "deliver", "delivered": "deliver", "deliver": "deliver", "dispatch": "deliver",
    "dispatched": "deliver", "reach": "deliver", "reached": "deliver",
    "shipping": "ship", "shipment": "ship", "shipped": "ship", "ship": "ship", "courier": "ship",
    "parcel": "parcel", "package": "parcel", "tracking": "track", "track": "track",
    # refunds and returns
    "refund": "refund", "refunds": "refund", "refunded": "refund", "reimburse": "refund",
    "return": "return", "returns": "return", "returned": "return", "returning": "return",
    # damage
    "broken": "damage", "broke": "damage", "damaged": "damage", "damage": "damage",
    "defective": "damage", "faulty": "damage", "crack": "damage", "cracked": "damage",
    "replace": "replace", "replacement": "replace", "replaced": "replace", "swap": "replace",
    # account
    "forgot": "reset", "forgotten": "reset", "reset": "reset", "recover": "reset",
    "login": "login", "log": "login", "signin": "login", "password": "password",
    "passcode": "password", "locked": "lock", "lock": "lock",
    # billing
    "charge": "charge", "charged": "charge", "charges": "charge", "billed": "charge",
    "billing": "charge", "bill": "charge", "deducted": "charge", "debited": "charge",
    "duplicate": "duplicate", "twice": "duplicate", "double": "duplicate", "thrice": "duplicate",
}


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def _terms(text: str):
    """Lower-case, drop filler words, map synonyms and stem. Returns a list of terms."""
    out = []
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in _STOPWORDS or word.isdigit():
            continue
        out.append(_CANONICAL.get(word) or _CANONICAL.get(_stem(word)) or _stem(word))
    return out


def _load_chunks():
    """Split every .md file in knowledge_base/ into sections (one section = one passage)."""
    chunks = []
    for path in sorted(config.KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = path.stem.replace("_", " ").title()
        sections = re.split(r"(?m)^## ", text)
        for part in sections[1:] if len(sections) > 1 else sections:
            heading, _, body = part.partition("\n")
            heading = heading.lstrip("# ").strip() or title
            passage = body.strip()
            if passage:
                chunks.append(
                    {
                        "file": path.name,
                        "heading": heading,
                        "text": passage,
                        "terms": set(_terms(heading + " " + passage)),
                        "heading_terms": set(_terms(heading)),
                    }
                )
    return chunks


def _search(query: str, top_k: int = 3):
    chunks = _load_chunks()
    query_terms = list(dict.fromkeys(_terms(query)))
    strong = [t for t in query_terms if t not in _WEAK]
    if not chunks or not strong:
        return []

    doc_freq = {t: sum(1 for c in chunks if t in c["terms"]) for t in query_terms}
    needed = min(2, len(strong))  # a passage must match at least 2 real words (or 1 if the query has 1)

    scored = []
    for chunk in chunks:
        matched = [t for t in strong if t in chunk["terms"]]
        in_heading = any(t in chunk["heading_terms"] for t in matched)
        if len(matched) < (1 if in_heading else needed):   # one match is enough if it is in the section title
            continue
        score = sum(math.log(1 + len(chunks) / max(doc_freq[t], 1)) for t in matched)
        score += sum(1.0 for t in matched if t in chunk["heading_terms"])  # heading match bonus
        score += 0.3 * sum(1 for t in query_terms if t in _WEAK and t in chunk["terms"])
        scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return []
    best = scored[0][0]
    return [chunk for score, chunk in scored[:top_k] if score >= 0.5 * best]


def search_kb(query: str) -> str:
    """Search the ShopNest company documents (shipping, refunds, accounts, products, billing).

    Pass a SHORT keyword query (4 to 8 words), for example "late delivery delay tracking".
    Returns matching passages, each labelled with the source file name, or NO_MATCH.
    """
    STATE.searched = True
    hits = _search(query)
    if not hits:
        STATE.kb_found = False
        STATE.kb_sources = []
        STATE.passages = ""
        return "NO_MATCH: no relevant passage was found in the company documents."

    STATE.kb_found = True
    STATE.kb_sources = list(dict.fromkeys(h["file"] for h in hits))
    blocks = [f"[Source: {h['file']} | Section: {h['heading']}]\n{h['text']}" for h in hits]
    STATE.passages = "\n\n".join(blocks)
    return STATE.passages


# ---------------------------------------------------------------- the agent
SYSTEM_MESSAGE = f"""You are the Knowledge Base Agent of the {config.COMPANY_NAME} support desk.
Your single job is to find the company documents that are relevant to the complaint. You do not answer the customer.

Steps:
1. Read the Customer Query Agent's JSON (category, summary) and the complaint.
2. Call the search_kb tool ONCE with a short keyword query (4 to 8 words) that names the problem,
   for example "late delivery delay tracking". Do not paste the whole complaint into the query.
3. After the tool returns, reply with the passages exactly as the tool returned them, keeping each
   "[Source: file | Section: ...]" label. Add nothing from your own knowledge.
4. If the tool returns NO_MATCH, reply with exactly: NO_MATCH - no relevant document found.
"""


def build_knowledge_agent(model_client) -> AssistantAgent:
    return AssistantAgent(
        name="knowledge_agent",
        description="Searches the company documents with search_kb and returns matching passages with the source file name.",
        model_client=model_client,
        tools=[search_kb],
        system_message=SYSTEM_MESSAGE,
        reflect_on_tool_use=True,
    )