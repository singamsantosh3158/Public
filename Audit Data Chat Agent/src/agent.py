"""OpenAI agent that answers questions by querying a Fabric semantic model."""

from __future__ import annotations

import json
import os

from openai import OpenAI

from fabric_client import FabricSemanticModelClient

MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.2")

SYSTEM_PROMPT = """You are a data analyst agent answering questions about a Microsoft Fabric \
semantic model (a Power BI dataset) by writing and running DAX queries.

Rules:
- Always call get_schema first if you haven't already, so you know the real table, \
column, and measure names. Never guess names.
- Write valid DAX for the executeQueries API: queries must start with EVALUATE and \
return a table expression, e.g. `EVALUATE SUMMARIZECOLUMNS(...)` or `EVALUATE TOPN(...)`.
- The measures list from get_schema encodes the model owner's official business logic \
(currency conversion, exclusions, filters, etc.) for common calculations. Before writing \
any aggregation (sales, revenue, cost, profit, counts, totals, averages, etc.), check the \
measures list for one that already matches what's being asked. If a matching measure \
exists, you MUST reference it directly (e.g. `SUMMARIZECOLUMNS('Table'[Col], "Label", \
[MeasureName])`) instead of writing your own SUM/AVERAGE/etc. over a raw column. Only \
derive an aggregation by hand when no existing measure covers it — hand-derived \
aggregations are a common source of numbers that don't match the model's real figures.
- When a query returns more than one row, the UI already renders the full result as a \
table (and, if the user asked for a visualization, a chart) right below your answer. \
Do NOT re-list, enumerate, or restate the individual rows in your text — that just \
duplicates the table. Instead give a short overview: what the result covers and one \
notable takeaway (e.g. the top value, a range, or a pattern), in 1-2 sentences.
- When a query returns a single row/value, state that value directly in your answer \
(there is no separate table for a single number, so this is not duplication).
- The table/chart the UI shows is generated ONLY from run_dax_query calls made in your \
CURRENT reply — it cannot render anything from earlier turns, even if you already know \
the answer from conversation history. So whenever the user asks to see, view, chart, \
plot, or visualize a result — including a follow-up like "can you visualize this" \
referring to something already discussed — you MUST call run_dax_query again (the same \
query as before, or an equivalent one) in THIS reply. Never claim you've shown or \
visualized something without actually calling the tool in the current turn.
- If a query errors, read the error, fix the DAX, and retry rather than giving up.
"""

# Responses API function tools are flat (no nested "function" key, unlike Chat Completions).
TOOLS = [
    {
        "type": "function",
        "name": "get_schema",
        "description": (
            "Returns the semantic model's tables, columns, and measures via DAX INFO "
            "functions. Call this before writing any query."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "run_dax_query",
        "description": "Executes a DAX query (must start with EVALUATE) against the semantic model and returns the result rows.",
        "parameters": {
            "type": "object",
            "properties": {
                "dax_query": {"type": "string", "description": "A complete DAX query, e.g. EVALUATE TOPN(10, Sales)"},
            },
            "required": ["dax_query"],
        },
    },
]


class FabricAgent:
    def __init__(self, fabric_client: FabricSemanticModelClient, openai_api_key: str | None = None):
        self.fabric_client = fabric_client
        self.client = OpenAI(api_key=openai_api_key)
        self.input_items: list = []
        self._schema_cache: str | None = None
        self.last_dax_queries: list[dict] = []

    def reset(self) -> None:
        """Clears conversation history (keeps the cached schema)."""
        self.input_items = []
        self.last_dax_queries = []

    def _repair_dangling_calls(self) -> None:
        """Synthesizes a stub output for any function_call left unresolved by a past
        crash (e.g. a network error escaping _run_tool). The Responses API rejects any
        request whose history contains a function_call with no matching
        function_call_output, so a single unresolved call would otherwise brick the
        conversation permanently."""

        def item_type(item):
            return item.get("type") if isinstance(item, dict) else getattr(item, "type", None)

        def item_call_id(item):
            return item.get("call_id") if isinstance(item, dict) else getattr(item, "call_id", None)

        resolved = {item_call_id(i) for i in self.input_items if item_type(i) == "function_call_output"}
        stubs = [
            {
                "type": "function_call_output",
                "call_id": item_call_id(item),
                "output": "ERROR: tool execution was interrupted and never completed.",
            }
            for item in self.input_items
            if item_type(item) == "function_call" and item_call_id(item) not in resolved
        ]
        self.input_items += stubs

    def _trim_input_items(self) -> None:
        """Drops the oldest complete turns (from one user message up to the next) once
        history gets too large, always keeping at least the most recent turn — a
        long-running conversation should degrade by forgetting old context, not by
        breaking with a context-length error."""

        def item_role(item):
            return item.get("role") if isinstance(item, dict) else getattr(item, "role", None)

        def size() -> int:
            return sum(
                len(json.dumps(item.model_dump() if hasattr(item, "model_dump") else item, default=str))
                for item in self.input_items
            )

        max_chars = 300_000
        boundaries = [i for i, item in enumerate(self.input_items) if item_role(item) == "user"]
        while size() > max_chars and len(boundaries) > 1:
            self.input_items = self.input_items[boundaries[1] :]
            boundaries = [i for i, item in enumerate(self.input_items) if item_role(item) == "user"]

    def ask(self, question: str) -> str:
        self._repair_dangling_calls()
        self._trim_input_items()
        self.input_items.append({"role": "user", "content": question})
        self.last_dax_queries = []

        while True:
            response = self.client.responses.create(
                model=MODEL,
                instructions=SYSTEM_PROMPT,
                input=self.input_items,
                tools=TOOLS,
            )
            self.input_items += response.output

            function_calls = [item for item in response.output if item.type == "function_call"]
            if not function_calls:
                return response.output_text

            for call in function_calls:
                args = json.loads(call.arguments or "{}")
                result_text = self._run_tool(call.name, args)
                self.input_items.append(
                    {"type": "function_call_output", "call_id": call.call_id, "output": result_text}
                )

    def _run_tool(self, name: str, tool_input: dict) -> str:
        # Must never raise: an uncaught exception here would skip appending this
        # call's function_call_output, leaving a dangling function_call that
        # permanently breaks every future request on this conversation (see
        # _repair_dangling_calls). Always return *some* string, even on failure.
        try:
            if name == "get_schema":
                return self._get_schema()
            if name == "run_dax_query":
                dax_query = tool_input["dax_query"]
                rows = self.fabric_client.execute_dax(dax_query)
                result_text = json.dumps(rows, default=str)
                self.last_dax_queries.append({"query": dax_query, "result": result_text, "error": None})
                return result_text
            return f"Unknown tool: {name}"
        except Exception as e:
            if name == "run_dax_query":
                self.last_dax_queries.append(
                    {"query": tool_input.get("dax_query", ""), "result": None, "error": str(e)}
                )
            return f"ERROR: {e}"

    def _get_schema(self) -> str:
        if self._schema_cache is None:
            tables = self.fabric_client.get_tables()
            columns = self.fabric_client.get_columns()
            measures = self.fabric_client.get_measures()

            # Shrink oversized VALUES (long description/expression text), never drop
            # whole rows — dropping rows by position risks silently deleting an entire
            # table's columns (e.g. a customer name column) just because of where it
            # landed in the list, which is worse than a bigger payload.
            def trim_long_values(rows: list[dict], max_value_len: int) -> list[dict]:
                return [
                    {k: (v[:max_value_len] + "…" if isinstance(v, str) and len(v) > max_value_len else v) for k, v in row.items()}
                    for row in rows
                ]

            raw_columns, raw_measures = columns, measures
            max_value_len = 200
            columns = trim_long_values(raw_columns, max_value_len)
            measures = trim_long_values(raw_measures, max_value_len)
            schema: dict = {"tables": tables, "columns": columns, "measures": measures}
            text = json.dumps(schema, default=str)

            # Last-resort safety net for pathologically schema-heavy models: shrink how
            # much of each VALUE we keep, never how many rows — this can never make a
            # table's columns disappear, only make their descriptions shorter.
            max_schema_chars = 250_000
            while len(text) > max_schema_chars and max_value_len > 20:
                max_value_len //= 2
                columns = trim_long_values(raw_columns, max_value_len)
                measures = trim_long_values(raw_measures, max_value_len)
                schema["columns"], schema["measures"] = columns, measures
                text = json.dumps(schema, default=str)

            self._schema_cache = text
        return self._schema_cache
