"""
Playlist ordering algorithms.

Finds the ordering of tracks that maximizes total transition compatibility.
Uses a three-phase approach:
  1. Greedy nearest-neighbor (always runs, O(n²))
  2. 2-opt local search improvement (for ≤200 tracks)
  3. Simulated annealing (for >200 tracks)

Optional energy arc constraint (--arc): enforces buildup → peak → cooldown shape.
"""

import math
import random
from models import Track
from analyzer import build_score_matrix


# ---------------------------------------------------------------------------
# Phase A — Greedy nearest-neighbor
# ---------------------------------------------------------------------------

def _greedy_order(tracks: list[Track], matrix: list[list[float]]) -> list[int]:
    """Return index sequence starting from the most 'connectable' track."""
    n = len(tracks)
    # Pick the starting track: highest mean outgoing score
    mean_scores = [sum(matrix[i]) / (n - 1) for i in range(n)]
    start = mean_scores.index(max(mean_scores))

    visited = [False] * n
    order = [start]
    visited[start] = True

    for _ in range(n - 1):
        current = order[-1]
        best_score = -1.0
        best_next = -1
        for j in range(n):
            if not visited[j] and matrix[current][j] > best_score:
                best_score = matrix[current][j]
                best_next = j
        order.append(best_next)
        visited[best_next] = True

    return order


# ---------------------------------------------------------------------------
# Phase B — 2-opt local search
# ---------------------------------------------------------------------------

def _total_score(order: list[int], matrix: list[list[float]]) -> float:
    return sum(matrix[order[i]][order[i + 1]] for i in range(len(order) - 1))


def _two_opt(order: list[int], matrix: list[list[float]]) -> list[int]:
    """Improve order via 2-opt swaps until no improvement found."""
    improved = True
    best = list(order)
    best_score = _total_score(best, matrix)

    while improved:
        improved = False
        n = len(best)
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                # Reverse the segment between i and j
                candidate = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                score = _total_score(candidate, matrix)
                if score > best_score + 1e-9:
                    best = candidate
                    best_score = score
                    improved = True
    return best


# ---------------------------------------------------------------------------
# Phase C — Simulated annealing
# ---------------------------------------------------------------------------

def _simulated_annealing(order: list[int], matrix: list[list[float]]) -> list[int]:
    """Improve order via simulated annealing (for large playlists)."""
    current = list(order)
    current_score = _total_score(current, matrix)
    best = list(current)
    best_score = current_score

    T = 1.0
    decay = 0.995
    iterations = 10_000

    for _ in range(iterations):
        # Random swap of two positions
        i, j = sorted(random.sample(range(len(current)), 2))
        candidate = current[:i] + current[i:j + 1][::-1] + current[j + 1:]
        candidate_score = _total_score(candidate, matrix)
        delta = candidate_score - current_score

        if delta > 0 or random.random() < math.exp(delta / T):
            current = candidate
            current_score = candidate_score
            if current_score > best_score:
                best = list(current)
                best_score = current_score

        T *= decay

    return best


# ---------------------------------------------------------------------------
# Energy arc enforcement
# ---------------------------------------------------------------------------

def _apply_energy_arc(tracks: list[Track], order: list[int]) -> list[int]:
    """
    Re-sort within three zones to create an energy arc:
      buildup (20%) → peak (60%) → cooldown (20%)
    """
    n = len(order)
    buildup_end = max(1, int(n * 0.20))
    peak_end = max(buildup_end + 1, int(n * 0.80))

    # Partition by energy into three groups (low / high / low)
    sorted_by_energy = sorted(order, key=lambda idx: tracks[idx].energy)
    low = sorted_by_energy[: n // 3]
    mid = sorted_by_energy[n // 3 : 2 * n // 3]
    high = sorted_by_energy[2 * n // 3 :]

    # Buildup: ascending low energy, Peak: high energy, Cooldown: descending low
    buildup = sorted(low[:buildup_end], key=lambda idx: tracks[idx].energy)
    peak = sorted(high + mid[len(buildup):], key=lambda idx: -tracks[idx].energy)
    cooldown = sorted(low[buildup_end:], key=lambda idx: tracks[idx].energy, reverse=True)

    return buildup + peak[:peak_end - buildup_end] + cooldown


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def order_tracks(tracks: list[Track], use_arc: bool = False) -> list[Track]:
    """
    Reorder tracks for the smoothest possible DJ-style transitions.

    Args:
        tracks: List of Track objects to reorder.
        use_arc: If True, enforce energy arc (build → peak → cool).

    Returns:
        New list of Track objects in optimized order.
    """
    if len(tracks) <= 1:
        return tracks

    print("Building compatibility matrix...")
    matrix = build_score_matrix(tracks)

    print("Ordering tracks (greedy nearest-neighbor)...")
    order = _greedy_order(tracks, matrix)

    if len(tracks) <= 200:
        print("Refining with 2-opt local search...")
        order = _two_opt(order, matrix)
    else:
        print("Refining with simulated annealing (large playlist)...")
        order = _simulated_annealing(order, matrix)

    if use_arc:
        print("Applying energy arc constraint...")
        order = _apply_energy_arc(tracks, order)

    score = _total_score(order, matrix)
    max_possible = (len(tracks) - 1) * 1.0
    print(f"Ordering score: {score:.2f} / {max_possible:.2f} ({score/max_possible*100:.0f}%)\n")

    return [tracks[i] for i in order]
