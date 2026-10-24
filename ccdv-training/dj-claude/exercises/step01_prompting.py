# arquivo: exercises/step01_prompting.py
import json
import anthropic
from djclaude import music_db
from djclaude.config import MODEL_WORKER

client = anthropic.Anthropic()
track = music_db.get_track("t010")
TRACK_JSON = json.dumps({k: track[k] for k in ("title", "genre", "bpm", "energy", "mood")}, ensure_ascii=False)


def ask(system, user, max_tokens=300):
    kwargs = {"system": system} if system else {}
    r = client.messages.create(model=MODEL_WORKER, max_tokens=max_tokens,
                               messages=[{"role": "user", "content": user}], **kwargs)
    
    print(f"  [stop_reason={r.stop_reason} in={r.usage.input_tokens} out={r.usage.output_tokens}]")
    
    return "".join(b.text for b in r.content if b.type == "text")


# V1 — sem técnica nenhuma
print("V1:", ask("", f"Describe this track: {TRACK_JSON}"))

# V2 — system prompt (contrato de comportamento) + XML (separa instrução de dado)
SYSTEM_V2 = "You are a music editor writing short blurbs for a playlist app. Be concrete; avoid clichés."
USER_V2 = f"Write a one-sentence blurb for the track below.\n<track>\n{TRACK_JSON}\n</track>"
print("V2:", ask(SYSTEM_V2, USER_V2))

# V3 — few-shot (mostra o formato) + output constraints (campos, tamanho, o que fazer se faltar dado)
SYSTEM_V3 = SYSTEM_V2 + """
<output_format>
Return ONLY a JSON object with keys:
- "blurb": string, max 120 characters, in Portuguese
- "vibe_tags": array of exactly 3 lowercase strings
No preamble and no markdown fences. If a value is unknown, use null instead of inventing it.
</output_format>"""
EXAMPLES = """<examples>
<example>
<track>{"title": "Rua Vazia", "genre": "lofi", "bpm": 72, "energy": 0.2, "mood": "relaxed"}</track>
<output>{"blurb": "Batida suave para estudar sem pressa.", "vibe_tags": ["calmo", "noturno", "foco"]}</output>
</example>
</examples>
"""
USER_V3 = f"{EXAMPLES}\n<track>\n{TRACK_JSON}\n</track>"

ok = 0
for _ in range(10):
    try:
        json.loads(ask(SYSTEM_V3, USER_V3))
        ok += 1
    except json.JSONDecodeError:
        pass
print(f"V3: {ok}/10 respostas com JSON válido")