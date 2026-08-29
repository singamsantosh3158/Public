# Setup

## 1. Prerequisites

- Python 3.9+
- An OpenAI API key
- A Microsoft Fabric / Power BI workspace ID and dataset (semantic model) ID
- Your Fabric/Power BI account needs at least **read** access to that workspace and dataset

## 2. Install

```bash
cd GenAI
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Key dependencies (see `requirements.txt`):

| Package | Used for |
|---|---|
| `openai` | The agent's LLM calls (Responses API, tool calling) |
| `azure-identity` | Interactive browser sign-in to Power BI |
| `requests` | Calling the Power BI `executeQueries` REST API |
| `streamlit` | The web chat UI |
| `plotly` / `pandas` | Charting DAX query results in the web UI |
| `python-dotenv` | Loading `.env` |

## 3. Configure `.env`

```bash
cp .env.example .env
```

Fill in:

```ini
FABRIC_WORKSPACE_ID=<your Fabric/Power BI workspace ID>
FABRIC_DATASET_ID=<your semantic model / dataset ID>
OPENAI_API_KEY=<your OpenAI API key>

# Optional — defaults to gpt-5.6-terra
OPENAI_MODEL=

# Optional — only needed if your tenant restricts interactive login to a
# specific Azure AD app registration instead of the default public client
AZURE_CLIENT_ID=
AZURE_TENANT_ID=
```

`.env` is git-ignored — never commit it.

### Choosing a model

`OPENAI_MODEL` can be set to any OpenAI model that supports the Responses
API with function tools. The default (`gpt-5.6-terra`) is chosen as a
balance of cost and quality for DAX generation and multi-step tool use; the
flagship (`gpt-5.6-sol`) trades cost for higher quality, and the budget tier
(`gpt-5.6-luna`) trades quality for speed/cost on simpler questions.

## 4. Run

### Command-line

```bash
.venv/bin/python src/main.py
```

The first question triggers an interactive browser sign-in to Power BI.
Type questions at the `>` prompt; type `exit` or `quit` to leave.

### Web UI (Streamlit)

```bash
.venv/bin/streamlit run src/app.py
```

Opens at `http://localhost:8501`. See [USAGE.md](./USAGE.md) for what the
UI offers beyond the CLI (multi-conversation history, charts, sign-in
status, chat export).

## Troubleshooting

- **"Missing environment variables"** — copy `.env.example` to `.env` and
  fill in the three required values (`FABRIC_WORKSPACE_ID`,
  `FABRIC_DATASET_ID`, `OPENAI_API_KEY`).
- **`INFO.VIEW.*` DAX errors on `get_schema`** — these functions require a
  reasonably recent semantic model (Fabric / Power BI Premium-backed). If
  unsupported, swap `get_schema` in `src/agent.py` for a call to the Fabric
  "Get Tables" REST API or a manual schema description.
- **Sign-in browser window doesn't appear** — check `AZURE_CLIENT_ID` /
  `AZURE_TENANT_ID` if your tenant restricts interactive login; otherwise
  the default public client ID should work without any Azure AD app
  registration.
- **No row limits** — the agent has no built-in query result caching or row
  limits. For very large tables, steer it (via your question or by editing
  the system prompt in `src/agent.py`) toward `TOPN`/`SUMMARIZECOLUMNS`
  rather than dumping full tables.
