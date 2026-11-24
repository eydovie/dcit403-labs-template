import os
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion

load_dotenv()
MODEL = os.getenv("LLM_MODEL")
HERE = Path(__file__).parent


def build_system_prompt() -> str:
    facts = (HERE / "facts.md").read_text(encoding="utf-8")
    return f"""You are the Campus Info Bot for the Computer Science department.
You help new students find offices, opening hours and contacts.

RULES (from the performance measure):
- Answer ONLY from the FACTS below. Never invent locations, times or names.
- If the answer is not in the FACTS, say you are not sure and point the
  student to the Department Office.
- Keep replies short (1 to 3 sentences).
- Use earlier messages in the conversation to resolve words like "it" or "there".
- If the student asks for a link, URL or website that is not in the FACTS,
do not guess one. Say you don't have it.
- If the student mentions a deadline or urgency, acknowledge it and give the
most useful next step from the FACTS (for example, the office hours and 
location, or the Academic Registrar for registration problems).
- Always state clearly when a request (like registering) is something you
cannot do, and name who can

LIMITS (from the actuators):
- You can only reply with text. You cannot register students, book rooms,
  or change anything. If asked, say so and tell them who to contact.

FACTS:
{facts}
"""


def main():
    if not MODEL:
        print("LLM_MODEL is not set. Check your .env file.")
        return

    messages = [{"role": "system", "content": build_system_prompt()}]
    print("Campus Info Bot (type 'quit' to exit)")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == "quit":
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        resp = completion(model=MODEL, messages=messages, temperature=0)
        reply = resp.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print(f"Bot: {reply}")


if __name__ == "__main__":
    main()