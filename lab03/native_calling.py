import csv
import json
from pathlib import Path
from llm_utils import ask, assistant_message

DATA = Path(__file__).parent / "data" / "pharmacy_stock.csv"


def check_stock(item: str, strength: str = ""):
    with open(DATA, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if item.lower() in r["item"].lower()]
    if strength:
        rows = [r for r in rows if strength.lower() in r["strength"].lower()]
    return rows[:10]


TOOLS = {"check_stock": check_stock}

tool_schemas = [{
    "type": "function",
    "function": {
        "name": "check_stock",
        "description": "Look up pharmacy stock. Returns rows (item, strength, form, "
                       "quantity, unit_price_ghs, expiry_date) whose name contains the item.",
        "parameters": {
            "type": "object",
            "properties": {
                "item": {"type": "string", "description": "Medicine name, e.g. amoxicillin"},
                "strength": {"type": "string", "description": "Optional strength, e.g. 500mg"},
            },
            "required": ["item"],
        },
    },
}]

messages = [
    {"role": "system", "content": "You are a stock assistant for a community pharmacy. "
                                  "Use the tools for stock facts. Never guess."},
    {"role": "user", "content": "Do we have amoxicillin 500mg?"},
]

resp = ask(messages, tool_schemas)
if resp is None:
    raise SystemExit("Model call failed. See lab03/evidence/api_errors.log")

msg = resp.choices[0].message
print("TOOL CALLS:", msg.tool_calls)          # message 2: the model's decision

messages.append(assistant_message(msg))
for tc in msg.tool_calls or []:
    args = json.loads(tc.function.arguments)
    result = TOOLS[tc.function.name](**args)  # code runs the function
    print("RESULT:", result)                  # message 3: the percept
    messages.append({"role": "tool", "tool_call_id": tc.id,
                     "content": json.dumps(result)})

resp = ask(messages, tool_schemas)
print("ANSWER:", resp.choices[0].message.content)   # message 4