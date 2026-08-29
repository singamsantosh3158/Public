"""CLI chat loop for the Fabric semantic model agent."""

import os
import sys

from dotenv import load_dotenv

from agent import FabricAgent
from fabric_client import FabricSemanticModelClient


def main():
    load_dotenv()

    workspace_id = os.environ.get("FABRIC_WORKSPACE_ID")
    dataset_id = os.environ.get("FABRIC_DATASET_ID")
    openai_api_key = os.environ.get("OPENAI_API_KEY")

    missing = [
        name
        for name, value in [
            ("FABRIC_WORKSPACE_ID", workspace_id),
            ("FABRIC_DATASET_ID", dataset_id),
            ("OPENAI_API_KEY", openai_api_key),
        ]
        if not value
    ]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in the values.")
        sys.exit(1)

    fabric_client = FabricSemanticModelClient(workspace_id, dataset_id)
    agent = FabricAgent(fabric_client, openai_api_key)

    print("📊 Audit Chat Agent. A browser window will open for sign-in on your first question.")
    print("Type your question, or 'exit' to quit.\n")

    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break

        answer = agent.ask(question)
        print(f"\n{answer}\n")


if __name__ == "__main__":
    main()
