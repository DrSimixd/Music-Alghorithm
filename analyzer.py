"""
Pairwise transition compatibility scoring between tracks.

Combines BPM, harmonic key, and energy continuity into a single 0.0–1.0 score
used by the ordering algorithm to find the smoothest playlist sequence.
"""

from models import Track
from camelot import camelot_score


def _bpm_score(bpm_a: float, bpm_b: float) -> tuple[float, float, bool]:
    """
    Score BPM compatibility.

    Also checks half/double-time compatibility (e.g. 75 BPM → 150 BPM).

    Returns:
        (score, effective_diff, halftime_compatible)
    """
    direct_diff = abs(bpm_a - bpm_b)
    half_diff = abs(bpm_a - 2 * bpm_b)
    double_diff = abs(2 * bpm_a - bpm_b)
    effective_diff = min(direct_diff, half_diff, double_diff)
    halftime = effective_diff < direct_diff  # used a half/double time match

    if effective_diff <= 3:
        score = 1.0
    elif effective_diff <= 6:
        score = 0.7
    elif effective_diff <= 8:
        score = 0.5
    elif effective_diff <= 20:
        score = 0.3
    else:
        score = 0.0

    return score, effective_diff, halftime


def score_transition(a: Track, b: Track) -> tuple[float, dict]:
    """
    Compute a compatibility score for transitioning from track a to track b.

    Returns:
        (total_score: float, details: dict)
        total_score: 0.0 (incompatible) → 1.0 (perfect)
        details: breakdown of component scores and metadata
    """
    bpm_s, bpm_diff, halftime = _bpm_score(a.bpm, b.bpm)
    key_s, key_label = camelot_score(a.camelot, b.camelot)
    energy_s = 1.0 - abs(a.energy - b.energy)

    total = 0.4 * key_s + 0.4 * bpm_s + 0.2 * energy_s

    return total, {
        "bpm_score": bpm_s,
        "key_score": key_s,
        "energy_score": energy_s,
        "bpm_diff": bpm_diff,
        "key_label": key_label,
        "halftime": halftime,
    }


def build_score_matrix(tracks: list[Track]) -> list[list[float]]:
    """
    Build an NxN matrix of pairwise transition scores.

    matrix[i][j] = score for going from tracks[i] → tracks[j]
    Diagonal is 0 (can't transition to self).
    """
    n = len(tracks)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                score, _ = score_transition(tracks[i], tracks[j])
                matrix[i][j] = score
    return matrix
