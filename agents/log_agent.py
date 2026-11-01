"""Agent 4 - Log Agent: records the ticket with the log_ticket tool and decides on escalation."""

from autogen_agentchat.agents import AssistantAgent

import config
import ticket_store
from escalation import (
    decide,
    normalise_confidence,
    normalise_sentiment,
    normalise_urgency,
)
from guardrails import unsupported_numbers
from state import STATE


def log_ticket(
    category: str,
    urgency: str,
    sentiment: str,
    summary: str,
    response: str,
    confidence: str,
    escalate: bool = False,
    escalation_reason: str = "",
) -> str:
    """Save one ticket to the log file and return its ticket id and final status.

    category, urgency, sentiment and summary come from the Customer Query Agent.
    response is the customer reply written by the Resolution Agent (the text after REPLY:).
    confidence is the Resolution Agent's confidence (High, Medium or Low).
    escalate is your own decision (true if a human should handle it) and escalation_reason says why.
    """
    # Facts that must be exact come from plain code (state), not from what the AI typed.
    ungrounded = unsupported_numbers(response, STATE.passages, STATE.complaint)
    status, reason = decide(
        urgency=urgency,
        sentiment=sentiment,
        kb_found=STATE.kb_found,
        confidence=confidence,
        complaint=STATE.complaint,
        ungrounded=ungrounded,
        injection=STATE.injection,
        agent_escalate=bool(escalate),
        agent_reason=escalation_reason,
    )

    row = ticket_store.append_ticket(
        {
            "ticket_id": ticket_store.next_ticket_id(),
            "timestamp": ticket_store.now_text(),
            "customer_name": STATE.customer_name,
            "order_id": STATE.order_id,
            "complaint": STATE.complaint,
            "category": (category or "Other").strip().title(),
            "urgency": normalise_urgency(urgency),
            "sentiment": normalise_sentiment(sentiment),
            "summary": (summary or "").strip(),
            "kb_sources": ", ".join(STATE.kb_sources),
            "response": (response or "").strip(),
            "confidence": normalise_confidence(confidence),
            "status": status,
            "escalation_reason": reason,
            "human_review": "Pending" if status == "Escalated" else "Not needed",
            "human_reply": "",
        }
    )
    return f"LOGGED: {row['ticket_id']} | status={status} | reason={reason or 'none'}"


SYSTEM_MESSAGE = f"""You are the Log Agent of the {config.COMPANY_NAME} support desk.
Your single job is to record the ticket and decide whether a human must take over. You do not write to the customer.

Read the conversation, then call the log_ticket tool ONCE with:
- category, urgency, sentiment, summary: copied from the Customer Query Agent's JSON.
- response: the customer reply from the Resolution Agent (the text after "REPLY:"), copied word for word.
- confidence: High, Medium or Low, copied from the Resolution Agent.
- escalate: true if a human should handle the ticket, otherwise false.
- escalation_reason: a short reason when escalate is true, otherwise an empty string.

Escalate (escalate = true) when ANY of these is true:
  urgency is High; the customer is very angry; the Knowledge Agent said NO_MATCH;
  the complaint mentions a legal threat, fraud or a payment dispute; the confidence is Low.
(The tool also checks these rules itself, so the final status is always consistent.)

After the tool returns, reply with exactly: {config.STOP_WORD} <ticket id> <status>
Example: {config.STOP_WORD} TKT-0007 Resolved
"""


def build_log_agent(model_client) -> AssistantAgent:
    return AssistantAgent(
        name="log_agent",
        description="Saves every ticket to the log file with log_ticket and decides whether to escalate it to a human.",
        model_client=model_client,
        tools=[log_ticket],
        system_message=SYSTEM_MESSAGE,
        reflect_on_tool_use=True,
    )