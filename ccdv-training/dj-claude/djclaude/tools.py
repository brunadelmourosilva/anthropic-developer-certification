# arquivo: djclaude/tools.py
import json
from djclaude import music_db


def _tool(name, description, properties, required=()):
    return {"name": name, "description": description,
            "input_schema": {"type": "object", "properties": properties, "required": list(required)}}


SEARCH_TRACKS = _tool(
    "search_tracks",
    "Search the local music catalog and return up to `limit` tracks (id, title, artist, genre, bpm, "
    "energy 0-1, mood, duration_sec). Use it whenever you need candidate tracks for a request. "
    "Do NOT use it to read one track you already have an id for (use get_track) or to look at "
    "playlists (use get_playlist / list_playlists). Returns an empty list when nothing matches.",
    {
        "genre": {"type": "string", "enum": music_db.GENRES},
        "mood": {"type": "string", "enum": music_db.MOODS},
        "artist": {"type": "string", "description": "Case-insensitive substring of the artist name."},
        "min_energy": {"type": "number", "description": "0.0-1.0"},
        "max_energy": {"type": "number", "description": "0.0-1.0"},
        "min_bpm": {"type": "integer"},
        "max_bpm": {"type": "integer"},
        "limit": {"type": "integer", "description": "1-25, default 10."},
    },
)
GET_TRACK = _tool(
    "get_track",
    "Get the full details of ONE track by id (adds album, year and free-text notes). Use it only when you "
    "already have an id from a previous result and need more detail. Do NOT use it to discover tracks; "
    "use search_tracks for that. Fails if the id does not exist.",
    {"track_id": {"type": "string", "description": "Track id such as 't042'."}},
    required=["track_id"],
)
CREATE_PLAYLIST = _tool(
    "create_playlist",
    "Create a new, empty playlist with a unique name. Use it once, before add_tracks_to_playlist, when "
    "the user asks for a new playlist. Do NOT use it to modify an existing playlist. "
    "Fails if the name already exists.",
    {"name": {"type": "string"}},
    required=["name"],
)
ADD_TRACKS = _tool(
    "add_tracks_to_playlist",
    "Append tracks (by id) to an EXISTING playlist; returns how many were added and how many were skipped "
    "as duplicates. The playlist must already exist (call create_playlist first) and every id must come "
    "from a previous search_tracks result. Never invent ids.",
    {
        "name": {"type": "string", "description": "Name of the existing playlist."},
        "track_ids": {"type": "array", "items": {"type": "string"}, "description": "At most 50 ids per call."},
    },
    required=["name", "track_ids"],
)
GET_PLAYLIST = _tool(
    "get_playlist",
    "Return the tracks of ONE playlist plus its total duration in minutes. Use it to verify the result "
    "after adding tracks or when the user asks what is inside a specific playlist. Do NOT use it to list "
    "all playlists (use list_playlists).",
    {"name": {"type": "string"}},
    required=["name"],
)
LIST_PLAYLISTS = _tool(
    "list_playlists",
    "List all playlists with track counts and total minutes. Use it when the user asks which playlists "
    "exist, or before creating one to avoid name clashes. Takes no arguments.",
    {},
)
DELETE_PLAYLIST = _tool(
    "delete_playlist",
    "Permanently delete a playlist by name. DESTRUCTIVE: only use it when the user explicitly asked to "
    "delete that specific playlist in the current conversation. Never use it as a cleanup step.",
    {"name": {"type": "string"}},
    required=["name"],
)

TOOLS = [SEARCH_TRACKS, GET_TRACK, CREATE_PLAYLIST, ADD_TRACKS, GET_PLAYLIST, LIST_PLAYLISTS, DELETE_PLAYLIST]

HANDLERS = {
    "search_tracks": lambda a: music_db.search_tracks(**a),
    "get_track": lambda a: music_db.get_track(a["track_id"]),
    "create_playlist": lambda a: music_db.create_playlist(a["name"]),
    "add_tracks_to_playlist": lambda a: music_db.add_tracks(a["name"], a["track_ids"]),
    "get_playlist": lambda a: music_db.get_playlist(a["name"]),
    "list_playlists": lambda a: music_db.list_playlists(),
    "delete_playlist": lambda a: music_db.delete_playlist(a["name"]),
}


def execute_tool(name: str, args: dict) -> tuple[str, bool]:
    handler = HANDLERS.get(name)
    if handler is None:
        return f"Unknown tool: {name}", True
    try:
        return json.dumps(handler(args), ensure_ascii=False), False
    except (ValueError, TypeError, KeyError) as exc:
        return f"Error: {exc}", True
