import asyncio
from pathlib import Path
from djclaude.agent import run_agent
from djclaude.config import MODEL_LEAD, make_client
from djclaude.prompts import SYSTEM_PROMPT
from djclaude.tools import TOOLS, execute_tool


async def local_exec(name, args):
    return execute_tool(name, args)


async def main():
    client = make_client()
    result = await run_agent(
        client, model=MODEL_LEAD, system=SYSTEM_PROMPT, tools=TOOLS, execute_tool=local_exec,
        user_message="Crie algo para um dia de chuva.", # Crie algo para um dia de chuva.
        trace_path=Path("traces/step04.jsonl"),
    )
    print(result.text)
    print(result.stop_reason, "| iterações:", result.iterations,
          "| tokens in/out:", result.input_tokens, result.output_tokens)

asyncio.run(main())