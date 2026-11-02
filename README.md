# AI Customer Support Desk (AutoGen + Streamlit)

A multi-agent support desk for a made-up online store, **ShopNest**. A customer complaint goes through
four AutoGen agents. They find the answer in the company's own documents, write a reply, log the ticket,
and hand the difficult cases to a human.

> Social Eagle · Multi-Agent Systems · Buildathon: *AI Customer Support Automation*

![Resolved ticket](screenshots/02-resolved.png)


## How a complaint flows

![Architecture](docs/architecture.png)

```
Streamlit form (complaint, optional name and order ID)
        |
        v   Input guardrails: mask personal data, detect hidden instructions
1. Customer Query Agent   -> category, urgency, sentiment, one-line summary
        |
2. Knowledge Base Agent   -> calls search_kb(), returns passages + the source file name
        |
3. Resolution Agent       -> customer reply using ONLY those passages + a confidence level
        |
4. Log Agent              -> calls log_ticket(): writes one row to logs/tickets.csv, decides Resolved / Escalated
        |
        v
Streamlit shows every agent step, the reply, a green Resolved or red Escalated badge,
a human review box for escalated tickets, the Ticket Log table and a small dashboard
```

The four agents are `AssistantAgent`s in a `RoundRobinGroupChat`, so they always speak in the order above.
The team stops when the Log Agent says `LOGGED` (`TextMentionTermination`), with a 16 message limit
(`MaxMessageTermination`) as a safety net.

## Key idea: the AI writes, plain code enforces

AI output can slip, so everything that must be right is ordinary Python:

| Plain Python (always the same) | AI agents (judgement) |
|---|---|
| Which documents were really used (`kb_sources`) | Understanding the complaint |
| Original complaint saved in the log | Choosing keywords to search |
| Final Resolved / Escalated decision (`escalation.py`) | Writing a polite reply |
| Masking emails, phone and card numbers | Judging confidence |
| Blocking numbers in a reply that are not in the documents | |

## Screenshots

**Ticket raised**

![Ticket raised](screenshots/01-ticket-raised.png)

**Escalated ticket with the human review step**

![Escalated ticket](screenshots/03-escalated.png)

**Ticket Log**

![Ticket log](screenshots/04-ticket-log.png)

**Dashboard**

![Dashboard](screenshots/05-dashboard.png)

![Graphs and logs](screenshots/06-graphs-and-logs.png)

**Knowledge base files**

![Knowledge base](screenshots/07-knowledge-base-files.png)

## Project structure

```
buildathon-ai-customer-support-desk/
├── app.py                  # Streamlit UI
├── agents/
│   ├── query_agent.py      # Customer Query Agent
│   ├── knowledge_agent.py  # Knowledge Base Agent + search_kb tool
│   ├── resolution_agent.py # Resolution Agent
│   └── log_agent.py        # Log Agent + log_ticket tool
├── team.py                 # wires the agents into one AutoGen team
├── escalation.py           # the escalation rule (plain code)
├── guardrails.py           # input and output guardrails (plain code)
├── ticket_store.py         # reads and writes logs/tickets.csv
├── state.py                # facts about the ticket that is running
├── examples.py             # the 6 test complaints from the assignment
├── evaluate.py             # runs the 6 complaints with the real AI
├── knowledge_base/         # 5 short company documents (.md)
├── logs/tickets.csv        # created automatically
├── screenshots/            # UI screenshots used in this README
├── .streamlit/config.toml  # colours and theme
├── .env.example            # OPENAI_API_KEY=your-key-here
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

Needs Python 3.10 or newer and an OpenAI API key.

**Windows (PowerShell)**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then open .env and put your real key after OPENAI_API_KEY=
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env and add your key
```

The key is read only from `.env` / the environment. `.env` is in `.gitignore`, so it is never committed.
Optional: set `OPENAI_MODEL` in `.env` (default `gpt-4o-mini`).

## Run

```bash
streamlit run app.py
```

The app opens at http://localhost:8501. Pick a sample complaint from the dropdown (or type your own)
and press **Submit complaint**.

Run all six assignment complaints in one go (adds six tickets to the log):
```bash
python evaluate.py
```

## The knowledge base

Five short documents for ShopNest in `knowledge_base/`: shipping policy, refund policy, account and login,
product FAQ, payments and billing. They contain real-looking details (delivery times, a 14 day return window,
password reset steps) so every answer can be checked against the file.

`search_kb(query)` splits each document into sections, ignores filler words, matches synonyms
(late = delayed, charged = billed, etc.) and returns the best passages with a
`[Source: file | Section: ...]` label, or `NO_MATCH`. A passage needs at least two real keyword matches,
so an unrelated question finds nothing instead of a wrong answer.

## Escalation rule

A ticket is **Escalated** to a human when any of these is true:

1. urgency is High
2. the customer is very angry
3. the Knowledge Agent found no matching document
4. the complaint mentions a legal threat, fraud or a payment dispute
5. the Resolution Agent's confidence is Low
6. the reply uses numbers (days, prices) that are not in the retrieved documents (guardrail)
7. the complaint looks like a prompt-injection attempt (guardrail)

The reason is written to `escalation_reason` in the log and shown in the UI.

## Guardrails and human-in-the-loop

- **Personal data is masked** (email, phone, card and ID numbers) before the AI sees the complaint and before it is logged.
- **Hidden instructions are ignored.** Text such as "ignore all previous instructions" is detected, the agents are warned, and the ticket is escalated.
- **No invented policies.** Numbers in the reply must appear in the retrieved passages or the complaint, or the ticket is escalated.
- **Human review.** For an Escalated ticket the UI shows an editable reply and an **Approve reply (mark as sent)** button.
  The approval and the final text are saved in the log (`human_review`, `human_reply`). Nothing is actually emailed; the
  approve step is where a real email or WhatsApp call would go.

## Log file format

`logs/tickets.csv` (opens in Excel) has one row per ticket:

`ticket_id, timestamp, customer_name, order_id, complaint, category, urgency, sentiment, summary, kb_sources, response, confidence, status, escalation_reason, human_review, human_reply`

## Test results (`python evaluate.py`, model gpt-4o-mini)

| # | Complaint | Result |
|---|---|---|
| 1 | Where is my order? It was supposed to arrive yesterday. | Shipping, **Resolved**, from the shipping policy |
| 2 | I want to return the shoes I bought last week. How do I get a refund? | Refund, **Resolved**, from the refund policy |
| 3 | I forgot my password and can't log in. | Account, **Resolved**, reset steps |
| 4 | The blender I received is broken. Can I get a replacement? | Product, **Resolved**, replacement process |
| 5 | You charged my card three times! Fix this now or I'm contacting my bank and a lawyer. | Billing, High, Angry, **Escalated** (3 reasons) |
| 6 | Do you sell gift cards for a company of 500 employees with custom branding? | **Escalated**: the reply was rated Low confidence, so a human follows up |

All six tickets got the expected status.

Fast offline tests: run `pytest` (31 tests, about 1 second, no API key needed).
All test cases are listed in [docs/test_cases.md](docs/test_cases.md).

## What I learned

- A plain-code rule is safer than asking the AI to "remember" a rule: even if the AI marks a ticket as not urgent, the escalation code still escalates a legal threat.
- Testing with a fixed set of complaints and written expectations found a wrong test case quickly.
- A second safety layer matters: for the gift card complaint the search found a loosely related passage, and the Resolution Agent's Low confidence still sent it to a human.

## Notes and limits

- The company, policies and prices are invented for this assignment.
- Search is keyword based. Embeddings with ChromaDB or FAISS would be the next upgrade.
- The human review step is an approve button in the UI, not AutoGen's `UserProxyAgent`.
- Keep your API key out of screenshots and posts. If a key was ever pushed to GitHub, revoke it and create a new one.