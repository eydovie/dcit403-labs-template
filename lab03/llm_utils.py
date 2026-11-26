import asyncio
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import litellm
from litellm import completion, acompletion

litellm.suppress_debug_info = True
load_dotenv()

MODEL = os.getenv("LLM_MODEL")
EVIDENCE = Path(__file__).parent / "evidence"
EVIDENCE.mkdir(exist_ok=True)
ERROR_LOG = EVIDENCE / "api_errors.log"   # errors go here, not on screen


def log_error(msg):
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n---\n")


def _kwargs(messages, tools, attempt):
    kw = dict(model=MODEL, messages=messages, max_tokens=1000,
              temperature=0 if attempt == 0 else 0.3)  # vary on retry
    if tools:
        kw["tools"] = tools
    return kw


def ask(messages, tools=None, tries=3):
    """Sync model call. Returns the response, or None if every try failed."""
    for attempt in range(tries):
        try:
            return completion(**_kwargs(messages, tools, attempt))
        except Exception as e:
            s = str(e)
            log_error(s[:1500])
            time.sleep(15 if ("rate_limit" in s or "RateLimit" in s) else 1)
    return None


async def aask(messages, tools=None, tries=3):
    """Async model call, for use inside the MCP client."""
    for attempt in range(tries):
        try:
            return await acompletion(**_kwargs(messages, tools, attempt))
        except Exception as e:
            s = str(e)
            log_error(s[:1500])
            await asyncio.sleep(15 if ("rate_limit" in s or "RateLimit" in s) else 1)
    return None


def assistant_message(msg):
    """Clean assistant message to send back (safer than msg.model_dump())."""
    d = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        d["tool_calls"] = [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name,
                          "arguments": tc.function.arguments}}
            for tc in msg.tool_calls]
    return d
