"""
Transition parameter recommendation engine.

For each consecutive pair of tracks, produces the exact data fields shown in
Spotify's "Edit Transition" UI:
  - Transition point (mixout time + bar number)
  - Transition length in bars
  - Volume type  (Overlap / Fade / Rise / Blend)
  - EQ           (None / Bass cut)
  - Filter       (None / High-pass / Low-pass)
  - Style        (Auto / Fade / Rise / Blend)
"""

import statistics
from models import Track, TransitionData
from analyzer import score_transition


def _detect_mixout(track: Track) -> tuple[float, int]:
    """
    Find the optimal mix-out point in track A using audio_analysis sections.

    Looks for the last section that is quieter than average (outro region).

    Returns:
        (mixout_time_sec, mixout_bar) — both -1 if no section data available.
    """
    if not track.sections:
        return -1.0, -1

    loudnesses = [s["loudness"] for s in track.sections if "loudness" in s]
    if not loudnesses:
        return -1.0, -1

    mean_loud = statistics.mean(loudnesses)
    threshold = mean_loud - 2.0  # sections quieter than mean - 2 dB

    # Walk backwards to find last quiet section (outro)
    last_quiet = None
    for section in reversed(track.sections):
        if section.get("loudness", 0) < threshold:
            last_quiet = section
            break

    if last_quiet is None:
        # Fallback: use 85% of track duration
        mixout_sec = (track.duration_ms / 1000) * 0.85
    else:
        mixout_sec = last_quiet["start"]

    # Convert seconds → bar number
    if track.bpm > 0:
        seconds_per_bar = (60.0 / track.bpm) * 4
        mixout_bar = max(0, int(mixout_sec / seconds_per_bar))
    else:
        mixout_bar = -1

    return mixout_sec, mixout_bar


def _recommend_bars(bpm_diff: float) -> int:
    """Recommend transition length in bars based on BPM difference."""
    if bpm_diff <= 2:
        return 2
    elif bpm_diff <= 5:
        return 4
    elif bpm_diff <= 8:
        return 8
    else:
        return 16


def _recommend_volume(a: Track, b: Track) -> str:
    """Choose volume/crossfade type based on energy flow."""
    diff = b.energy - a.energy
    if abs(diff) < 0.1:
        return "Overlap"
    elif diff > 0.1:
        return "Rise"
    elif diff < -0.1:
        return "Fade"
    return "Blend"


def _recommend_filter(a: Track, b: Track) -> str:
    """Recommend filter based on BPM and energy change."""
    bpm_up = b.bpm > a.bpm + 5
    energy_up = b.energy > a.energy + 0.15
    bpm_down = b.bpm < a.bpm - 5

    if bpm_up or energy_up:
        return "High-pass"
    elif bpm_down:
        return "Low-pass"
    return "None"


def _recommend_eq(key_score: float) -> str:
    """Recommend EQ based on harmonic compatibility."""
    if key_score < 0.5:
        return "Bass cut"
    return "None"


def _recommend_style(score: float, volume: str) -> str:
    """Recommend overall transition style."""
    if score >= 0.8:
        return "Auto"
    if volume == "Fade":
        return "Fade"
    if volume == "Rise":
        return "Rise"
    return "Blend"


def recommend_transition(a: Track, b: Track) -> TransitionData:
    """
    Produce full transition recommendation for going from track a → track b.

    This generates exactly the data fields shown in Spotify's Edit Transition UI.
    """
    total_score, details = score_transition(a, b)
    bpm_diff = details["bpm_diff"]
    key_score = details["key_score"]
    key_label = details["key_label"]
    halftime = details["halftime"]

    mixout_sec, mixout_bar = _detect_mixout(a)
    bars = _recommend_bars(bpm_diff)
    avg_bpm = (a.bpm + b.bpm) / 2
    transition_sec = bars * (4 * 60.0 / avg_bpm) if avg_bpm > 0 else 0.0
    volume = _recommend_volume(a, b)
    filter_type = _recommend_filter(a, b)
    eq = _recommend_eq(key_score)
    style = _recommend_style(total_score, volume)

    return TransitionData(
        track_a=a,
        track_b=b,
        bpm_diff=bpm_diff,
        halftime_compatible=halftime,
        key_compatibility=key_label,
        compatibility_score=total_score,
        mixout_time_sec=mixout_sec,
        mixout_bar=mixout_bar,
        transition_bars=bars,
        transition_sec=transition_sec,
        volume_type=volume,
        eq=eq,
        filter_type=filter_type,
        style=style,
    )


def build_transitions(tracks: list[Track]) -> list[TransitionData]:
    """Build the full list of transitions for an ordered track list."""
    return [recommend_transition(tracks[i], tracks[i + 1]) for i in range(len(tracks) - 1)]
