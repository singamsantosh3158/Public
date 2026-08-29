# Audit Chat Agent — Documentation

A chat agent that answers natural-language questions about a Microsoft Fabric
semantic model (Power BI dataset) by writing and running DAX queries through
an OpenAI model with tool calling, exposed through both a CLI and a
Streamlit web UI.

## Contents

- [Setup](./SETUP.md) — installing dependencies, configuring `.env`, running the CLI or web UI
- [Architecture](./ARCHITECTURE.md) — how the pieces fit together, file by file
- [Usage & Features](./USAGE.md) — everything the web UI can do: multi-conversation history, charts, sign-in, export

## At a glance

```
┌─────────────┐      DAX queries       ┌──────────────────────┐
│  OpenAI      │ ───────────────────▶  │  Fabric / Power BI    │
│  (Responses  │   tool calls:         │  executeQueries REST  │
│   API)       │   get_schema,         │  API                  │
│              │ ◀─────────────────── │  (workspace + dataset) │
└─────────────┘     rows / schema      └──────────────────────┘
       ▲
       │ natural language
       ▼
┌─────────────────────────────┐
│  CLI (main.py)  or           │
│  Streamlit UI (app.py)       │
└─────────────────────────────┘
```

The agent never guesses table/column names — it always calls `get_schema`
(backed by DAX `INFO.VIEW.*` functions) before writing a query, so answers
stay grounded in the real semantic model.
