"""The six test complaints from the assignment, used by the UI dropdown and by evaluate.py."""

EXAMPLES = [
    {
        "label": "1. Late order",
        "text": "Where is my order? It was supposed to arrive yesterday.",
        "customer": "Priya",
        "order_id": "ORD-4512",
        "expect_category": "Shipping",
        "expect_status": "Resolved",
    },
    {
        "label": "2. Return shoes / refund",
        "text": "I want to return the shoes I bought last week. How do I get a refund?",
        "customer": "Arjun",
        "order_id": "ORD-4620",
        "expect_category": "Refund",
        "expect_status": "Resolved",
    },
    {
        "label": "3. Forgot password",
        "text": "I forgot my password and can't log in.",
        "customer": "Meena",
        "order_id": "",
        "expect_category": "Account",
        "expect_status": "Resolved",
    },
    {
        "label": "4. Broken blender",
        "text": "The blender I received is broken. Can I get a replacement?",
        "customer": "Karthik",
        "order_id": "ORD-4733",
        "expect_category": "Product",
        "expect_status": "Resolved",
    },
    {
        "label": "5. Charged three times",
        "text": "You charged my card three times! Fix this now or I'm contacting my bank and a lawyer.",
        "customer": "Rahul",
        "order_id": "ORD-4801",
        "expect_category": "Billing",
        "expect_status": "Escalated",
    },
    {
        "label": "6. Gift cards for 500 employees",
        "text": "Do you sell gift cards for a company of 500 employees with custom branding?",
        "customer": "Sunita",
        "order_id": "",
        "expect_category": "Other",
        "expect_status": "Escalated",
    },
]