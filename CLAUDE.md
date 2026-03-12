# CLAUDE.md — Music-Algorithm Codebase Guide

This file provides context for AI assistants working on the Music-Algorithm codebase.

## Project Overview

Music-Algorithm is a Python CLI tool that analyzes Spotify playlists and generates DJ-style mixing recommendations. Given a Spotify playlist URL or ID, it:

1. Fetches track metadata and audio features via the Spotify Web API
2. Scores pairwise track compatibility (BPM, key, energy)
3. Reorders tracks to minimize transition roughness (or enforce an energy arc)
4. Outputs per-transition mixing parameters that match Spotify's "Edit Transition" UI

## Repository Structure

```
Music-Alghorithm/
├── main.py            # CLI entry point; argument parsing and pipeline orchestration
├── spotify_client.py  # Spotify OAuth2 auth and data fetching
├── models.py          # Track and TransitionData dataclasses
├── analyzer.py        # Pairwise compatibility scoring
├── camelot.py         # Harmonic key mapping (Camelot Wheel)
├── ordering.py        # Playlist reordering algorithms
├── mixer.py           # Transition recommendation engine
├── output.py          # Rich CLI output and JSON export
├── requirements.txt   # Python dependencies
├── .env.example       # Template for required environment variables
├── README.md
└── LICENSE            # MIT
```

There are no subdirectories, no test suite, and no build system. All source is at the root level.

## Running the Tool

### Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI
```

### Usage

```bash
python main.py <playlist_url_or_id> [options]
```

**Options:**
| Flag | Description |
|------|-------------|
| `--fast` | Skip audio analysis API calls (faster, less precise mix-out timing) |
| `--no-reorder` | Keep the original playlist order; only generate transitions |
| `--arc` | Enforce energy arc: buildup → peak → cooldown |
| `--json FILE` | Export full transition data to a JSON file |

**Example:**
```bash
python main.py https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M --arc --json out.json
```

First run triggers Spotify OAuth2 in the browser; a `.cache` file stores the token for subsequent runs.

## Module Responsibilities

### `main.py`
Parses `argparse` arguments, calls modules in pipeline order, and exits. Keep it thin — no business logic here.

### `spotify_client.py`
- `fetch_playlist(playlist_id, fast=False)` — returns `list[Track]`
- Authenticates with `spotipy.Spotify` using `SpotifyOAuth`
- Fetches audio features in batches of 100 (`_BATCH = 100`)
- When `fast=False`, also fetches detailed audio analysis (sections, beats) for each track
- Env vars required: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI`

### `models.py`
Two `@dataclass` types:

- **`Track`** — immutable track representation with audio features (`bpm`, `key`, `mode`, `camelot`, `energy`, `danceability`, `loudness`, `valence`) and optional analysis data (`sections`, `beats`). Has a `duration_str` property.
- **`TransitionData`** — all computed fields for one track-to-track transition, plus a `to_dict()` method for JSON serialization.

### `analyzer.py`
- `score_transition(a, b)` → `(score, key_compat, bpm_diff, halftime)` tuple
  - Score = 0.4 × key + 0.4 × BPM + 0.2 × energy
- `build_score_matrix(tracks)` → `dict[str, dict[str, float]]` keyed by track id

### `camelot.py`
- `CAMELOT_MAP` — 24-entry dict mapping `(pitch_class, mode)` → Camelot string (e.g. `"8A"`)
- `camelot_score(a, b)` → float in [0.2, 1.0] based on Camelot Wheel distance

Camelot compatibility weights:
| Relationship | Score |
|---|---|
| Same key | 1.0 |
| Relative key (same number, A↔B) | 0.8 |
| Adjacent same letter (±1 step) | 0.9 |
| Adjacent different letter | 0.6 |
| 2 steps away | 0.5 |
| Dominant (7 semitones) | 0.55 |
| Clash | 0.2 |

### `ordering.py`
`order_tracks(tracks, score_matrix, arc=False)` → `list[Track]`

Three-phase algorithm:
1. **Phase A — Greedy nearest-neighbor** (O(n²)): Start with highest mean-score track, greedily pick the best next unvisited track.
2. **Phase B — 2-opt local search** (n ≤ 200): Improve by reversing segments.
3. **Phase C — Simulated annealing** (n > 200): Random swaps with temperature decay.

When `arc=True`, post-process the result into three energy zones:
- Buildup (first 20% — ascending low energy)
- Peak (middle 60% — high energy)
- Cooldown (last 20% — descending low energy)

### `mixer.py`
`build_transitions(tracks, score_matrix, fast=False)` → `list[TransitionData]`

Per-transition logic:
- `_detect_mixout()` — finds optimal mix-out point using audio section analysis
- `_recommend_bars()` — transition length in bars based on BPM delta
- `_recommend_volume()` — Overlap / Fade / Rise / Blend based on energy flow
- `_recommend_filter()` — filter type based on BPM and energy change
- `_recommend_eq()` — EQ recommendation based on key compatibility
- `_recommend_style()` — overall transition style

### `output.py`
Uses the `rich` library for all terminal output.
- `print_tracklist(tracks)` — numbered table with BPM, key, energy, duration
- `print_transitions(transitions)` — per-transition panels with full recommendation details
- `save_json(transitions, path)` — writes `list[TransitionData.to_dict()]` to file

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `spotipy` | ≥2.24.0 | Spotify Web API client |
| `python-dotenv` | ≥1.0.0 | Load `.env` files |
| `rich` | ≥13.0.0 | Terminal tables, panels, colors |
| `networkx` | ≥3.0 | Graph algorithms (imported, available for future use) |

Install: `pip install -r requirements.txt`

## Code Conventions

- **Language**: Python 3, type hints throughout
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for module-level constants
- **Private helpers**: Prefix with `_` (e.g. `_bpm_score`, `_fetch_audio_features`)
- **Docstrings**: Module-level + function-level docstrings present in all modules; maintain this
- **Data structures**: Prefer `@dataclass` for structured data; avoid plain dicts for model objects
- **Error handling**: Minimal and intentional — only wrap calls that can genuinely fail at runtime (e.g. missing audio analysis). Do not add defensive try/except for internal logic.
- **Return types**: Prefer explicit return type annotations; use tuples for multi-value returns from scoring functions

## Environment Variables

Defined in `.env` (gitignored). See `.env.example`:

```
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

Do not hardcode credentials. Always use `os.getenv()` or `python-dotenv`.

## No Tests / No CI

There is currently no test suite. When adding tests:
- Use `pytest`
- Place test files in a `tests/` directory with `test_*.py` naming
- Unit test pure functions (scoring, Camelot mapping, algorithm phases) first

There is no CI/CD pipeline. Changes are committed and pushed manually.

## Git Workflow

- Main branch: `master`
- Feature branches follow the pattern: `claude/<description>-<id>`
- Commits should be clear and descriptive

## Key Algorithms — Quick Reference

**BPM compatibility** (`analyzer._bpm_score`):
- Half-time / double-time detection (±2 BPM tolerance at 0.5× or 2× ratio)
- Linear penalty for BPM difference up to 10 BPM

**Track ordering** (`ordering.order_tracks`):
- Greedy → 2-opt (small) or simulated annealing (large)
- Energy arc splits: 20% buildup / 60% peak / 20% cooldown

**Transition scoring weight** (`analyzer.score_transition`):
- 40% harmonic key compatibility
- 40% BPM compatibility
- 20% energy delta

## Common Modification Points

| Task | File(s) to edit |
|---|---|
| Change scoring weights | `analyzer.py` → `score_transition()` |
| Add a new Camelot rule | `camelot.py` → `camelot_score()` |
| Add a new CLI flag | `main.py` → `argparse` setup + pipeline call |
| Change transition output fields | `models.py` → `TransitionData`, `mixer.py` → recommendation functions |
| Change display formatting | `output.py` |
| Modify energy arc logic | `ordering.py` → `_apply_energy_arc()` |
| Change Spotify scopes or batch size | `spotify_client.py` → `_SCOPE`, `_BATCH` constants |
