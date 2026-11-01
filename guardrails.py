"""Guardrails: plain Python checks that do not depend on the AI behaving well.

1. Input:  mask personal data (email, phone, card number) before the AI or the log sees it.
2. Input:  detect text that tries to give instructions to the AI (prompt injection).
3. Output: check that numbers in the reply (days, prices, hours) really appear in the
           retrieved company documents, so the Resolution Agent cannot invent a policy.
"""

import re

# ---------- 1. personal data ----------
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_AADHAAR = re.compile(r"\b\d{4}[ -]\d{4}[ -]\d{4}\b")
_CARD = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")
_PHONE = re.compile(r"(?<![\w-])(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)|\+\d{1,3}[\s-]?\d{6,12}(?!\d)")


def mask_personal_data(text: str):
    """Return (masked_text, list_of_types_found)."""
    found = []

    def sub(pattern, label, value):
        nonlocal found
        new_value, count = pattern.subn(label, value)
        if count:
            found.append(label.strip("[]").lower())
        return new_value

    text = sub(_EMAIL, "[EMAIL]", text)
    text = sub(_CARD, "[CARD-NUMBER]", text)      # 13-19 digits first, so cards are not split
    text = sub(_AADHAAR, "[ID-NUMBER]", text)
    text = sub(_PHONE, "[PHONE]", text)
    return text, found


# ---------- 2. prompt injection ----------
_INJECTION_PATTERNS = [
    r"ignore (?:all |any |the )?(?:previous|prior|above|earlier|your)\s+(?:instructions|rules|prompts?)",
    r"disregard (?:the |your |all )?(?:instructions|rules|system prompt)",
    r"(?:reveal|show|print|repeat|tell me) (?:me )?(?:your|the) (?:system prompt|instructions|prompt|rules)",
    r"\byou are now\b",
    r"\bact as (?:an? )?(?:admin|administrator|developer|system)\b",
    r"developer mode|jailbreak",
    r"override (?:the )?(?:rules|policy|policies|escalation)",
    r"mark (?:this |the )?(?:ticket )?as (?:resolved|not escalated)",
]
_INJECTION = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


def looks_like_injection(text: str) -> bool:
    return bool(_INJECTION.search(text or ""))


# ---------- 3. grounding of the reply ----------
_ID_LIKE = re.compile(r"\b[A-Za-z]{2,}-\d+\b")          # ORD-4512, TKT-0007
_LIST_MARKER = re.compile(r"^\s*\d+[.)]\s", re.MULTILINE)  # "1. ", "2) "
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def _numbers(text: str):
    text = _ID_LIKE.sub(" ", text)
    text = _LIST_MARKER.sub(" ", text)
    return {n.replace(",", "") for n in _NUMBER.findall(text)}


def unsupported_numbers(reply: str, *allowed_sources: str):
    """Numbers used in the reply that appear in none of the allowed texts."""
    allowed = set()
    for source in allowed_sources:
        allowed |= _numbers(source or "")
    return sorted(_numbers(reply) - allowed, key=lambda n: (len(n), n))