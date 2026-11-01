"""Facts about the ticket that is running right now.

The agents talk to each other in text, which can be mis-copied. Anything that must be
exactly right (the original complaint, which files the Knowledge Agent really used) is
kept here by plain Python code and written to the log from here.
"""

from dataclasses import dataclass, field


@dataclass
class RunState:
    complaint: str = ""            # complaint after personal data was masked
    customer_name: str = ""
    order_id: str = ""
    kb_sources: list = field(default_factory=list)
    passages: str = ""             # text the Knowledge Agent really retrieved
    kb_found: bool = False
    searched: bool = False         # was search_kb called at all?
    injection: bool = False        # complaint looked like a prompt-injection attempt
    masked_types: list = field(default_factory=list)


STATE = RunState()


def reset_state(**values) -> RunState:
    """Start a fresh ticket."""
    fresh = RunState(**values)
    for name, value in vars(fresh).items():
        setattr(STATE, name, value)
    return STATE