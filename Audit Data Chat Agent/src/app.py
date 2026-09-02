"""Streamlit chat UI for the Audit Chat Agent (Fabric semantic model agent)."""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from agent import FabricAgent
from fabric_client import FabricSemanticModelClient
from viz import build_chart, render_single_row_metrics

load_dotenv()

ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
icon = Image.open(ICON_PATH)
with open(ICON_PATH, "rb") as f:
    ICON_B64 = base64.b64encode(f.read()).decode()

st.set_page_config(page_title="Audit Chat Agent", page_icon=icon, layout="wide")

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1.5rem; padding-left: 2.5rem; padding-right: 2.5rem; max-width: 100%;}

    /* Slim top bar */
    .topbar {display:flex; align-items:center; justify-content:space-between;
              padding-bottom: 0.9rem; margin-bottom: 1.2rem; border-bottom: 1px solid #E8E8E8;}
    .topbar-brand {display:flex; align-items:center; gap: 0.55rem;}
    .topbar-brand img {width: 26px; height: 26px;}
    .topbar-brand span {font-weight: 700; font-size: 1.05rem; color: #1A1A1A;}

    /* Centered hero (empty state) */
    .hero {text-align:center; margin: 2.4rem 0 1.8rem;}
    .hero-badge {width:64px; height:64px; border-radius:50%; background:#E3F2FD;
                 display:flex; align-items:center; justify-content:center; margin: 0 auto 1rem;}
    .hero-badge img {width: 34px; height: 34px;}
    .hero h2 {font-weight: 700; font-size: 1.6rem; margin: 0 0 0.5rem; color: #1A1A1A;}
    .hero p {color: #6B7280; font-size: 0.95rem; max-width: 480px; margin: 0 auto; line-height: 1.5;}

    /* Sidebar: neutral "New chat" pill + subtle export link */
    section[data-testid="stSidebar"] .stButton>button {
        background-color: #FFFFFF;
        color: #1A1A1A;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        font-weight: 500;
        justify-content: flex-start;
        padding-left: 1rem;
        transition: background-color 0.15s ease, border-color 0.15s ease;
    }
    section[data-testid="stSidebar"] .stButton>button:hover {
        background-color: #F5F9FF;
        border-color: #1E88E5;
        color: #1E88E5;
    }
    section[data-testid="stSidebar"] .stDownloadButton>button {
        background-color: transparent;
        color: #6B7280;
        border: none;
        font-weight: 500;
        font-size: 0.88rem;
        justify-content: flex-start;
        padding-left: 0.3rem;
    }
    section[data-testid="stSidebar"] .stDownloadButton>button:hover {
        color: #1E88E5;
        text-decoration: underline;
    }

    /* Quick-start suggestion pills: single column, left-aligned */
    .st-key-quick_start {max-width: 480px; margin: 0 auto;}
    .st-key-quick_start .stButton>button {
        background-color: #FFFFFF;
        color: #374151;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        font-weight: 400;
        font-size: 0.85rem;
        justify-content: flex-start;
        text-align: left;
        padding: 0.75rem 1.1rem;
        transition: background-color 0.15s ease, border-color 0.15s ease;
    }
    .st-key-quick_start .stButton>button:hover {
        background-color: #F5F9FF;
        border-color: #1E88E5;
    }

    /* Sign-in / account chip */
    .st-key-signin_button button,
    .st-key-signout_button button,
    [data-testid="stPopover"] button {
        background-color: transparent;
        color: #1E88E5;
        border: 1px solid #1E88E5;
        font-weight: 600;
        white-space: nowrap;
        transition: background-color 0.15s ease, color 0.15s ease;
    }
    [data-testid="stPopover"] button {
        width: auto !important;
    }
    .st-key-signin_button button:hover,
    .st-key-signout_button button:hover,
    [data-testid="stPopover"] button:hover {
        background-color: #1E88E5;
        color: #FFFFFF;
        border-color: #1E88E5;
    }

    /* Sidebar brand header */
    .sidebar-brand {display:flex; align-items:center; gap:0.5rem; padding: 0.2rem 0 1rem;}
    .sidebar-brand img {width: 22px; height: 22px;}
    .sidebar-brand span {font-weight: 700; font-size: 1rem; color: #1A1A1A;}

    /* Recent conversations list */
    .recent-label {color: #9CA3AF; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.04em;
                    text-transform: uppercase; margin: 1.1rem 0 0.3rem 0.3rem;}
    .st-key-recent_list .stButton>button {
        background-color: transparent;
        color: #374151;
        border: none;
        font-weight: 400;
        font-size: 0.9rem;
        justify-content: flex-start;
        padding: 0.35rem 0.3rem;
    }
    .st-key-recent_list .stButton>button:hover {
        background-color: #F0F2F5;
        color: #1A1A1A;
    }

    /* Chat input: white rounded-rectangle + blue rounded-square send button */
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] [data-baseweb="textarea"],
    [data-testid="stChatInput"] [data-baseweb="base-input"] {
        background-color: #FFFFFF !important;
        border-color: #E0E0E0 !important;
    }
    [data-testid="stChatInput"] {
        border: 1px solid #E0E0E0 !important;
        border-radius: 14px !important;
        max-width: 900px;
        margin: 0 auto;
    }
    [data-testid="stChatInputSubmitButton"] {
        background-color: #1E88E5 !important;
        border-radius: 10px !important;
    }
    [data-testid="stChatInputSubmitButton"] svg {
        fill: #FFFFFF !important;
    }
    [data-testid="stChatInputSubmitButton"]:disabled {
        background-color: #E0E0E0 !important;
    }
    [data-testid="stChatInputSubmitButton"]:disabled svg {
        fill: #9CA3AF !important;
    }
    [data-testid="stBottom"] {
        border-top: 1px solid #E8E8E8;
        background-color: #FFFFFF;
    }

    /* Reply card footer: Export + Show/Hide query */
    .card-footer-divider {border-top: 1px solid #EEF0F2; margin: 0.6rem 0 0.5rem;}
    [data-testid="stChatMessage"] .stButton>button,
    [data-testid="stChatMessage"] .stDownloadButton>button {
        background-color: transparent;
        color: #6B7280;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        font-weight: 500;
        font-size: 1rem;
        padding-top: 0.35rem;
        padding-bottom: 0.35rem;
        transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
    }
    [data-testid="stChatMessage"] .stButton>button:hover,
    [data-testid="stChatMessage"] .stDownloadButton>button:hover {
        background-color: #F5F9FF;
        border-color: #1E88E5;
        color: #1E88E5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

REQUIRED_ENV_VARS = ("FABRIC_WORKSPACE_ID", "FABRIC_DATASET_ID", "OPENAI_API_KEY")
missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
if missing:
    st.error(f"Missing environment variables: {', '.join(missing)}. Fill in .env and restart.")
    st.stop()


@st.cache_resource
def get_agent() -> FabricAgent:
    fabric_client = FabricSemanticModelClient(
        os.environ["FABRIC_WORKSPACE_ID"], os.environ["FABRIC_DATASET_ID"]
    )
    return FabricAgent(fabric_client, os.environ["OPENAI_API_KEY"])


agent = get_agent()

brand_col, _spacer_col, signin_col = st.columns([3, 7, 3], vertical_alignment="center")
with brand_col:
    st.markdown(
        f"""<div class="topbar-brand"><img src="data:image/png;base64,{ICON_B64}"/><span>Audit Chat Agent</span></div>""",
        unsafe_allow_html=True,
    )
with signin_col:
    if agent.fabric_client.is_signed_in:
        user = agent.fabric_client.signed_in_user or "Signed in"
        with st.popover(f"👤 {user}", use_container_width=False):
            st.caption(f"Signed in as **{user}**")
            if st.button("Sign out", use_container_width=True, key="signout_button"):
                agent.fabric_client.sign_out()
                st.rerun()
    else:
        if st.button("Log in", use_container_width=True, key="signin_button"):
            with st.spinner("Waiting for sign-in in your browser..."):
                try:
                    agent.fabric_client.sign_in()
                except Exception as e:
                    st.error(f"Sign-in failed: {e}")
                else:
                    st.rerun()
st.markdown('<div style="border-bottom:1px solid #E8E8E8; margin-bottom:1.2rem;"></div>', unsafe_allow_html=True)

if "conversations" not in st.session_state:
    first_id = str(uuid.uuid4())
    st.session_state.conversations = {first_id: {"title": None, "history": [], "agent_items": []}}
    st.session_state.current_conv_id = first_id


def get_current_conv() -> dict:
    return st.session_state.conversations[st.session_state.current_conv_id]


def switch_conversation(conv_id: str) -> None:
    st.session_state.current_conv_id = conv_id
    agent.input_items = list(st.session_state.conversations[conv_id]["agent_items"])
    agent.last_dax_queries = []


TABLE_REF_RE = re.compile(r"'([^']+)'\s*\[|\b([A-Z][A-Za-z0-9_ ]*?)\s*\[")


def build_analysis_note(dax_calls: list[dict]) -> str | None:
    """Summarizes the DAX calls behind a reply into a short human-readable note."""
    if not dax_calls:
        return None

    tables: set[str] = set()
    total_rows = 0
    errors = 0
    for call in dax_calls:
        for match in TABLE_REF_RE.finditer(call["query"]):
            name = (match.group(1) or match.group(2) or "").strip()
            if name:
                tables.add(name)
        if call["error"]:
            errors += 1
        else:
            try:
                total_rows += len(json.loads(call["result"]))
            except (TypeError, ValueError):
                pass

    n = len(dax_calls)
    note = f"Ran {n} DAX quer{'y' if n == 1 else 'ies'}"
    if tables:
        shown = sorted(tables)[:5]
        note += " against " + ", ".join(shown) + (" and more" if len(tables) > 5 else "")
    note += f" — {total_rows} row{'s' if total_rows != 1 else ''} returned"
    if errors:
        note += f" ({errors} error{'s' if errors != 1 else ''} encountered)"
    return note


def render_dax_results(dax_calls: list[dict], key_prefix: str) -> None:
    """Renders each DAX call's outcome (metrics/chart/table/error) — always visible."""
    for i, call in enumerate(dax_calls, start=1):
        if call["error"]:
            st.error(call["error"])
            continue

        rows = json.loads(call["result"])
        if not rows:
            st.info("No rows returned.")
            continue

        if len(rows) == 1:
            metrics, context = render_single_row_metrics(rows[0])
            if metrics:
                for col, (label, value) in zip(st.columns(len(metrics)), metrics):
                    col.metric(label, value)
            if context:
                st.dataframe(
                    pd.DataFrame([context]),
                    use_container_width=True,
                    hide_index=True,
                    key=f"{key_prefix}_ctx_{i}",
                )
        else:
            fig = build_chart(rows)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True, theme=None, key=f"{key_prefix}_chart_{i}")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, key=f"{key_prefix}_df_{i}")


def render_dax_queries(dax_calls: list[dict]) -> None:
    """Renders just the DAX query text — st.code ships its own copy-to-clipboard icon."""
    for i, call in enumerate(dax_calls, start=1):
        if len(dax_calls) > 1:
            st.caption(f"DAX query {i}")
        st.code(call["query"], language="sql")


def build_card_export(question: str, msg: dict) -> str:
    lines = ["# Audit Chat Agent - Q&A Export", f"_Exported {datetime.now().isoformat(timespec='seconds')}_", ""]
    lines.append(f"**You**: {question}")
    lines.append(f"**Agent**: {msg['content']}")
    for i, call in enumerate(msg.get("dax", []), start=1):
        lines.append(f"\n<details><summary>DAX query {i}</summary>\n")
        lines.append(f"```dax\n{call['query']}\n```")
        if call["error"]:
            lines.append(f"\nError: {call['error']}")
        else:
            lines.append(f"\nResult:\n```json\n{call['result']}\n```")
        lines.append("</details>")
    return "\n".join(lines)


def build_export(history: list[dict]) -> str:
    lines = ["# Audit Chat Agent - Chat Export", f"_Exported {datetime.now().isoformat(timespec='seconds')}_", ""]
    if not history:
        lines.append("_No messages yet._")
    for msg in history:
        speaker = "**You**" if msg["role"] == "user" else "**Agent**"
        lines.append(f"{speaker}: {msg['content']}")
        for i, call in enumerate(msg.get("dax", []), start=1):
            lines.append(f"\n<details><summary>DAX query {i}</summary>\n")
            lines.append(f"```dax\n{call['query']}\n```")
            if call["error"]:
                lines.append(f"\nError: {call['error']}")
            else:
                lines.append(f"\nResult:\n```json\n{call['result']}\n```")
            lines.append("</details>")
        lines.append("")
    return "\n".join(lines)


def run_turn(question: str) -> None:
    conv = get_current_conv()
    conv["history"].append({"role": "user", "content": question})
    if conv["title"] is None:
        conv["title"] = question
    with st.spinner("Analyzing your semantic model..."):
        answer = agent.ask(question)
        dax_calls = agent.last_dax_queries
    conv["history"].append({"role": "assistant", "content": answer, "dax": dax_calls})
    conv["agent_items"] = agent.input_items


with st.sidebar:
    st.markdown(
        f"""<div class="sidebar-brand"><img src="data:image/png;base64,{ICON_B64}"/><span>Audit Chat Agent</span></div>""",
        unsafe_allow_html=True,
    )
    if st.button("➕  New chat", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.conversations[new_id] = {"title": None, "history": [], "agent_items": []}
        st.session_state.current_conv_id = new_id
        agent.reset()
        st.rerun()

    st.download_button(
        "⬇️  Export chat",
        data=build_export(get_current_conv()["history"]),
        file_name=f"audit_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        use_container_width=True,
    )

    saved_conversations = [
        (conv_id, conv) for conv_id, conv in st.session_state.conversations.items() if conv["history"]
    ]
    if saved_conversations:
        st.markdown('<div class="recent-label">Recent</div>', unsafe_allow_html=True)
        with st.container(key="recent_list"):
            for conv_id, conv in reversed(saved_conversations):
                title = conv["title"] or "Untitled chat"
                label = title[:30] + ("…" if len(title) > 30 else "")
                prefix = "💬 " if conv_id != st.session_state.current_conv_id else "🔵 "
                if st.button(prefix + label, use_container_width=True, key=f"conv_{conv_id}"):
                    switch_conversation(conv_id)
                    st.rerun()

EXAMPLE_QUESTIONS = [
    "What is the current year sales?",
    "List the top 10 customers by revenue.",
    "Which vendors have the highest outstanding balance?",
    "What tables and measures are available in this model?",
]

current_history = get_current_conv()["history"]

_left_pad, content_col, _right_pad = st.columns([1, 6, 1])
with content_col:
    if not current_history:
        st.markdown(
            f"""<div class="hero">
            <div class="hero-badge"><img src="data:image/png;base64,{ICON_B64}"/></div>
            <h2>Audit Chat Agent</h2>
            <p>Ask questions about your Fabric semantic model in plain language.
            I&rsquo;ll write the DAX and return the results.</p>
            </div>""",
            unsafe_allow_html=True,
        )
        with st.container(key="quick_start"):
            for i, q in enumerate(EXAMPLE_QUESTIONS):
                if st.button(q, use_container_width=True, key=f"example_{i}"):
                    run_turn(q)
                    st.rerun()

    for msg_idx, msg in enumerate(current_history):
        avatar = ICON_PATH if msg["role"] == "assistant" else "🧑"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("dax"):
                key_prefix = f"{st.session_state.current_conv_id}_msg{msg_idx}"
                note = build_analysis_note(msg["dax"])
                if note:
                    st.caption(f"📝 {note}")
                render_dax_results(msg["dax"], key_prefix)

                toggle_key = f"{key_prefix}_show_dax"
                if toggle_key not in st.session_state:
                    st.session_state[toggle_key] = False

                st.markdown('<div class="card-footer-divider"></div>', unsafe_allow_html=True)
                with st.container(key=f"{key_prefix}_footer"):
                    export_col, toggle_col = st.columns(2)
                    with export_col:
                        question_text = current_history[msg_idx - 1]["content"] if msg_idx > 0 else ""
                        st.download_button(
                            "⬇️ Export",
                            data=build_card_export(question_text, msg),
                            file_name=f"audit_qa_{msg_idx}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown",
                            use_container_width=True,
                            key=f"{key_prefix}_export",
                        )
                    with toggle_col:
                        toggle_label = "🔼 Hide query" if st.session_state[toggle_key] else "🔎 Show query"
                        if st.button(toggle_label, use_container_width=True, key=f"{key_prefix}_toggle"):
                            st.session_state[toggle_key] = not st.session_state[toggle_key]
                            st.rerun()

                if st.session_state[toggle_key]:
                    render_dax_queries(msg["dax"])

question = st.chat_input("Ask about your Fabric semantic model...")
if question:
    run_turn(question)
    st.rerun()
