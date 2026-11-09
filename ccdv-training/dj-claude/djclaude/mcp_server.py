# arquivo: djclaude/mcp_server.py
import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from djclaude import music_db
from djclaude.music_db import Genre, Mood

# ⚠️ Servidor stdio: NUNCA use print() (stdout é o canal do protocolo). Logs vão para stderr.
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

mcp = FastMCP("dj-claude-music")


# O docstring vira a DESCRIÇÃO da tool; os type hints viram o input_schema.
@mcp.tool()
def search_tracks(genre: Genre | None = None, mood: Mood | None = None, artist: str | None = None,
                  min_energy: float | None = None, max_energy: float | None = None,
                  min_bpm: int | None = None, max_bpm: int | None = None, limit: int = 10) -> dict:
    """Search the local music catalog and return up to `limit` tracks (id, title, artist, genre, bpm,
    energy 0-1, mood, duration_sec). Use it whenever you need candidate tracks for a request.
    Do NOT use it to read one track you already have an id for (use get_track) or to look at
    playlists (use get_playlist / list_playlists). `limit` is 1-25. Returns an empty list when nothing matches."""
    tracks = music_db.search_tracks(genre=genre, mood=mood, artist=artist, min_energy=min_energy,
                                    max_energy=max_energy, min_bpm=min_bpm, max_bpm=max_bpm, limit=limit)
    return {"count": len(tracks), "tracks": tracks}


@mcp.tool()
def get_track(track_id: str) -> dict:
    """Get the full details of ONE track by id (adds album, year and free-text notes). Use it only when
    you already have an id from a previous result. Do NOT use it to discover tracks (use search_tracks).
    Fails if the id does not exist."""
    return music_db.get_track(track_id)


@mcp.tool()
def create_playlist(name: str) -> dict:
    """Create a new, empty playlist with a unique name. Use it once, before add_tracks_to_playlist, when the
    user asks for a new playlist. Do NOT use it to modify an existing playlist. Fails if the name exists."""
    return music_db.create_playlist(name)


@mcp.tool()
def add_tracks_to_playlist(name: str, track_ids: list[str]) -> dict:
    """Append tracks (by id, at most 50 per call) to an EXISTING playlist; returns how many were added and
    how many were skipped as duplicates. Create the playlist first and use only ids from search_tracks."""
    return music_db.add_tracks(name, track_ids)


@mcp.tool()
def get_playlist(name: str) -> dict:
    """Return the tracks of ONE playlist plus its total duration in minutes. Use it to verify a playlist after
    adding tracks. Do NOT use it to list all playlists (use list_playlists)."""
    return music_db.get_playlist(name)


@mcp.tool()
def list_playlists() -> dict:
    """List all playlists with track counts and total minutes. Use it when the user asks which playlists
    exist, or before creating one to avoid name clashes. Takes no arguments."""
    return {"playlists": music_db.list_playlists()}


@mcp.tool()
def delete_playlist(name: str) -> dict:
    """Permanently delete a playlist by name. DESTRUCTIVE: only use it when the user explicitly asked to
    delete that specific playlist in the current conversation. Never use it as a cleanup step."""
    return music_db.delete_playlist(name)


if __name__ == "__main__":
    # stdio = servidor local, iniciado como subprocesso pelo cliente.
    # MCP_TRANSPORT=streamable-http faz o mesmo servidor atender via HTTP (passo 7).
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "stdio"))
