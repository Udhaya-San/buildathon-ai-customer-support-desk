"""Tests for the output guardrail: no unofficial contact details in a reply."""

from guardrails import unofficial_contacts

DOCS = "Write to support@shopnest.example. Call 080 4000 1234."


def test_official_email_is_allowed():
    assert unofficial_contacts("Email support@shopnest.example", DOCS) == []


def test_unknown_email_is_flagged():
    assert unofficial_contacts("Email help@fastrefund.com", DOCS) == ["help@fastrefund.com"]


def test_unknown_link_is_flagged():
    assert unofficial_contacts("Visit www.fastrefund.com/claim now", DOCS) == ["www.fastrefund.com/claim"]


def test_official_link_is_allowed():
    assert unofficial_contacts("Visit https://www.shopnest.example/help", DOCS) == []


def test_unknown_phone_is_flagged():
    assert unofficial_contacts("Call 9876543210 for your refund", DOCS) == ["9876543210"]


def test_phone_from_the_documents_is_allowed():
    assert unofficial_contacts("Call +91 80 4000 1234", DOCS + " +91 80 4000 1234") == []


def test_reply_without_contacts_is_clean():
    assert unofficial_contacts("Your refund takes 5 to 7 days", DOCS) == []