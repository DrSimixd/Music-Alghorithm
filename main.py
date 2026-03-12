#!/usr/bin/env python3
"""
Spotify Playlist Mixing Algorithm
==================================
Fetches a Spotify playlist, scores harmonic/BPM compatibility between tracks,
reorders them for the smoothest DJ-style flow, and outputs per-transition mixing
instructions matching Spotify's "Edit Transition" UI.

Usage:
    python main.py <playlist_url_or_id> [options]

Options:
    --fast          Skip audio_analysis API calls (faster, no mixout timing)
    --no-reorder    Analyze transitions in the original playlist order
    --arc           Enforce an energy arc: buildup → peak → cooldown
    --json FILE     Also save results as JSON

Examples:
    python main.py https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd
    python main.py 37i9dQZF1DX0XUsuxWHRQd --fast --json mix.json
    python main.py <url> --arc --json set.json
"""

import argparse
import sys

from spotify_client import fetch_playlist
from ordering import order_tracks
from mixer import build_transitions
from output import print_tracklist, print_transitions, save_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze a Spotify playlist and generate DJ transition data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "playlist",
        help="Spotify playlist URL or bare playlist ID",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip audio_analysis calls (faster, no mixout timing data)",
    )
    parser.add_argument(
        "--no-reorder",
        action="store_true",
        help="Keep original playlist order instead of optimizing",
    )
    parser.add_argument(
        "--arc",
        action="store_true",
        help="Enforce energy arc: buildup → peak → cooldown",
    )
    parser.add_argument(
        "--json",
        metavar="FILE",
        help="Save full transition data as JSON to this file",
    )

    args = parser.parse_args()

    # 1. Fetch playlist tracks from Spotify API
    tracks = fetch_playlist(args.playlist, fast=args.fast)
    if len(tracks) < 2:
        print("Need at least 2 tracks to generate transitions.")
        sys.exit(1)

    # 2. Optionally reorder for smoothest flow
    if not args.no_reorder:
        tracks = order_tracks(tracks, use_arc=args.arc)

    # 3. Print reordered tracklist
    print_tracklist(tracks)

    # 4. Generate transition recommendations
    transitions = build_transitions(tracks)

    # 5. Print transition guide
    print_transitions(transitions)

    # 6. Optional JSON export
    if args.json:
        save_json(transitions, args.json)


if __name__ == "__main__":
    main()
