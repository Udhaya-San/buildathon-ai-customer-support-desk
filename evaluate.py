"""Run every test complaint through the real agents and score PASS / FAIL.

Needs your OPENAI_API_KEY (in .env). Each run adds one row to logs/tickets.csv.
Writes eval_results.md, a table you can paste into the README.

Run:  python evaluate.py
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import config
from examples import EXAMPLES
from team import run_ticket

RESULTS_FILE = Path(__file__).parent / "eval_results.md"


def accepted(expect):
    """expect_status can be one word or a tuple of allowed words."""
    return (expect,) if isinstance(expect, str) else tuple(expect)


def check(example, ticket):
    """Return (passed, problems, actual_status)."""
    actual = "Rejected" if ticket is None else ticket["status"]
    problems = []
    if actual not in accepted(example["expect_status"]):
        problems.append(f"status {actual}, expected {' or '.join(accepted(example['expect_status']))}")
    if ticket is not None:
        saved = f"{ticket['complaint']} {ticket['response']}".lower()
        for bad in example["forbid"]:
            if bad.lower() in saved:
                problems.append(f"'{bad}' found in the saved ticket")
    return not problems, problems, actual


def write_report(rows, passed):
    lines = [
        "# Evaluation results",
        "",
        f"Model: {config.MODEL} | {datetime.now():%Y-%m-%d} | **{passed}/{len(rows)} passed**",
        "",
        "| Case | Group | Complaint | Expected | Actual | Result |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for example, actual, ok, _ in rows:
        expected = " or ".join(accepted(example["expect_status"]))
        text = (example["text"].strip() or "(empty)").replace("|", "/")[:60]
        lines.append(
            f"| {example['label']} | {example['group']} | {text} | {expected} | {actual} | "
            f"{'PASS' if ok else 'FAIL'} |"
        )
    RESULTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def main() -> int:
    print(f"Model: {config.MODEL}\n")
    rows, passed = [], 0
    for example in EXAMPLES:
        try:
            _, ticket = await run_ticket(example["text"], example["customer"], example["order_id"])
        except config.MissingKeyError as exc:
            print(exc)
            return 2
        except Exception as exc:  # one bad case must not stop the whole run
            print(f"ERROR {example['label']}: {exc}")
            rows.append((example, "Error", False, [str(exc)]))
            continue
        ok, problems, actual = check(example, ticket)
        passed += ok
        rows.append((example, actual, ok, problems))
        extra = f"{ticket['latency_s']}s ${ticket['cost_usd']}" if ticket else ""
        print(f"{'PASS' if ok else 'FAIL'}  {example['label']:<34} {actual:<10} ({example['group']}) {extra}")
        for problem in problems:
            print(f"      problem: {problem}")
        if ticket and ticket["escalation_reason"]:
            print(f"      reason : {ticket['escalation_reason']}")
    write_report(rows, passed)
    print(f"\n{passed}/{len(EXAMPLES)} cases passed. Table saved to {RESULTS_FILE.name}. Log: {config.LOG_PATH}")
    return 0 if passed == len(EXAMPLES) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))