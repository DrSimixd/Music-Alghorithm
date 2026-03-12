# Music-Algorithm

A Python CLI tool that analyzes Spotify playlists and generates DJ-style mixing recommendations. It fetches track audio features, scores pairwise compatibility, reorders tracks for smooth transitions, and outputs per-transition mixing parameters that match Spotify's **Edit Transition** UI.

## Features

- **Harmonic mixing** — Camelot Wheel key compatibility scoring
- **BPM matching** — detects half-time and double-time relationships
- **Smart reordering** — greedy nearest-neighbor + 2-opt / simulated annealing optimization
- **Energy arc mode** — structures the playlist into buildup → peak → cooldown zones
- **Transition recommendations** — volume type, EQ, filter, style, and mix-out timing per transition
- **JSON export** — machine-readable output for further processing

## Requirements

- Python 3.8+
- A [Spotify Developer](https://developer.spotify.com/dashboard) app (Client ID + Secret)

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure Spotify credentials
cp .env.example .env
# Edit .env and fill in your SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI
```

## Usage

```bash
python main.py <playlist_url_or_id> [options]
```

| Option | Description |
|--------|-------------|
| `--fast` | Skip detailed audio analysis (faster, less precise mix-out timing) |
| `--no-reorder` | Keep the original playlist order |
| `--arc` | Enforce energy arc: buildup → peak → cooldown |
| `--json FILE` | Export full transition data to a JSON file |

**Examples:**

```bash
# Analyze and reorder a playlist
python main.py https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

# Energy arc with JSON export
python main.py 37i9dQZF1DXcBWIGoYBM5M --arc --json transitions.json

# Fast mode, keep original order
python main.py 37i9dQZF1DXcBWIGoYBM5M --fast --no-reorder
```

The first run will open a browser for Spotify OAuth2 authentication. A `.cache` file stores the token for subsequent runs.

## How It Works

1. **Fetch** — pulls track metadata and audio features (BPM, key, energy, danceability, loudness, valence) from the Spotify API
2. **Score** — computes pairwise compatibility: 40% harmonic key + 40% BPM + 20% energy
3. **Reorder** — optimizes track sequence using greedy + 2-opt (≤200 tracks) or simulated annealing (>200 tracks)
4. **Mix** — generates transition parameters for each consecutive track pair
5. **Output** — displays a formatted tracklist and transition guide in the terminal

## License

MIT
