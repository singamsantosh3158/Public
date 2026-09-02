# Audit Chat Agent

An agent that answers natural-language questions by querying a Microsoft
Fabric semantic model (Power BI dataset) with DAX — available as a CLI or
a Streamlit web chat UI.

📖 **Full documentation: [Documentation/](./Documentation/README.md)** — setup, architecture, and
web UI usage (multi-conversation history, charts, sign-in, chat export).

## How it works

- Auth: interactive browser sign-in (`azure-identity` `InteractiveBrowserCredential`)
  against the Power BI API scope. No app registration needed by default — it uses a
  well-known Microsoft public client ID. Override with `AZURE_CLIENT_ID` /
  `AZURE_TENANT_ID` if your tenant blocks that.
- Query path: the agent calls the Power BI REST **executeQueries** endpoint
  (`POST /v1.0/myorg/groups/{workspaceId}/datasets/{datasetId}/executeQueries`) with
  DAX, using your workspace ID + dataset ID.
- Agent loop: an OpenAI model (`gpt-5.6-terra` by default, override with `OPENAI_MODEL`) with
  two tools — `get_schema` (runs DAX `INFO.VIEW.TABLES/COLUMNS/MEASURES` to discover real
  table/column/measure names) and `run_dax_query` (executes arbitrary `EVALUATE ...`
  DAX) — via the OpenAI Python SDK's function calling.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# fill in FABRIC_WORKSPACE_ID, FABRIC_DATASET_ID, OPENAI_API_KEY
```

Your Fabric/Power BI account needs at least read access to the workspace and dataset.

## Run

CLI:

```bash
.venv/bin/python src/main.py
```

Streamlit web UI (multi-conversation history, auto-generated charts, sign-in/out, chat export):

```bash
.venv/bin/streamlit run src/app.py
```

Gradio web UI (polished chat interface out of the box, less custom styling to maintain):

```bash
.venv/bin/python src/gradio_app.py
```

React web UI (custom Vite + React + Tailwind 4 frontend, full design control — sidebar,
header, transcript, composer, and a resizable report panel for DAX/results). Requires Node.js
18+; run the backend and frontend in two terminals:

```bash
# Terminal 1 — API backend
.venv/bin/python -m uvicorn src.api_server:app --reload --port 8787 --app-dir .

# Terminal 2 — frontend dev server (proxies /api to the backend above)
cd frontend
npm install   # first time only
npm run dev
```

Open the URL Vite prints (typically `http://localhost:5173`).

The first question triggers a browser sign-in prompt. After that, ask things like:

```
> What were total sales by region last quarter?
> List the top 10 customers by revenue.
```

## Notes / next steps

- `INFO.VIEW.*` DAX functions require a reasonably recent semantic model (Fabric /
  Power BI Premium-backed). If your model doesn't support them, swap `get_schema` in
  `src/agent.py` for a call to the Fabric "Get Tables" REST API or a manual schema
  description.
- The agent has no query result caching or row limits — for very large tables, guide
  it (or the system prompt) to use `TOPN`/`SUMMARIZECOLUMNS` rather than dumping full
  tables.
- For unattended/service use instead of interactive login, swap
  `InteractiveBrowserCredential` in `src/fabric_client.py` for
  `ClientSecretCredential` (service principal) — the rest of the code is unchanged.
