"""Reading and writing the ticket log (logs/tickets.csv). Opens fine in Excel."""

import csv
from datetime import datetime

import config

COLUMNS = [
    "ticket_id",
    "timestamp",
    "customer_name",
    "order_id",
    "complaint",
    "category",
    "urgency",
    "sentiment",
    "summary",
    "kb_sources",
    "response",
    "confidence",
    "status",
    "escalation_reason",
    "human_review",
    "human_reply",
    "latency_s",
    "tokens",
    "cost_usd",
]

def _read_rows():
    if not config.LOG_PATH.exists():
        return []
    with open(config.LOG_PATH, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def all_tickets():
    return _read_rows()


def ticket_count() -> int:
    return len(_read_rows())


def latest_ticket():
    rows = _read_rows()
    return rows[-1] if rows else None


def next_ticket_id() -> str:
    numbers = []
    for row in _read_rows():
        try:
            numbers.append(int(str(row["ticket_id"]).split("-")[-1]))
        except (KeyError, ValueError):
            continue
    return f"TKT-{(max(numbers) + 1 if numbers else 1):04d}"


def append_ticket(row: dict) -> dict:
    """Add one ticket. Missing columns are left empty."""
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    row = {col: row.get(col, "") for col in COLUMNS}
    new_file = not config.LOG_PATH.exists() or config.LOG_PATH.stat().st_size == 0
    with open(config.LOG_PATH, "a", newline="", encoding="utf-8-sig" if new_file else "utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)
    return row


def get_ticket(ticket_id: str):
    for row in _read_rows():
        if row.get("ticket_id") == ticket_id:
            return row
    return None


def update_ticket(ticket_id: str, **fields) -> bool:
    """Change fields of an existing ticket (used by the human review step)."""
    rows = _read_rows()
    changed = False
    for row in rows:
        if row.get("ticket_id") == ticket_id:
            row.update({k: v for k, v in fields.items() if k in COLUMNS})
            changed = True
    if changed:
        with open(config.LOG_PATH, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow({col: row.get(col, "") for col in COLUMNS})
    return changed


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

