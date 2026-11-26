import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from llm_utils import aask, assistant_message, EVIDENCE

HERE = Path(__file__).parent
TOOL_LOG = EVIDENCE / "tool_calls.jsonl"

SYSTEM_PROMPT = """You are a stock assistant for a community pharmacy in Ghana.
- Use the tools for every stock, price and expiry fact. Never guess.
- Call record_sale ONLY when the user explicitly asks to sell or record a sale.
- If a tool refuses or finds nothing, tell the user plainly and explain why.
- Keep answers short."""

params = StdioServerParameters(command=sys.executable,
                               args=[str(HERE / "server.py")], cwd=str(HERE))


def log_call(question, name, args, text, ms):
    entry = {"timestamp": datetime.now().isoformat(timespec="seconds"),
             "question": question, "tool": name, "arguments": args,
             "result_summary": text[:150], "duration_ms": round(ms, 1)}
    with open(TOOL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


async def run_question(session, schemas, question, max_steps=6):
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}]
    for _ in range(max_steps):
        await asyncio.sleep(2)
        resp = await aask(messages, schemas)
        if resp is None:
            return "Model call failed. Details in evidence/api_errors.log."
        msg = resp.choices[0].message
        if not msg.tool_calls:                      # no more tools: final answer
            return msg.content

        messages.append(assistant_message(msg))
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            start = time.perf_counter()
            try:
                # MCP does the work
                result = await session.call_tool(name, args)
                text = "\n".join(
                    c.text for c in result.content if hasattr(c, "text"))
                text = text or "[] (no results)"
            except Exception as e:
                text = f"Tool error: {e}"
            ms = (time.perf_counter() - start) * 1000

            print(f"  -> {name}({json.dumps(args)})")
            print(f"  <- {text[:120]}")
            log_call(question, name, args, text, ms)
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": text})
    return "Stopped: reached max_steps without a final answer."


async def main(question):
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # DISCOVERED, not imported
            tools = (await session.list_tools()).tools
            schemas = [{"type": "function", "function": {
                "name": t.name, "description": t.description,
                "parameters": t.inputSchema}} for t in tools]
            print(f"Discovered tools: {[t.name for t in tools]}\n")
            print(f"Question: {question}")
            answer = await run_question(session, schemas, question)
            print(f"\nAnswer: {answer}")


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Do we have amoxicillin 500mg?"
    asyncio.run(main(q))
