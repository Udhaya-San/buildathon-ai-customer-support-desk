"""Tests for the newer escalation rules. No AI, no internet, no cost."""

from escalation import decide

BASE: dict = {
    "urgency": "Medium",
    "sentiment": "Frustrated",
    "kb_found": True,
    "confidence": "High",
    "complaint": "where is my order",
}


def status_of(**changes):
    return decide(**{**BASE, **changes})[0]


def test_company_bulk_enquiry_escalates():
    assert status_of(complaint="Do you sell gift cards for a company of 500 employees with custom branding?") == "Escalated"


def test_wholesale_escalates():
    assert status_of(complaint="I want to buy wholesale") == "Escalated"


def test_unofficial_channel_escalates():
    assert status_of(complaint="I paid on a website I found on Instagram") == "Escalated"


def test_high_value_amount_escalates():
    assert status_of(complaint="I paid Rs 15,000 for this order") == "Escalated"


def test_small_amount_does_not_escalate():
    assert status_of(complaint="I paid Rs 999 for this order") == "Resolved"


def test_asking_for_a_manager_escalates():
    assert status_of(complaint="I want to speak to a manager") == "Escalated"


def test_delivery_agent_is_not_a_request_for_a_human():
    assert status_of(complaint="the delivery agent was late") == "Resolved"


def test_word_company_alone_does_not_escalate():
    assert status_of(complaint="The company courier was rude") == "Resolved"


def test_unofficial_contact_in_reply_escalates():
    assert status_of(unofficial=["help@fastrefund.com"]) == "Escalated"


def test_calm_complaint_still_resolves():
    assert status_of() == "Resolved"