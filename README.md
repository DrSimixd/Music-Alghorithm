# Music-Algorithm

A CLI tool that analyzes Spotify playlists and generates DJ-style mixing recommendations. It fetches track audio features, scores pairwise compatibility, reorders tracks for smooth transitions, and outputs per-transition mixing parameters that match Spotify's **Edit Transition** UI.

## Features

- **Harmonic mixing** — Camelot Wheel key compatibility scoring
- **BPM matching** — detects half-time and double-time relationships
- **Smart reordering** — greedy nearest-neighbor + 2-opt / simulated annealing optimization
- **Energy arc mode** — structures the playlist into buildup → peak → cooldown zones
- **Transition recommendations** — volume type, EQ, filter, style, and mix-out timing per transition
- **JSON export** — machine-readable output for further processing

---

## Option A — Windows Executable (no Python required)

1. Download or clone the project on a Windows machine
2. Run `build.bat` — it installs everything and produces `dist\music-algorithm.exe`
3. Open `dist\.env` and fill in your [Spotify credentials](https://developer.spotify.com/dashboard)
4. Run the exe:

```bat
dist\music-algorithm.exe https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
dist\music-algorithm.exe <playlist_url> --arc --json transitions.json
```

The first run opens a browser for Spotify OAuth2. The `.env` and `.cache` (token) files are always read from the same folder as the exe.

> **Note:** `build.bat` requires Python + pip on the build machine. The resulting `.exe` can then be distributed and run without Python.

---

## Option B — Run with Python

**Requirements:** Python 3.8+, a [Spotify Developer](https://developer.spotify.com/dashboard) app

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI
```

```bash
python main.py <playlist_url_or_id> [options]
```

---

## Usage

Same options for both the exe and the Python script:

| Option | Description |
|--------|-------------|
| `--fast` | Skip detailed audio analysis (faster, less precise mix-out timing) |
| `--no-reorder` | Keep the original playlist order |
| `--arc` | Enforce energy arc: buildup → peak → cooldown |
| `--json FILE` | Export full transition data to a JSON file |

**Examples:**

```bash
# Analyze and reorder a playlist
music-algorithm.exe https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

# Energy arc with JSON export
music-algorithm.exe 37i9dQZF1DXcBWIGoYBM5M --arc --json transitions.json

# Fast mode, keep original order
music-algorithm.exe 37i9dQZF1DXcBWIGoYBM5M --fast --no-reorder
```

---

## How It Works

1. **Fetch** — pulls track metadata and audio features (BPM, key, energy, danceability, loudness, valence) from the Spotify API
2. **Score** — computes pairwise compatibility: 40% harmonic key + 40% BPM + 20% energy
3. **Reorder** — optimizes track sequence using greedy + 2-opt (≤200 tracks) or simulated annealing (>200 tracks)
4. **Mix** — generates transition parameters for each consecutive track pair
5. **Output** — displays a formatted tracklist and transition guide in the terminal

---

## License

MIT
