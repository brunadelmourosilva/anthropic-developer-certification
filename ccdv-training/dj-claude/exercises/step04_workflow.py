"""A versão determinística do pedido do passo 4: uma chamada ao LLM, sem loop."""

import asyncio
import json
import time

from djclaude import music_db
from djclaude.config import MODEL_WORKER, make_client

# Crie algo para um dia de chuva.
REQUEST = "Crie uma playlist 'Foco (Workflow Model)' de ~30 minutos com lofi relaxante."
PLAYLIST_NAME = "Foco (Workflow Model)"

PLANNER_SYSTEM = """You extract playlist constraints from a user's request.

<output_format>
Return ONLY a JSON object with exactly these keys:
- "genre": one of rock, jazz, electronic, lofi, pop, mpb, hiphop, or null
- "mood": one of energetic, angry, nostalgic, relaxed, romantic, happy, focused, melancholic, or null
- "target_minutes": positive number, or null when the request gives no duration
Do not add markdown fences or explanations. Do not invent constraints absent from the request.
</output_format>"""


def text_of(content) -> str:
    return "".join(block.text for block in content if block.type == "text")


def parse_plan(text: str) -> dict:
    """Parse and validate the one structured output produced by the planner."""
    plan = json.loads(text)
    if set(plan) != {"genre", "mood", "target_minutes"}:
        raise ValueError("Planner returned an unexpected schema.")
    if plan["genre"] not in (*music_db.GENRES, None):
        raise ValueError(f"Unsupported genre: {plan['genre']!r}")
    if plan["mood"] not in (*music_db.MOODS, None):
        raise ValueError(f"Unsupported mood: {plan['mood']!r}")
    if plan["target_minutes"] is None or float(plan["target_minutes"]) <= 0:
        raise ValueError("A positive target_minutes is required for this fixed workflow.")
    plan["target_minutes"] = float(plan["target_minutes"])
    return plan


def select_to_target(tracks: list[dict], target_minutes: float) -> list[dict]:
    """Keep catalog-order tracks until their combined duration reaches the requested target."""
    target_seconds = target_minutes * 60
    selected: list[dict] = []
    total_seconds = 0
    for track in tracks:
        selected.append(track)
        total_seconds += track["duration_sec"]
        if total_seconds >= target_seconds:
            break
    return selected


async def main():
    client = make_client()

    # The workflow's sole LLM call: turn natural language into a fixed schema.
    started = time.perf_counter()
    response = await client.messages.create(
        model=MODEL_WORKER,
        max_tokens=150,
        system=PLANNER_SYSTEM,
        messages=[{"role": "user", "content": f"<request>{REQUEST}</request>"}],
    )

    print(response.content)
    
    latency = time.perf_counter() - started
    plan = parse_plan(text_of(response.content))

    # Everything below is ordinary, deterministic application code -- no more LLM calls.
    candidates = music_db.search_tracks(genre=plan["genre"], mood=plan["mood"], limit=25)
    selected = select_to_target(candidates, plan["target_minutes"])
    if not selected:
        raise ValueError("No catalog tracks match the requested constraints.")

    music_db.create_playlist(PLAYLIST_NAME)
    music_db.add_tracks(PLAYLIST_NAME, [track["id"] for track in selected])
    playlist = music_db.get_playlist(PLAYLIST_NAME)

    print(json.dumps(plan, ensure_ascii=False))
    print(f"Playlist '{playlist['name']}': {playlist['total_minutes']} minutos")
    print("faixas:", ", ".join(track["title"] for track in playlist["tracks"]))
    print(f"tokens in/out: {response.usage.input_tokens}/{response.usage.output_tokens} | "
          f"latência: {latency:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
