from pathlib import Path

from agents import Runner, SQLiteSession
from dotenv import load_dotenv

from .agent_defs import triage_agent

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DB_PATH = ROOT / "data" / "sessions.db"


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    session_id = input("Session name (reuse a name to resume that trip): ").strip() or "default"
    session = SQLiteSession(session_id, db_path=str(DB_PATH))

    print("\nTravel Assistant ready. Describe a trip, ask a logistics question, or type 'exit'.\n")

    current_agent = triage_agent
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        result = Runner.run_sync(current_agent, user_input, session=session)
        print(f"\n{result.last_agent.name}: {result.final_output}\n")
        current_agent = result.last_agent


if __name__ == "__main__":
    main()
