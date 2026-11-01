"""Run the six assignment test complaints through the real agents and compare with the expected result.

Needs your OPENAI_API_KEY (in .env). Each run adds one row to logs/tickets.csv, so after this
you also have six tickets ready for screenshots.

Run:  python evaluate.py
"""

import asyncio
import sys

import config
from examples import EXAMPLES
from team import run_ticket


async def main() -> int:
    passed = 0
    print(f"Model: {config.MODEL}\n")
    for example in EXAMPLES:
        try:
            _, ticket = await run_ticket(example["text"], example["customer"], example["order_id"])
        except config.MissingKeyError as exc:
            print(exc)
            return 2
        if ticket is None:
            print(f"{example['label']:<34} NOT LOGGED (the team stopped early)")
            continue
        ok_status = ticket["status"] == example["expect_status"]
        ok_category = ticket["category"] == example["expect_category"] or example["expect_category"] == "Other"
        passed += ok_status
        mark = "PASS" if ok_status else "FAIL"
        note = "" if ok_category else f"  <- category differs from {example['expect_category']}"
        print(
            f"{mark}  {example['label']:<32} {ticket['category']:<9} {ticket['urgency']:<7} "
            f"{ticket['sentiment']:<11} {ticket['status']:<10} (expected {example['expect_status']}){note}"
        )
        if ticket["escalation_reason"]:
            print(f"      reason : {ticket['escalation_reason']}")
        print(f"      sources: {ticket['kb_sources'] or 'none'}")
    print(f"\n{passed}/{len(EXAMPLES)} tickets got the expected status. Log: {config.LOG_PATH}")
    return 0 if passed == len(EXAMPLES) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))