import csv
import random
from pathlib import Path

random.seed(42)

PROFILES = {
    "rock":       {"bpm": (110, 170), "energy": (0.60, 0.95), "moods": ["energetic", "angry", "nostalgic"]},
    "jazz":       {"bpm": (70, 140),  "energy": (0.20, 0.60), "moods": ["relaxed", "romantic", "nostalgic"]},
    "electronic": {"bpm": (115, 150), "energy": (0.65, 1.00), "moods": ["energetic", "happy", "focused"]},
    "lofi":       {"bpm": (60, 90),   "energy": (0.10, 0.40), "moods": ["relaxed", "focused", "melancholic"]},
    "pop":        {"bpm": (95, 130),  "energy": (0.50, 0.85), "moods": ["happy", "romantic", "energetic"]},
    "mpb":        {"bpm": (70, 120),  "energy": (0.20, 0.65), "moods": ["romantic", "relaxed", "nostalgic"]},
    "hiphop":     {"bpm": (80, 105),  "energy": (0.55, 0.90), "moods": ["energetic", "angry", "focused"]},
}
ARTISTS = [
    "Luna Cobalto", "Os Vagalumes", "Maré Alta", "Neon Jardim", "Cais do Sol", "Pedro Quasar",
    "Velvet Rio", "Ciranda Digital", "Nina Ferrugem", "Banda Horizonte", "Atlas Lunar",
    "DJ Pitanga", "Quarteto Âmbar", "Sombra & Luz", "Tomás Brisa", "Eco Urbano",
]
WORDS_A = ["Noite", "Estrada", "Cidade", "Sol", "Chuva", "Neon", "Maré", "Janela", "Poeira", "Vento", "Cobre"]
WORDS_B = ["Azul", "de Verão", "sem Fim", "Elétrica", "Lenta", "Vazia", "em Chamas", "da Madrugada", "Dourada"]
NOTES = [
    "Instrumental, great for studying.", "Live recording from a small club.",
    "Features a long guitar solo.", "Minimal arrangement with warm bass.", "Radio edit.", "",
]

genres = list(PROFILES)
artist_genre = {a: genres[i % len(genres)] for i, a in enumerate(ARTISTS)}

rows = []
for n in range(1, 201):
    artist = random.choice(ARTISTS)
    genre = artist_genre[artist]
    p = PROFILES[genre]
    rows.append({
        "id": f"t{n:03d}",
        "title": f"{random.choice(WORDS_A)} {random.choice(WORDS_B)}",
        "artist": artist,
        "album": f"{random.choice(WORDS_A)} Sessions",
        "year": random.randint(1998, 2025),
        "genre": genre,
        "bpm": random.randint(*p["bpm"]),
        "energy": round(random.uniform(*p["energy"]), 2),
        "mood": random.choice(p["moods"]),
        "duration_sec": random.randint(120, 330),
        "notes": random.choice(NOTES),
    })

out = Path(__file__).resolve().parent.parent / "data" / "tracks.csv"
out.parent.mkdir(exist_ok=True)
with open(out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(f"{len(rows)} faixas em {out}")
