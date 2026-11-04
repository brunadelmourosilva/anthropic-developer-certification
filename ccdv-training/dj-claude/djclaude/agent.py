# arquivo: djclaude/agent.py
import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable
from djclaude.errors import call_llm

ExecuteTool = Callable[[str, dict], Awaitable[tuple[str, bool]]]


@dataclass
class AgentResult:
    text: str
    stop_reason: str
    iterations: int
    input_tokens: int = 0
    output_tokens: int = 0
    messages: list = field(default_factory=list)


def text_of(content) -> str:
    return "".join(b.text for b in content if b.type == "text")


def extract_json(text: str) -> dict:
    """Pega o primeiro objeto JSON do texto (tolera cercas de markdown ao redor)."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model output.")
    return json.loads(text[start:end + 1])


def _trace(path: Path | None, event: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), **event}, ensure_ascii=False, default=str) + "\n")


async def _safe_exec(execute_tool: ExecuteTool, name: str, args: dict) -> tuple[str, bool]:
    try:
        return await execute_tool(name, args)
    except Exception as exc:  # a tool nunca pode derrubar o loop em silêncio
        return f"Tool '{name}' crashed: {exc!r}", True


async def run_agent(client, *, model, system, tools, execute_tool: ExecuteTool, user_message,
                    history=None, max_iterations=8, max_tokens=2048,
                    trace_path: Path | None = None, label="agent") -> AgentResult:
    messages = list(history or []) + [{"role": "user", "content": user_message}]
    total_in = total_out = 0

    for iteration in range(1, max_iterations + 1):
        params = dict(model=model, max_tokens=max_tokens, system=system, messages=messages)
        if tools:
            params["tools"] = tools

        started = time.perf_counter()
        response = await call_llm(client, **params)
        elapsed = time.perf_counter() - started

        total_in += response.usage.input_tokens
        total_out += response.usage.output_tokens
        _trace(trace_path, {"agent": label, "event": "llm_call", "iteration": iteration,
                            "stop_reason": response.stop_reason, "latency_s": round(elapsed, 2),
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens})

        messages.append({"role": "assistant", "content": response.content})

        # Condição de saída 1: qualquer stop_reason diferente de tool_use (end_turn, max_tokens, refusal...)
        if response.stop_reason != "tool_use":
            return AgentResult(text_of(response.content), response.stop_reason, iteration,
                               total_in, total_out, messages)

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        outputs = await asyncio.gather(*(_safe_exec(execute_tool, b.name, b.input) for b in tool_uses))

        results = []
        for block, (content, is_error) in zip(tool_uses, outputs):
            _trace(trace_path, {"agent": label, "event": "tool_call", "name": block.name,
                                "input": block.input, "is_error": is_error, "preview": content[:200]})
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": content, "is_error": is_error})
        messages.append({"role": "user", "content": results})

    # Condição de saída 2: limite de iterações — NÃO confie em Claude para parar sozinho
    return AgentResult("", "max_iterations", max_iterations, total_in, total_out, messages)