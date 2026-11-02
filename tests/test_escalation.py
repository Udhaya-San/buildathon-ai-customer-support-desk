"""Fast tests for the escalation rule in escalation.py. No AI, no internet, no cost."""

from escalation import decide

# A calm complaint that should be Resolved. Each test changes ONE thing.
BASE: dict = {
    "urgency": "Medium",
    "sentiment": "Frustrated",
    "kb_found": True,
    "confidence": "High",
    "complaint": "where is my order",
}


def status_of(**changes):
    return decide(**{**BASE, **changes})[0]


def test_calm_complaint_is_resolved():
    assert status_of() == "Resolved"


def test_high_urgency_escalates():
    assert status_of(urgency="High") == "Escalated"


def test_angry_customer_escalates():
    assert status_of(sentiment="Angry") == "Escalated"


def test_no_matching_document_escalates():
    assert status_of(kb_found=False) == "Escalated"


def test_low_confidence_escalates():
    assert status_of(confidence="Low") == "Escalated"


def test_legal_threat_escalates():
    assert status_of(complaint="I will talk to my lawyer") == "Escalated"


def test_fraud_word_escalates():
    assert status_of(complaint="this is a scam") == "Escalated"


def test_charged_three_times_escalates():
    assert status_of(complaint="you charged me three times") == "Escalated"


def test_invented_numbers_escalate():
    assert status_of(ungrounded=["30"]) == "Escalated"


def test_prompt_injection_escalates():
    assert status_of(injection=True) == "Escalated"


def test_word_issue_is_not_a_legal_threat():
    # "sue" must match as a whole word, not inside "issue"
    assert status_of(complaint="I have an issue with my order") == "Resolved"


def test_reason_lists_every_rule_that_fired():
    status, reason = decide(**{**BASE, "urgency": "High", "sentiment": "Angry"})
    assert status == "Escalated"
    assert "High urgency" in reason
    assert "Angry customer" in reason


def test_resolved_ticket_has_no_reason():
    assert decide(**BASE) == ("Resolved", "")