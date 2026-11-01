"""The escalation rule, written as code so it is applied the same way every time.

A ticket is Escalated to a human when ANY of these is true:
  - urgency is High
  - the customer is very angry
  - the Knowledge Agent found no matching document
  - the complaint mentions a legal threat, fraud or a payment dispute
  - the Resolution Agent's confidence is low
  - the reply uses numbers that are not in the retrieved documents (guardrail)
  - the complaint looks like a prompt-injection attempt (guardrail)
  - the Log Agent itself judged the case complicated
"""

import re

_LEGAL_FRAUD_PAYMENT = re.compile(
    r"\b(lawyer|attorney|legal action|legal notice|legally|sue|suing|court|consumer forum|"
    r"consumer court|police|fraud|fraudulent|scam|scammed|chargeback|dispute|"
    r"(?:contact|contacting|call|calling|inform|informing|report|reporting|tell|telling)\s+(?:my|the)\s+bank|"
    r"charged\s+(?:me\s+)?(?:twice|thrice|again|multiple times|\w+\s+times)|"
    r"double[- ]charged|unauthori[sz]ed (?:charge|transaction)|stolen)\b",
    re.IGNORECASE,
)

_ANGRY = {"angry", "very angry", "furious", "outraged", "enraged"}


def normalise_urgency(value: str) -> str:
    v = (value or "").strip().lower()
    if v.startswith("high") or v in {"urgent", "critical"}:
        return "High"
    if v.startswith("low"):
        return "Low"
    return "Medium"


def normalise_sentiment(value: str) -> str:
    v = (value or "").strip().lower()
    if v in _ANGRY or "angry" in v or "furious" in v:
        return "Angry"
    if "frustrat" in v or "upset" in v or "annoy" in v or "disappoint" in v:
        return "Frustrated"
    if "positive" in v or "happy" in v or "satisf" in v:
        return "Positive"
    return "Neutral"


def normalise_confidence(value: str) -> str:
    v = (value or "").strip().lower()
    if v.startswith("high"):
        return "High"
    if v.startswith("low"):
        return "Low"
    return "Medium"


def decide(
    *,
    urgency: str,
    sentiment: str,
    kb_found: bool,
    confidence: str,
    complaint: str,
    ungrounded=(),
    injection: bool = False,
    agent_escalate: bool = False,
    agent_reason: str = "",
):
    """Return (status, reason). status is 'Resolved' or 'Escalated'."""
    reasons = []
    if normalise_urgency(urgency) == "High":
        reasons.append("High urgency")
    if normalise_sentiment(sentiment) == "Angry":
        reasons.append("Angry customer")
    if not kb_found:
        reasons.append("No matching document in the knowledge base")
    hit = _LEGAL_FRAUD_PAYMENT.search(complaint or "")
    if hit:
        reasons.append(f"Legal, fraud or payment dispute mentioned ('{hit.group(0).lower()}')")
    if normalise_confidence(confidence) == "Low":
        reasons.append("Low confidence in the reply")
    if ungrounded:
        reasons.append("Reply uses details not found in the documents (" + ", ".join(ungrounded) + ")")
    if injection:
        reasons.append("Possible prompt-injection text in the complaint")
    if agent_escalate and not reasons:
        reasons.append((agent_reason or "Log Agent judged the case complicated").strip())

    if reasons:
        return "Escalated", " + ".join(reasons)
    return "Resolved", ""