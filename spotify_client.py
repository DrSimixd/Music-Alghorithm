"""
Spotify API client: authentication and playlist data fetching.

Requires environment variables:
  SPOTIFY_CLIENT_ID
  SPOTIFY_CLIENT_SECRET
  SPOTIFY_REDIRECT_URI  (default: http://localhost:8888/callback)
"""

import os
import re
import time
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from models import Track
from camelot import spotify_key_to_camelot

load_dotenv()

_SCOPE = "playlist-read-private playlist-read-collaborative"
_BATCH = 100  # Spotify max per API call


def _build_client() -> spotipy.Spotify:
    auth_manager = SpotifyOAuth(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"),
        scope=_SCOPE,
        open_browser=True,
        cache_path=".cache",
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def _parse_playlist_id(url_or_id: str) -> str:
    """Extract playlist ID from a URL like open.spotify.com/playlist/ID or bare ID."""
    match = re.search(r"playlist[/:]([A-Za-z0-9]+)", url_or_id)
    if match:
        return match.group(1)
    # Assume bare ID
    return url_or_id.strip()


def _fetch_all_items(sp: spotipy.Spotify, playlist_id: str) -> list[dict]:
    """Paginate through playlist tracks, returning raw Spotify track objects."""
    items = []
    offset = 0
    while True:
        result = sp.playlist_items(
            playlist_id,
            fields="items(track(id,name,artists,duration_ms)),next",
            limit=_BATCH,
            offset=offset,
        )
        batch = result.get("items", [])
        for item in batch:
            track = item.get("track")
            if track and track.get("id"):
                items.append(track)
        if result.get("next") is None:
            break
        offset += _BATCH
    return items


def _fetch_audio_features(sp: spotipy.Spotify, track_ids: list[str]) -> dict[str, dict]:
    """Batch-fetch audio features. Returns {track_id: features_dict}."""
    features_map: dict[str, dict] = {}
    for i in range(0, len(track_ids), _BATCH):
        batch = track_ids[i : i + _BATCH]
        results = sp.audio_features(batch)
        for feat in results:
            if feat:
                features_map[feat["id"]] = feat
    return features_map


def _fetch_audio_analysis(sp: spotipy.Spotify, track_id: str) -> dict:
    """Fetch full audio analysis for one track (sections, beats)."""
    try:
        return sp.audio_analysis(track_id)
    except Exception:
        return {}


def fetch_playlist(url_or_id: str, fast: bool = False) -> list[Track]:
    """
    Fetch a Spotify playlist and return a list of Track objects.

    Args:
        url_or_id: Spotify playlist URL or bare playlist ID.
        fast: If True, skip per-track audio_analysis calls (no mixout timing).

    Returns:
        List of Track objects ordered as they appear in the playlist.
    """
    sp = _build_client()
    playlist_id = _parse_playlist_id(url_or_id)

    print(f"Fetching playlist {playlist_id}...")
    raw_tracks = _fetch_all_items(sp, playlist_id)
    print(f"  Found {len(raw_tracks)} tracks")

    track_ids = [t["id"] for t in raw_tracks]
    print("Fetching audio features...")
    features_map = _fetch_audio_features(sp, track_ids)

    tracks: list[Track] = []
    for i, raw in enumerate(raw_tracks):
        tid = raw["id"]
        feat = features_map.get(tid)
        if feat is None:
            print(f"  Warning: no audio features for '{raw['name']}', skipping")
            continue

        key = feat.get("key", -1)
        mode = feat.get("mode", -1)
        camelot = spotify_key_to_camelot(key, mode) if key >= 0 and mode >= 0 else "?"

        artist_names = ", ".join(a["name"] for a in raw.get("artists", []))

        sections: list[dict] = []
        beats: list[dict] = []
        if not fast:
            # Rate-limit: Spotify allows ~1 audio_analysis call/sec before throttling
            print(f"  [{i+1}/{len(raw_tracks)}] Fetching analysis: {raw['name'][:40]}")
            analysis = _fetch_audio_analysis(sp, tid)
            sections = analysis.get("sections", [])
            beats = analysis.get("beats", [])
            time.sleep(0.2)  # gentle pacing

        tracks.append(Track(
            id=tid,
            title=raw["name"],
            artist=artist_names,
            duration_ms=raw.get("duration_ms", 0),
            bpm=feat.get("tempo", 0.0),
            key=key,
            mode=mode,
            camelot=camelot,
            energy=feat.get("energy", 0.0),
            danceability=feat.get("danceability", 0.0),
            loudness=feat.get("loudness", -60.0),
            valence=feat.get("valence", 0.0),
            sections=sections,
            beats=beats,
        ))

    print(f"Ready: {len(tracks)} tracks loaded.\n")
    return tracks
