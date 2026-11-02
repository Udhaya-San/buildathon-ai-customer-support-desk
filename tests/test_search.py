"""Fast tests for the knowledge-base keyword search. No AI, no internet, no cost."""

from agents.knowledge_agent import _keyword_search, _load_chunks

def files_found(query):
    return [hit["file"] for hit in _keyword_search(query)]

def test_delivery_question_finds_shipping_policy():
    assert files_found("late delivery delay tracking")[0] == "shipping_policy.md"

def test_password_question_finds_account_document():
    assert files_found("forgot password reset login")[0] == "account_and_login.md"

def test_refund_question_includes_refund_policy():
    assert "refund_policy.md" in files_found("refund return money back")

def test_unrelated_question_finds_nothing():
    assert _keyword_search("weather forecast football") == []

def test_every_passage_has_a_source_file_and_text():
    chunks = _load_chunks()
    assert len(chunks) > 0
    assert all(chunk["file"] and chunk["text"] for chunk in chunks)
    
def test_coupon_question_finds_offers_document():
    assert files_found("coupon not working cashback")[0] == "offers_and_rewards.md"

def test_cancel_question_finds_order_management():
    assert files_found("cancel order before dispatch")[0] == "order_management.md"

def test_gift_cards_for_a_company_still_finds_nothing():
    # this complaint must keep going to a human
    assert _keyword_search("gift cards company employees custom branding") == []