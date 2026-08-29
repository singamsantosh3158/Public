"""OpenAI agent that answers questions by querying a Fabric semantic model."""

from __future__ import annotations

import json
import os

from openai import OpenAI

from fabric_client import FabricQueryError, FabricSemanticModelClient

MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.2")

SYSTEM_PROMPT = """You are a data analyst agent answering questions about a Microsoft Fabric \
semantic model (a Power BI dataset) by writing and running DAX queries.

Rules:
- Always call get_schema first if you haven't already, so you know the real table, \
column, and measure names. Never guess names.
- Write valid DAX for the executeQueries API: queries must start with EVALUATE and \
return a table expression, e.g. `EVALUATE SUMMARIZECOLUMNS(...)` or `EVALUATE TOPN(...)`.
- Prefer existing measures over re-deriving aggregations by hand.
- After getting query results, answer the user's question directly in plain language. \
Only show the raw DAX or raw rows if the user asks for them.
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

    def ask(self, question: str) -> str:
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
        except FabricQueryError as e:
            if name == "run_dax_query":
                self.last_dax_queries.append(
                    {"query": tool_input.get("dax_query", ""), "result": None, "error": str(e)}
                )
            return f"ERROR: {e}"

    def _get_schema(self) -> str:
        if self._schema_cache is None:
            schema = {
                "tables": self.fabric_client.get_tables(),
                "columns": self.fabric_client.get_columns(),
                "measures": self.fabric_client.get_measures(),
            }
            self._schema_cache = json.dumps(schema, default=str)
        return self._schema_cache
