# arquivo: exercises/step02_tool_loop.py
import anthropic
from djclaude.config import MODEL_WORKER
from djclaude.tools import TOOLS, execute_tool

client = anthropic.Anthropic()
messages = [{"role": "user", "content": "Me sugira 5 músicas de jazz relaxantes."}]

while True:
    response = client.messages.create(model=MODEL_WORKER, max_tokens=1024, tools=TOOLS, messages=messages)
    # Preserva o content INTEIRO (inclui blocos text junto com tool_use)
    messages.append({"role": "assistant", "content": response.content})
    print("stop_reason:", response.stop_reason)

    if response.stop_reason != "tool_use":
        break

    results = []
    for block in response.content:
        if block.type == "tool_use":
            print("  Claude pediu:", block.name, block.input)
            content, is_error = execute_tool(block.name, block.input)   # VOCÊ executa
            # print('TOOL CONTENT ', content)
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": content, "is_error": is_error})
    messages.append({"role": "user", "content": results})               # turno imediatamente seguinte

print("".join(b.text for b in response.content if b.type == "text"))
