# Usage & Features (Web UI)

Run with `.venv/bin/streamlit run src/app.py`, then open
`http://localhost:8501`.

## Asking questions

Type a question in the input bar at the bottom, or click one of the
quick-start suggestions shown when a conversation is empty:

- "What is the current year sales?"
- "List the top 10 customers by revenue."
- "Which vendors have the highest outstanding balance?"
- "What tables and measures are available in this model?"

The agent always discovers the real schema first, then writes and runs
DAX, then answers in plain language.

## Reading a reply

Under each answer:

- A small **analysis note** (e.g. *"Ran 1 DAX query against Dim Customers
  — 3 rows returned"*) summarizing what was queried.
- One **"🔎 DAX query N"** expander per query the agent ran, containing:
  - The exact DAX text
  - For a **single-row result**: value(s) as metric tiles
  - For a **multi-row result**: an auto-generated chart (bar/grouped
    bar/line depending on the data shape) plus the full result as a table
  - Any query error, shown inline

## Sign-in

The top-right corner shows your Fabric/Power BI auth status:

- **Log in** — not yet signed in; click to trigger the interactive browser
  sign-in (also happens automatically on your first question if you skip
  this).
- **👤 &lt;name/email&gt;** — signed in; click to open a small popover with
  a **Sign out** button. Signing out clears the cached credential so the
  next sign-in starts fresh (same or a different account).

## Conversations

- **➕ New chat** (sidebar) starts a fresh, separate conversation — it does
  not erase your other conversations.
- **Recent** (sidebar) lists every conversation that has at least one
  message, titled from its first question. Click one to switch back into
  it — both the visible messages and the agent's own conversation memory
  for that thread are restored.
- **⬇️ Export chat** downloads the *current* conversation as a Markdown
  file, including every DAX query/result/error, timestamped in the
  filename.

## Model & connection info

The active OpenAI model is set via `OPENAI_MODEL` in `.env` (see
[SETUP.md](./SETUP.md)); there's no in-UI model switcher by design — change
it in `.env` and restart the app.
