# Architecture

## File map

```
src/
├── main.py          CLI entry point — simple input()/print() chat loop
├── app.py           Streamlit web UI — chat, charts, multi-conversation history, sign-in
├── agent.py         FabricAgent — the OpenAI tool-calling loop
├── fabric_client.py FabricSemanticModelClient — auth + DAX execution against Power BI
├── viz.py           Chart-building for DAX result rows (Plotly)
└── assets/icon.png  App icon (bar-chart + magnifying glass, transparent background)
```

## `fabric_client.py` — talking to Fabric

`FabricSemanticModelClient` wraps the Power BI REST API's
`executeQueries` endpoint:

```
POST /v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries
```

- **Auth**: `azure-identity`'s `InteractiveBrowserCredential`, using a
  well-known Microsoft public client ID by default (no app registration
  needed). A cached token is reused until it expires (`_get_token`).
- **`sign_in()` / `sign_out()` / `is_signed_in` / `signed_in_user`**: explicit
  auth controls used by the web UI's sign-in chip. `signed_in_user` decodes
  the JWT access token's claims client-side (no signature verification —
  display only) to show the signed-in account's name/email.
- **`execute_dax(query)`**: runs one DAX query, returns rows as
  `list[dict]`. Raises `FabricQueryError` on HTTP failure or a
  query-level error in the response body.
- **`get_tables()` / `get_columns()` / `get_measures()`**: convenience
  wrappers around `execute_dax` using DAX `INFO.VIEW.*` functions —
  this is how the agent discovers real schema instead of guessing.

For unattended/service use instead of interactive login, swap
`InteractiveBrowserCredential` for `ClientSecretCredential` (service
principal) — the rest of the client is unchanged.

## `agent.py` — the tool-calling loop

`FabricAgent` drives an OpenAI model through the **Responses API**
(`client.responses.create`), not Chat Completions — reasoning models like
the `gpt-5.6-*` family don't support function tools on
`/v1/chat/completions`, only on `/v1/responses`.

Two tools are exposed to the model:

| Tool | What it does |
|---|---|
| `get_schema` | Runs `INFO.VIEW.TABLES/COLUMNS/MEASURES`, cached after first call |
| `run_dax_query` | Executes an arbitrary `EVALUATE ...` DAX query |

The system prompt instructs the model to always call `get_schema` first,
write valid `EVALUATE`-rooted DAX, prefer existing measures over
hand-rolled aggregation, and retry on query errors rather than giving up.

**Conversation state** lives in `self.input_items` (the Responses API's
flat conversation history) and is fully exposed so callers (the web UI)
can snapshot/restore it per saved conversation — see
[`switch_conversation`](../src/app.py) in `app.py`.

**`last_dax_queries`** records every DAX call made during the *current*
`ask()` turn (query, result JSON, error) — this is what powers the app's
"DAX query" expanders, charts, and analysis-note captions. It resets at
the start of each `ask()` call.

## `viz.py` — charting DAX results

`build_chart(rows)` turns a list of result-row dicts into a Plotly figure,
or `None` if the shape doesn't chart well (fewer than 2 rows, or fewer than
2 columns). Logic:

1. Coerce columns to numeric where every value parses cleanly
   (`_coerce_numeric`); remaining columns are candidates for the
   category/dimension axis.
2. Try to coerce one of those into a datetime column (`_coerce_date`) — if
   found, it becomes the x-axis and the chart is a line (trend-over-time).
3. **One numeric column** → single-hue bar (or line, if dated) — a plain
   magnitude comparison, sequential blue.
4. **Multiple numeric columns** → grouped bar, one color per measure from
   a fixed, CVD-safe 8-hue categorical palette (never cycled/generated).

Every mark gets a data label (`texttemplate`) and a hover tooltip. Colors,
gridlines, and ink tones are pulled from a small validated palette module
rather than left to Plotly/Streamlit defaults — see the palette constants
at the top of `viz.py`.

`render_single_row_metrics(row)` instead splits a single-row result into
`st.metric`-style (label, formatted value) pairs plus any non-numeric
context fields, for a "stat tile" style answer (e.g. "What is the current
year sales?").

> **Streamlit gotcha**: `st.plotly_chart()` must be called with
> `theme=None` — Streamlit's default `theme="streamlit"` silently
> overrides a figure's own trace colors. All calls in `app.py` pass
> `theme=None` for exactly this reason.

## `app.py` — the Streamlit UI

### State model

The UI supports multiple saved conversations (like a typical chat app's
"New chat" + history sidebar), not just one running thread:

```python
st.session_state.conversations = {
    conv_id: {"title": str | None, "history": [...], "agent_items": [...]},
    ...
}
st.session_state.current_conv_id = conv_id
```

- `history` is the display-facing list of `{"role", "content", "dax"}` messages.
- `agent_items` is a snapshot of `FabricAgent.input_items` for that
  conversation — since there is only **one** `FabricAgent` instance
  (cached process-wide via `st.cache_resource`), switching conversations
  means swapping `agent.input_items` to match the selected conversation
  (`switch_conversation`).
- A conversation only appears in the sidebar's "Recent" list once it has
  at least one message — a brand-new/empty conversation stays hidden until
  you actually ask something (title is taken from the first question).

### Every `st.plotly_chart` / `st.dataframe` needs a unique `key`

Because message history is re-rendered from scratch on every rerun, two
charts with identical parameters (e.g. two DAX results with the same
shape) can collide on Streamlit's auto-generated element ID
(`StreamlitDuplicateElementId`). `render_dax_calls` takes a `key_prefix`
(conversation ID + message index) and derives a unique `key` for every
chart/dataframe from it — don't remove these keys when editing this
function.

### Layout notes

- `st.chat_input(...)` must be called at the **top level** of the script,
  not nested inside `st.columns(...)` — nesting it silently disables
  Streamlit's automatic "pin to the bottom of the viewport, span full
  width" behavior for that widget.
- The main content (hero, chat messages) is deliberately wrapped in a
  `st.columns([1, 6, 1])` split so it reads as a centered column even
  though the app runs in `layout="wide"` (full-width next to the sidebar).
- Most custom styling is scoped CSS keyed off Streamlit's own
  `data-testid` attributes (stable across versions) or `st-key-<key>`
  classes generated from a widget's `key=` (also stable) — avoid targeting
  Streamlit's auto-generated `st-emotion-cache-*` classes, which are
  unstable build hashes.

### `build_analysis_note`

A small regex (`TABLE_REF_RE`) pulls distinct DAX table references
(`'Table Name'[Col]` or `TableName[Col]`) out of the DAX queries behind a
reply, and combines that with row/error counts into a one-line caption
shown directly under each answer — e.g. *"Ran 1 DAX query against Dim
Customers, Fact SalesLines — 3 rows returned."* This is a heuristic, not a
parser — it's good enough for typical `SUMMARIZECOLUMNS`/`TOPN` queries but
won't catch every DAX table-reference syntax.
