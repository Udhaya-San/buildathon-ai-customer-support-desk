"""Streamlit UI for the ShopNest AI Customer Support Desk.   Run:  streamlit run app.py"""

import asyncio
import html
import json
import os
import re

import altair as alt
import pandas as pd
import streamlit as st
from autogen_agentchat.messages import TextMessage, ToolCallExecutionEvent, ToolCallRequestEvent

import config
import ticket_store
from examples import EXAMPLES
from state import STATE
from team import stream_ticket

st.set_page_config(page_title=f"{config.COMPANY_NAME} AI Support Desk", page_icon="🎧", layout="wide")

AGENTS = {
    "query_agent": ("1", "🔎", "Customer Query Agent", "Understands the complaint"),
    "knowledge_agent": ("2", "📚", "Knowledge Base Agent", "Finds the matching company documents"),
    "resolution_agent": ("3", "✍️", "Resolution Agent", "Writes the reply from those documents only"),
    "log_agent": ("4", "🗂️", "Log Agent", "Records the ticket and decides on escalation"),
}

GREEN, LIME, RED = "#0E3B2E", "#B8F000", "#D64545"

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
.stApp {font-family: 'Plus Jakarta Sans', sans-serif; background: #F2F5F3;}
[data-testid="stAppDeployButton"], .stAppDeployButton {display: none;}
[data-testid="stHeader"] {background: transparent;}
.block-container {padding-top: 2.2rem; max-width: 1320px;}

/* ---- sidebar ---- */
section[data-testid="stSidebar"] {background: #0E3B2E;}
section[data-testid="stSidebar"] * {color: #DCEBE3;}
section[data-testid="stSidebar"] hr {border-color: rgba(255,255,255,.12);}
.side-brand {font-size: 1.1rem; font-weight: 800; color: #fff !important; margin: .2rem 0 .1rem 0;}
.side-brand span {color: #B8F000 !important;}
.side-label {font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; opacity: .6; margin: 1.1rem 0 .5rem 0;}
.agent-row {display: flex; gap: .7rem; align-items: flex-start; padding: .55rem .7rem; border-radius: 12px; margin-bottom: .35rem;
            background: rgba(255,255,255,.05);}
.agent-num {min-width: 1.5rem; height: 1.5rem; border-radius: 50%; background: #B8F000; color: #0E3B2E !important;
            font-weight: 800; font-size: .8rem; display: flex; align-items: center; justify-content: center;}
.agent-title {font-weight: 600; font-size: .92rem; color: #fff !important;}
.agent-sub {font-size: .78rem; opacity: .7;}
.rule {font-size: .85rem; margin: .25rem 0; opacity: .9;}
.rule:before {content: "✓"; color: #B8F000 !important; font-weight: 800; margin-right: .5rem;}
.status-chip {display: inline-block; padding: .2rem .7rem; border-radius: 999px; font-size: .78rem; font-weight: 600;
              background: rgba(184,240,0,.16); color: #B8F000 !important; margin-right: .4rem;}
.status-chip.bad {background: rgba(214,69,69,.2); color: #FF9A9A !important;}

/* ---- hero + kpi cards ---- */
.hero {position: relative; overflow: hidden; border-radius: 22px; padding: 1.7rem 2rem; margin-bottom: 1.1rem;
       background: linear-gradient(135deg, #0B2F24 0%, #0E3B2E 60%, #14503E 100%); color: #fff;}
.hero:after {content: ""; position: absolute; right: -60px; bottom: -80px; width: 260px; height: 260px; border-radius: 50%;
             border: 34px solid #B8F000; opacity: .95;}
.hero:before {content: ""; position: absolute; right: 150px; top: -70px; width: 140px; height: 140px; border-radius: 50%;
              background: rgba(184,240,0,.18);}
.hero .pill {display: inline-block; background: rgba(255,255,255,.12); border-radius: 999px; padding: .2rem .8rem;
             font-size: .78rem; font-weight: 600; margin-bottom: .8rem;}
.hero .pill i {display: inline-block; width: .5rem; height: .5rem; border-radius: 50%; background: #B8F000; margin-right: .45rem;}
.hero h1 {font-size: 1.9rem; font-weight: 800; margin: 0 0 .35rem 0; color: #fff; padding: 0; line-height: 1.2;}
.hero p {margin: 0; opacity: .8; max-width: 640px; font-size: .95rem;}
.hero .flow {margin-top: 1rem; font-size: .85rem; color: #B8F000; font-weight: 700;}

.kpi {background: #fff; border-radius: 18px; padding: 1.1rem 1.3rem; box-shadow: 0 6px 22px rgba(14,59,46,.07); height: 100%;}
.kpi .k-label {font-size: .85rem; color: #6B7C74; font-weight: 600;}
.kpi .k-value {font-size: 2.1rem; font-weight: 800; color: #10231C; line-height: 1.2; margin: .15rem 0;}
.kpi .k-note {font-size: .8rem; font-weight: 600;}
.kpi .k-note.up {color: #1F9D55;} .kpi .k-note.down {color: #D64545;} .kpi .k-note.flat {color: #6B7C74;}

/* ---- cards (containers with a key) ---- */
[class*="st-key-card_"] {background: #fff; border-radius: 20px; padding: 1.3rem 1.5rem; box-shadow: 0 6px 22px rgba(14,59,46,.07);
                         margin-bottom: 1.1rem;}
.card-title {font-size: 1.12rem; font-weight: 800; color: #10231C; margin: 0 0 .15rem 0;}
.card-sub {font-size: .85rem; color: #6B7C74; margin-bottom: .8rem;}

/* ---- inputs and buttons ---- */
.stTextArea textarea, .stTextInput input {background: #F5F8F6 !important; border-radius: 12px !important; border: 1.5px solid #B9C9C1 !important;}
div[data-baseweb="select"] > div {background: #FFFFFF !important; border-radius: 12px !important; border: 1.5px solid #0E3B2E !important; cursor: pointer;}
.stButton > button, .stDownloadButton > button {border-radius: 12px; font-weight: 700; padding: .5rem 1.4rem;}
.stButton > button[kind="primary"] {background: #0E3B2E; color: #fff; border: none;}
.stButton > button[kind="primary"]:hover {background: #14503E; color: #B8F000;}
[data-testid="stExpander"] {border-radius: 14px; border: 1px solid #E2EAE6; background: #FBFDFC;}
section[data-testid="stSidebar"] [data-testid="stExpander"] {background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.15);}

/* ---- result ---- */
.reply-box {border-radius: 14px; padding: 1rem 1.2rem; margin: .4rem 0 1rem 0; background: #F8FAF9; border: 1px solid #E2EAE6;}
.reply-box.resolved {border-left: 6px solid #1F9D55;}
.reply-box.escalated {border-left: 6px solid #D64545;}
.badge {display: inline-block; padding: .18rem .75rem; border-radius: 999px; font-weight: 800; font-size: .8rem; color: #fff; margin-right: .6rem;}
.badge.resolved {background: #1F9D55;}
.badge.escalated {background: #D64545;}
.chip {display: inline-block; padding: .15rem .65rem; border-radius: 8px; font-size: .8rem; font-weight: 600;
       background: #EAF1ED; color: #34594A; margin: 0 .35rem .35rem 0;}
.small-note {font-size: .85rem; opacity: .75;}
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ helpers
def safe_error(exc: Exception) -> str:
    """Error text with anything that looks like an API key removed."""
    return re.sub(r"sk-[A-Za-z0-9_\-*]{6,}", "sk-***", f"{type(exc).__name__}: {exc}")


def esc(text: str) -> str:
    return html.escape(text or "").replace("\n", "<br>")


def parse_json(text: str):
    try:
        cleaned = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.MULTILINE).strip()
        return json.loads(cleaned)
    except (ValueError, TypeError):
        return None


def split_resolution(text: str):
    """Split 'REPLY: ... CONFIDENCE: High' into (reply, confidence)."""
    text = (text or "").strip()
    match = re.search(r"CONFIDENCE:\s*(\w+)\s*$", text, flags=re.IGNORECASE)
    confidence = match.group(1) if match else ""
    body = text[: match.start()] if match else text
    body = re.sub(r"^\s*REPLY:\s*", "", body, flags=re.IGNORECASE).strip()
    return body, confidence


def card_header(title: str, subtitle: str = ""):
    sub = f"<div class='card-sub'>{esc(subtitle)}</div>" if subtitle else ""
    st.markdown(f"<div class='card-title'>{esc(title)}</div>{sub}", unsafe_allow_html=True)


def kpi(col, label: str, value: str, note: str, tone: str = "flat"):
    col.markdown(
        f"<div class='kpi'><div class='k-label'>{esc(label)}</div><div class='k-value'>{esc(value)}</div>"
        f"<div class='k-note {tone}'>{esc(note)}</div></div>",
        unsafe_allow_html=True,
    )


def count_chart(counts, colors=None):
    """Fixed (non-zoomable) bar chart of a value_counts() series. colors = {label: hex}."""
    data = counts.rename_axis("label").reset_index(name="count")
    if colors:
        color = alt.Color("label:N", scale=alt.Scale(domain=list(colors), range=list(colors.values())), legend=None)
    else:
        color = alt.value(GREEN)
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=38)
        .encode(
            x=alt.X("label:N", sort=None, title=None, axis=alt.Axis(labelAngle=0, domain=False, ticks=False)),
            y=alt.Y("count:Q", title=None, axis=alt.Axis(tickMinStep=1, domain=False, gridColor="#E8EEEA")),
            color=color,
            tooltip=["label", "count"],
        )
        .properties(height=240)
        .configure_view(strokeWidth=0)
    )


async def run_live(complaint, customer, order_id, status_box):
    """Run the team and collect each agent's output while showing progress."""
    steps = {name: {"text": "", "tool_calls": [], "tool_results": []} for name in AGENTS}
    async for item in stream_ticket(complaint, customer, order_id):
        source = getattr(item, "source", None)
        if source not in steps:
            continue
        if isinstance(item, ToolCallRequestEvent):
            for call in item.content:
                steps[source]["tool_calls"].append(f"{call.name}({call.arguments})")
            status_box.write(f"🛠️ **{AGENTS[source][2]}** is calling a tool…")
        elif isinstance(item, ToolCallExecutionEvent):
            for result in item.content:
                steps[source]["tool_results"].append(result.content)
        elif isinstance(item, TextMessage):
            steps[source]["text"] = item.content
            icon, name = AGENTS[source][1], AGENTS[source][2]
            status_box.write(f"{icon} **{name}** finished.")
    return steps

def signature(complaint, customer, order_id):
    """A fingerprint of the form, ignoring case and extra spaces, to spot a repeated submit."""
    clean = lambda t: " ".join((t or "").lower().split())
    return (clean(complaint), clean(customer), clean(order_id))


def process(complaint, customer, order_id):
    """Submit handler: run the agents, then keep the outcome in session_state."""
    before = ticket_store.ticket_count()
    outcome = {"error": None, "steps": {}, "ticket_id": None, "masked": [], "injection": False}
    with st.status("The support team is working on your complaint…", expanded=True) as status_box:
        try:
            outcome["steps"] = asyncio.run(run_live(complaint, customer, order_id, status_box))
            outcome["masked"] = list(STATE.masked_types)
            outcome["injection"] = STATE.injection
            if ticket_store.ticket_count() > before:
                latest = ticket_store.latest_ticket()
                outcome["ticket_id"] = latest["ticket_id"] if latest else None
                status_box.update(label="Done. Ticket logged.", state="complete", expanded=False)
            else:
                outcome["error"] = "The team stopped before the ticket was logged."
                status_box.update(label="The team stopped early.", state="error")
        except config.MissingKeyError as exc:
            outcome["error"] = str(exc)
            status_box.update(label="API key missing", state="error")
        except Exception as exc:  # noqa: BLE001 - show any failure in the UI instead of crashing
            outcome["error"] = safe_error(exc)
            status_box.update(label="Something went wrong", state="error")
    st.session_state["outcome"] = outcome
    if outcome["ticket_id"]:   # remember what was sent, so the same form cannot be sent twice
        st.session_state["last_sig"] = signature(complaint, customer, order_id)
    st.rerun()


# ------------------------------------------------------------------ rendering
def render_step(name, data):
    number, icon, title, subtitle = AGENTS[name]
    text = data["text"]
    done = bool(text or data["tool_results"])
    with st.expander(f"{'✅' if done else '⏳'}  Step {number} · {icon} {title}", expanded=False):
        st.caption(subtitle)
        if name == "query_agent":
            info = parse_json(text)
            if info:
                cols = st.columns(4)
                for col, key in zip(cols, ["category", "urgency", "sentiment", "summary"]):
                    col.markdown(f"**{key.title()}**  \n{info.get(key, '-')}")
            else:
                st.write(text or "(no output)")
        elif name == "knowledge_agent":
            for call in data["tool_calls"]:
                st.code(call, language="text")
            if "NO_MATCH" in (text or "") or any("NO_MATCH" in r for r in data["tool_results"]):
                st.warning("No matching document found in the knowledge base.")
            else:
                st.markdown(text or "(no output)")
        elif name == "resolution_agent":
            reply, confidence = split_resolution(text)
            st.markdown(f"> {reply}" if reply else "(no output)")
            if confidence:
                st.markdown(f"<span class='chip'>Confidence: {esc(confidence)}</span>", unsafe_allow_html=True)
        else:
            for call in data["tool_calls"]:
                st.code(call, language="text")
            for result in data["tool_results"]:
                st.success(result)
            if text:
                st.write(text)


def render_result(outcome):
    card_header("Result", "What the four agents did with this complaint")
    if outcome.get("masked"):
        st.info("🔒 Guardrail: personal data (" + ", ".join(outcome["masked"]) + ") was masked before it reached the AI and the log.")
    if outcome.get("injection"):
        st.warning("🛡️ Guardrail: the complaint contained text that tries to instruct the AI. It was ignored and the ticket was escalated.")

    st.markdown("##### Agent steps")
    for name in AGENTS:
        render_step(name, outcome["steps"].get(name, {"text": "", "tool_calls": [], "tool_results": []}))

    if outcome.get("error") and not outcome.get("ticket_id"):
        st.error(outcome["error"])
        return

    row = ticket_store.get_ticket(outcome["ticket_id"])
    if not row:
        st.error("The ticket could not be found in the log file.")
        return
    escalated = row["status"] == "Escalated"
    css = "escalated" if escalated else "resolved"

    st.markdown("##### Reply to the customer")
    reply = row["human_reply"] if row.get("human_review") == "Approved" and row.get("human_reply") else row["response"]
    reason = f"<br><span class='small-note'>Reason: {esc(row['escalation_reason'])}</span>" if escalated else ""
    st.markdown(
        f"<div class='reply-box {css}'><span class='badge {css}'>{row['status'].upper()}</span>"
        f"<b>{esc(row['ticket_id'])}</b>{reason}<hr style='margin:.6rem 0;opacity:.3'>{esc(reply)}</div>",
        unsafe_allow_html=True,
    )
    chips = [f"Category: {row['category']}", f"Urgency: {row['urgency']}", f"Sentiment: {row['sentiment']}",
             f"Confidence: {row['confidence']}", f"Sources: {row['kb_sources'] or 'none'}"]
    st.markdown("".join(f"<span class='chip'>{esc(c)}</span>" for c in chips), unsafe_allow_html=True)

    if escalated:
        render_human_review(row)


def render_human_review(row):
    """Human-in-the-loop: a support person approves (or edits) the reply for an escalated ticket."""
    st.markdown("##### 👤 Human support review")
    if row["human_review"] == "Approved":
        st.success("Approved by the support team. The reply above is the approved version.")
        return
    st.caption("This ticket needs a human. Edit the reply if needed, then approve it.")
    edited = st.text_area("Reply to send", value=row["response"], key=f"review_{row['ticket_id']}", height=140)
    if st.button("✅ Approve reply (mark as sent)", key=f"approve_{row['ticket_id']}"):
        ticket_store.update_ticket(row["ticket_id"], human_review="Approved", human_reply=(edited or "").strip())
        st.rerun()


def render_kpis(rows):
    total = len(rows)
    resolved = sum(1 for r in rows if r["status"] == "Resolved")
    escalated = sum(1 for r in rows if r["status"] == "Escalated")
    pending = sum(1 for r in rows if r["human_review"] == "Pending")
    scores = {"Low": 1, "Medium": 2, "High": 3}
    levels = [scores[r["urgency"]] for r in rows if r["urgency"] in scores]
    avg = sum(levels) / len(levels) if levels else 0
    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, "Total tickets", str(total), "all complaints so far", "flat")
    kpi(c2, "Resolved by AI", str(resolved), f"{resolved * 100 // total}% of tickets" if total else "no tickets yet", "up")
    kpi(c3, "Escalated to a human", str(escalated), f"{pending} waiting for review" if escalated else "none", "down" if pending else "flat")
    kpi(c4, "Average urgency", f"{avg:.1f} / 3" if total else "-", "1 = low, 3 = high", "flat")


def render_charts(df):
    left, right = st.columns(2)
    with left:
        with st.container(key="card_chart_category"):
            card_header("Tickets per category", "What customers write about")
            st.altair_chart(count_chart(df["category"].value_counts()), width="stretch")
    with right:
        with st.container(key="card_chart_status"):
            card_header("Resolved vs escalated", "How much the AI handled alone")
            st.altair_chart(count_chart(df["status"].value_counts(), {"Resolved": "#1F9D55", "Escalated": RED}), width="stretch")


def render_log(rows):
    with st.container(key="card_log"):
        card_header("Ticket Log", "Every complaint is saved to logs/tickets.csv")
        if not rows:
            st.caption("No tickets yet. Submit a complaint above.")
            return
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.download_button(
            "⬇️ Download tickets.csv",
            data=config.LOG_PATH.read_bytes(),
            file_name="tickets.csv",
            mime="text/csv",
        )


# ------------------------------------------------------------------ page
def load_example():
    choice = st.session_state.get("example_choice")
    example = next((e for e in EXAMPLES if e["label"] == choice), None)
    if example:
        st.session_state["complaint"] = example["text"]
        st.session_state["customer"] = example["customer"]
        st.session_state["order_id"] = example["order_id"]

def require_access_code():
    code = os.getenv("APP_ACCESS_CODE", "").strip()
    if not code or st.session_state.get("unlocked"):
        return
    st.markdown(f"### 🎧 {config.COMPANY_NAME} Support Desk")
    st.caption("This demo is private. Enter the access code to continue.")
    entered = st.text_input("Access code", type="password", key="access_code_input")
    if entered and entered == code:
        st.session_state["unlocked"] = True
        st.rerun()
    if entered:
        st.error("Wrong access code.")
    st.stop()


require_access_code()

with st.sidebar:
    st.markdown(f"<div class='side-brand'>🎧 {config.COMPANY_NAME} <span>Support Desk</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='side-label'>Agent pipeline</div>", unsafe_allow_html=True)
    for name, (number, icon, title, subtitle) in AGENTS.items():
        st.markdown(
            f"<div class='agent-row'><div class='agent-num'>{number}</div>"
            f"<div><div class='agent-title'>{icon} {title}</div><div class='agent-sub'>{subtitle}</div></div></div>",
            unsafe_allow_html=True,
        )
    st.markdown("<div class='side-label'>Rules enforced by code</div>", unsafe_allow_html=True)
    for rule in ["Personal data is masked", "Hidden instructions are ignored", "Replies use only document facts", "Hard cases go to a human"]:
        st.markdown(f"<div class='rule'>{rule}</div>", unsafe_allow_html=True)
    st.markdown("<div class='side-label'>System</div>", unsafe_allow_html=True)
    has_key = bool(os.getenv("OPENAI_API_KEY", "").strip())
    st.markdown(
        f"<span class='status-chip{'' if has_key else ' bad'}'>{'API key found' if has_key else 'API key missing'}</span>"
        f"<span class='status-chip'>{config.MODEL}</span>",
        unsafe_allow_html=True,
    )
    with st.expander("Knowledge base files"):
        for path in sorted(config.KB_DIR.glob("*.md")):
            st.write(f"📄 {path.name}")

rows = ticket_store.all_tickets()

st.markdown(
    f"""<div class='hero'>
<span class='pill'><i></i>Live · multi-agent support</span>
<h1>{config.COMPANY_NAME} AI Customer Support Desk</h1>
<p>Type a customer complaint. Four AutoGen agents find the answer in the company documents, write a reply,
log the ticket and hand the hard cases to a human.</p>
<div class='flow'>Query → Knowledge → Resolution → Log</div>
</div>""",
    unsafe_allow_html=True,
)
render_kpis(rows)
st.write("")

with st.container(key="card_form"):
    card_header("New complaint", "Fields marked * are required. The sample list is only a shortcut for testing.")
    st.selectbox(
        "Quick start: load a sample complaint (optional)",
        ["(write my own)"] + [e["label"] for e in EXAMPLES],
        key="example_choice",
        on_change=load_example,
    )
    st.text_area("Customer complaint *", key="complaint", height=110, placeholder="e.g. My order is 10 days late and nobody replies to my emails.")
    col_a, col_b = st.columns(2)
    col_a.text_input("Customer name (optional)", key="customer")
    col_b.text_input("Order ID (optional)", key="order_id", placeholder="ORD-4512")
    submitted = st.button("Submit complaint", type="primary")

if submitted:
    text = st.session_state.get("complaint", "").strip()
    name = st.session_state.get("customer", "")
    order = st.session_state.get("order_id", "")
    if not text:
        st.warning("Please type a complaint first.")
    elif len(text.split()) < 4:
        st.warning("Please describe the problem in a little more detail (at least 4 words).")
    elif signature(text, name, order) == st.session_state.get("last_sig"):
        st.info("This complaint was already submitted. Edit it, or change the name or order ID, to submit again.")
    else:
        process(text, name, order)

if "outcome" in st.session_state:
    with st.container(key="card_result"):
        render_result(st.session_state["outcome"])

if rows:
    render_charts(pd.DataFrame(rows))
render_log(rows)