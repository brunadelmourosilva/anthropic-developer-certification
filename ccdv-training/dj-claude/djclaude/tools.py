# arquivo: djclaude/tools.py
import json
from djclaude import music_db

SEARCH_TRACKS = {
    "name": "search_tracks",
    "description": (
        "Search the local music catalog and return up to `limit` tracks (id, title, artist, genre, bpm, "
        "energy 0-1, mood, duration_sec). Use it whenever you need candidate tracks for a request. "
        "Returns an empty list when nothing matches."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "genre": {"type": "string", "enum": music_db.GENRES},
            "mood": {"type": "string", "enum": music_db.MOODS},
            "limit": {"type": "integer", "description": "1-25, default 10."},
        },
        "required": [],
    },
}
TOOLS = [SEARCH_TRACKS]

HANDLERS = {"search_tracks": lambda a: music_db.search_tracks(**a)}


def execute_tool(name: str, args: dict) -> tuple[str, bool]:
    """Retorna (conteúdo, is_error). Erros viram texto descritivo — nunca silêncio."""
    handler = HANDLERS.get(name)
    if handler is None:
        return f"Unknown tool: {name}", True
    try:
        return json.dumps(handler(args), ensure_ascii=False), False
    except (ValueError, TypeError, KeyError) as exc:
        return f"Error: {exc}", True
