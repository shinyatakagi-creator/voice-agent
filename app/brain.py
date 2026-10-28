import json
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
TICKETS = json.loads((Path(__file__).parent.parent / "data" / "tickets.json").read_text())


def get_ticket_status(ticket_id: str) -> dict:
    ticket = TICKETS.get(str(ticket_id).strip())
    if ticket is None:
        return {"found": False, "ticket_id": ticket_id}
    return {"found": True, "ticket_id": ticket_id, **ticket}


ws_id = os.getenv("ANTHROPIC_WORKSPACE_ID")
client = Anthropic(default_headers={"anthropic-workspace-id": ws_id} if ws_id else None)

SYSTEM = (
    "You are a phone support agent for Acme Cloud Backup, a made-up product. "
    "Reply in one or two short spoken sentences. No lists, no markdown, no emojis. "
    "If the caller gives a ticket number, use the get_ticket_status tool. "
    "If the ticket is not found, say so and ask them to repeat the number. "
    "For how-to questions, give a short practical answer."
)

TOOLS = [
    {
        "name": "get_ticket_status",
        "description": "Look up the status of a support ticket by its number.",
        "input_schema": {
            "type": "object",
            "properties": {"ticket_id": {"type": "string", "description": "Ticket number, digits only"}},
            "required": ["ticket_id"],
        },
    }
]


def answer(text: str) -> str:
    messages = [{"role": "user", "content": text}]
    for _ in range(3):  # safety limit so a bad loop can't run forever
        resp = client.messages.create(
            model=MODEL, max_tokens=300, system=SYSTEM, tools=TOOLS, messages=messages
        )
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text").strip()

        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                out = get_ticket_status(**block.input)
                results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(out)}
                )
        messages.append({"role": "user", "content": results})
    return "Sorry, I had trouble with that. Could you say it again?"


if __name__ == "__main__":
    import sys
    print(answer(" ".join(sys.argv[1:])))
