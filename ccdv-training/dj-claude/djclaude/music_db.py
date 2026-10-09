# arquivo: djclaude/music_db.py
import csv
import json
import os
from pathlib import Path
from typing import Literal, get_args

Genre = Literal["rock", "jazz", "electronic", "lofi", "pop", "mpb", "hiphop"]
Mood = Literal["energetic", "angry", "nostalgic", "relaxed", "romantic", "happy", "focused", "melancholic"]
GENRES = list(get_args(Genre))
MOODS = list(get_args(Mood))

# DJ_DATA_DIR permite apontar para uma pasta temporária (usado nos evals, passo 12)
DATA_DIR = Path(os.getenv("DJ_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
TRACKS_CSV = DATA_DIR / "tracks.csv"
PLAYLISTS_JSON = DATA_DIR / "playlists.json"
PROFILE_JSON = DATA_DIR / "taste_profile.json"


def load_tracks() -> list[dict]:
    with open(TRACKS_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["year"] = int(r["year"])
        r["bpm"] = int(r["bpm"])
        r["energy"] = float(r["energy"])
        r["duration_sec"] = int(r["duration_sec"])
    return rows


def _summary(t: dict) -> dict:
    keys = ("id", "title", "artist", "genre", "bpm", "energy", "mood", "duration_sec")
    return {k: t[k] for k in keys}


def search_tracks(genre=None, mood=None, artist=None, min_energy=None, max_energy=None,
                  min_bpm=None, max_bpm=None, limit=10) -> list[dict]:
    limit = max(1, min(int(limit), 25))
    found = []
    for t in load_tracks():
        if genre and t["genre"] != genre:
            continue
        if mood and t["mood"] != mood:
            continue
        if artist and artist.lower() not in t["artist"].lower():
            continue
        if min_energy is not None and t["energy"] < min_energy:
            continue
        if max_energy is not None and t["energy"] > max_energy:
            continue
        if min_bpm is not None and t["bpm"] < min_bpm:
            continue
        if max_bpm is not None and t["bpm"] > max_bpm:
            continue
        found.append(_summary(t))
    return found[:limit]


def get_track(track_id: str) -> dict:
    for t in load_tracks():
        if t["id"] == track_id:
            return t  # inclui album, year e notes
    raise ValueError(f"Track '{track_id}' not found.")


def _read_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def create_playlist(name: str) -> dict:
    name = name.strip()
    if not name:
        raise ValueError("Playlist name cannot be empty.")
    playlists = _read_json(PLAYLISTS_JSON, {})
    if name in playlists:
        raise ValueError(f"Playlist '{name}' already exists.")
    playlists[name] = []
    _write_json(PLAYLISTS_JSON, playlists)
    return {"name": name, "track_count": 0}


def add_tracks(name: str, track_ids: list[str]) -> dict:
    playlists = _read_json(PLAYLISTS_JSON, {})
    if name not in playlists:
        raise ValueError(f"Playlist '{name}' not found. Create it first.")
    known = {t["id"] for t in load_tracks()}
    unknown = [i for i in track_ids if i not in known]
    if unknown:
        raise ValueError(f"Unknown track ids: {unknown}")
    added, skipped = [], []
    for i in track_ids:
        if i in playlists[name]:
            skipped.append(i)
        else:
            playlists[name].append(i)
            added.append(i)
    _write_json(PLAYLISTS_JSON, playlists)
    return {"name": name, "added": len(added), "skipped_duplicates": len(skipped),
            "track_count": len(playlists[name])}


def get_playlist(name: str) -> dict:
    playlists = _read_json(PLAYLISTS_JSON, {})
    if name not in playlists:
        raise ValueError(f"Playlist '{name}' not found.")
    index = {t["id"]: t for t in load_tracks()}
    tracks = [_summary(index[i]) for i in playlists[name] if i in index]
    total = sum(t["duration_sec"] for t in tracks)
    return {"name": name, "total_minutes": round(total / 60, 1), "tracks": tracks}


def list_playlists() -> list[dict]:
    playlists = _read_json(PLAYLISTS_JSON, {})
    index = {t["id"]: t for t in load_tracks()}
    return [
        {"name": n, "track_count": len(ids),
         "total_minutes": round(sum(index[i]["duration_sec"] for i in ids if i in index) / 60, 1)}
        for n, ids in playlists.items()
    ]


def delete_playlist(name: str) -> dict:
    playlists = _read_json(PLAYLISTS_JSON, {})
    if name not in playlists:
        raise ValueError(f"Playlist '{name}' not found.")
    del playlists[name]
    _write_json(PLAYLISTS_JSON, playlists)
    return {"deleted": name}


# --- usadas no passo 8 (memória externa) ---
def get_taste_profile() -> dict:
    return _read_json(PROFILE_JSON, {"liked_genres": [], "disliked_moods": [], "notes": ""})


def save_taste_profile(liked_genres=None, disliked_moods=None, notes=None) -> dict:
    profile = get_taste_profile()
    if liked_genres is not None:
        profile["liked_genres"] = sorted(set(profile["liked_genres"]) | set(liked_genres))
    if disliked_moods is not None:
        profile["disliked_moods"] = sorted(set(profile["disliked_moods"]) | set(disliked_moods))
    if notes is not None:
        profile["notes"] = notes
    _write_json(PROFILE_JSON, profile)
    return profile
