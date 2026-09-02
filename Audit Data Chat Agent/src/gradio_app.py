"""Gradio chat UI for the Audit Chat Agent (Fabric semantic model agent)."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import gradio as gr
import pandas as pd
from dotenv import load_dotenv

from agent import FabricAgent
from fabric_client import FabricSemanticModelClient
from viz import render_single_row_metrics

load_dotenv()

REQUIRED_ENV_VARS = ("FABRIC_WORKSPACE_ID", "FABRIC_DATASET_ID", "OPENAI_API_KEY")
missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
if missing:
    raise SystemExit(
        f"Missing required environment variables: {', '.join(missing)}. "
        "Copy .env.example to .env and fill in the values."
    )

fabric_client = FabricSemanticModelClient(os.environ["FABRIC_WORKSPACE_ID"], os.environ["FABRIC_DATASET_ID"])
agent = FabricAgent(fabric_client, os.environ["OPENAI_API_KEY"])


def render_dax_section(dax_calls: list[dict]) -> str:
    if not dax_calls:
        return ""

    parts = ["\n\n---"]
    for i, call in enumerate(dax_calls, start=1):
        parts.append(f"\n<details><summary>🔎 DAX query {i}</summary>\n")
        parts.append(f"\n```sql\n{call['query']}\n```\n")
        if call["error"]:
            parts.append(f"\n**Error:** {call['error']}\n")
            parts.append("</details>")
            continue

        rows = json.loads(call["result"])
        if not rows:
            parts.append("\n_No rows returned._\n")
        elif len(rows) == 1:
            metrics, context = render_single_row_metrics(rows[0])
            for label, value in metrics:
                parts.append(f"\n**{label}:** {value}  ")
            if context:
                parts.append("\n\n" + pd.DataFrame([context]).to_markdown(index=False))
        else:
            df = pd.DataFrame(rows)
            parts.append("\n\n" + df.to_markdown(index=False))
        parts.append("\n</details>")
    return "".join(parts)


def respond(message: str, history: list) -> str:
    answer = agent.ask(message)
    return answer + render_dax_section(agent.last_dax_queries)


EXAMPLES = [
    "What is the current year sales?",
    "List the top 10 customers by revenue.",
    "Which vendors have the highest outstanding balance?",
    "What tables and measures are available in this model?",
]

CUSTOM_CSS = """
.gradio-container {max-width: 900px !important; margin: 0 auto !important;}
"""

demo = gr.ChatInterface(
    fn=respond,
    type="messages",
    title="📊 Audit Chat Agent",
    description=(
        "Ask questions about your Fabric semantic model in plain language — I'll write the DAX "
        "and return the results. Your first question opens a browser window for Power BI sign-in."
    ),
    examples=EXAMPLES,
    theme=gr.themes.Soft(primary_hue="blue"),
    css=CUSTOM_CSS,
)

if __name__ == "__main__":
    demo.launch()
