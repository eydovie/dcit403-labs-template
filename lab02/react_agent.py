import json
import os
import re
import time
from pathlib import Path
from dotenv import load_dotenv
import litellm
from litellm import completion
from tools import calculator, wiki_lookup

litellm.suppress_debug_info = True

load_dotenv()
MODEL = os.getenv("LLM_MODEL")
HERE = Path(__file__).parent
EVIDENCE = HERE / "evidence"
EVIDENCE.mkdir(exist_ok=True)
ERROR_LOG = EVIDENCE / "api_errors.log"   # API errors go here, not on screen

TOOLS = {"CALC": calculator, "WIKI": wiki_lookup}

SYSTEM_PROMPT = """You are a helpful assistant for traders at Makola Market.
You solve problems step by step. You have no function-calling ability.
You work ONLY by writing plain text in the format below. Never output JSON,
never use <function> tags, and never use tools provided by the API.

Available actions (use these exact names and no others):
- CALC: evaluates arithmetic. The Action Input is an expression such as 4*185 + 3*95.
- WIKI: returns a short Wikipedia summary. The Action Input is a page title such as Techiman.
- DONE: ends the task. The Action Input is your final answer to the user.

On EVERY step, reply in exactly this plain-text format and nothing else:

Thought: <your reasoning>
Action: CALC | WIKI | DONE
Action Input: <input for the action, or the final answer if the action is DONE>

RULES:
- Use CALC for ALL arithmetic. Never calculate in your head.
- Use WIKI for facts you are not certain about.
- If WIKI says no page was found, try a simpler title (for example "Ghana"
  instead of "Ghana independence"), or answer that nothing was found.
- Write only ONE Thought/Action/Action Input per reply.
- Never write an Observation yourself. It will be given to you.

EXAMPLE of one step:
Thought: I need the total cost first.
Action: CALC
Action Input: 2*50 + 3*10
"""

FORMAT_REMINDER = (
    "Format error: your reply could not be parsed. Do not call functions or "
    "output JSON. Reply in plain text with exactly:\n"
    "Thought: ...\nAction: CALC | WIKI | DONE\nAction Input: ..."
)

ACTION_RE = re.compile(r"Action:\s*(\w+)\s*\nAction Input:\s*(.*)", re.DOTALL)


def parse(text):
    m = ACTION_RE.search(text)
    if not m:
        return None, None
    return m.group(1).strip(), m.group(2).strip()


def log_error(msg):
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n---\n")


def _norm(key):
    return re.sub(r"[^a-z]", "", str(key).lower())


def salvage(err_text):
    """Recover the model's intended step from a Groq tool_use_failed error."""
    try:
        start = err_text[err_text.index("{"):]
        body, _ = json.JSONDecoder().raw_decode(start)
        gen = json.loads(body["error"]["failed_generation"])
        name = str(gen.get("name", ""))
        args = gen.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)
        a = {_norm(k): v for k, v in args.items()}
    except Exception:
        return None

    action = a.get("action")
    if not action and name.upper() in (*TOOLS, "DONE"):
        action = name
    action_input = a.get("actioninput", a.get("input"))
    if not action or action_input is None:
        return None
    thought = a.get("thought") or "(step recovered from the model's output)"
    return f"Thought: {thought}\nAction: {action}\nAction Input: {action_input}"


def call_model(messages, tries=3):
    """Call the model quietly. Returns (reply, error)."""
    last = None
    for _ in range(tries):
        try:
            r = completion(model=MODEL, messages=messages, temperature=0,
                           stop=["Observation:"], max_tokens=600)
            return (r.choices[0].message.content or "").strip(), None
        except Exception as e:
            s = str(e)
            last = e
            log_error(s[:1500])
            if "rate_limit" in s or "RateLimit" in s:
                time.sleep(15)
                continue
            if "tool_use_failed" in s:
                recovered = salvage(s)
                if recovered:
                    return recovered, None
            return "", e
    return "", last


def next_trace_number():
    return len(list(EVIDENCE.glob("trace_*.txt"))) + 1


def run_agent(question, max_steps=8):
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}]
    trace = [f"Question: {question}", ""]
    final = None

    for step in range(1, max_steps + 1):
        time.sleep(2)
        reply, err = call_model(messages)

        if err is not None:
            trace.append("[model call failed; details in api_errors.log]")
            obs = FORMAT_REMINDER
            trace.append(f"Observation: {obs}")
            trace.append("")
            messages.append({"role": "user", "content": f"Observation: {obs}"})
            continue

        trace.append(reply)
        messages.append({"role": "assistant", "content": reply})

        action, action_input = parse(reply)

        if action is None:
            obs = FORMAT_REMINDER
        elif action.upper() == "DONE":
            final = action_input
            break
        elif action.upper() not in TOOLS:
            obs = (f"Unknown action '{action}'. Valid actions are: "
                   f"{', '.join(TOOLS)}, DONE.")
        else:
            try:
                obs = TOOLS[action.upper()](action_input)
            except Exception as e:
                obs = f"Tool error: {e}"

        trace.append(f"Observation: {obs}")
        trace.append("")
        messages.append({"role": "user", "content": f"Observation: {obs}"})

    if final is None:
        final = "Stopped: reached max_steps without a final answer."

    trace.append(f"\nFINAL ANSWER: {final}")
    text = "\n".join(trace)
    print(text)
    path = EVIDENCE / f"trace_{next_trace_number()}.txt"
    path.write_text(text, encoding="utf-8")
    return final


if __name__ == "__main__":
    if not MODEL:
        raise SystemExit("LLM_MODEL is not set. Check your .env file.")

    QUESTIONS = [
        "Look up when Ghana became independent, then calculate how many years ago that was from 2026.",
    ]
    for q in QUESTIONS:
        print("=" * 60)
        run_agent(q)