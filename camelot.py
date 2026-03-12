"""
Camelot Wheel key mapping and harmonic compatibility scoring.

The Camelot system assigns each musical key a number (1-12) and letter (A=minor, B=major).
Compatible keys sit adjacent on the wheel, enabling smooth harmonic transitions.
"""

# Maps (spotify_key: int, mode: int) → Camelot notation
# spotify_key: 0=C, 1=C#/Db, 2=D, ..., 11=B
# mode: 0=minor (A), 1=major (B)
CAMELOT_MAP: dict[tuple[int, int], str] = {
    # Major keys (B)
    (0, 1): "8B",   # C major
    (1, 1): "3B",   # C#/Db major
    (2, 1): "10B",  # D major
    (3, 1): "5B",   # D#/Eb major
    (4, 1): "12B",  # E major
    (5, 1): "7B",   # F major
    (6, 1): "2B",   # F#/Gb major
    (7, 1): "9B",   # G major
    (8, 1): "4B",   # G#/Ab major
    (9, 1): "11B",  # A major
    (10, 1): "6B",  # A#/Bb major
    (11, 1): "1B",  # B major
    # Minor keys (A)
    (0, 0): "5A",   # C minor
    (1, 0): "12A",  # C#/Db minor
    (2, 0): "7A",   # D minor
    (3, 0): "2A",   # D#/Eb minor
    (4, 0): "9A",   # E minor
    (5, 0): "4A",   # F minor
    (6, 0): "11A",  # F#/Gb minor
    (7, 0): "6A",   # G minor
    (8, 0): "1A",   # G#/Ab minor
    (9, 0): "8A",   # A minor
    (10, 0): "3A",  # A#/Bb minor
    (11, 0): "10A", # B minor
}

# Reverse map: Camelot string → (number, letter)
def _parse_camelot(code: str) -> tuple[int, str] | None:
    if not code or code == "?":
        return None
    letter = code[-1].upper()
    try:
        number = int(code[:-1])
        return (number, letter)
    except ValueError:
        return None


def spotify_key_to_camelot(key: int, mode: int) -> str:
    """Convert Spotify key (0-11) and mode (0/1) to Camelot notation."""
    return CAMELOT_MAP.get((key, mode), "?")


def camelot_score(a: str, b: str) -> tuple[float, str]:
    """
    Score harmonic compatibility between two Camelot keys.

    Returns:
        (score: float, label: str)
        score: 0.0 (worst) to 1.0 (best)
        label: human-readable compatibility description
    """
    pa = _parse_camelot(a)
    pb = _parse_camelot(b)

    if pa is None or pb is None:
        return (0.3, "Unknown key")

    num_a, let_a = pa
    num_b, let_b = pb

    # Same key — perfect
    if num_a == num_b and let_a == let_b:
        return (1.0, "Perfect match (same key)")

    # Same number, opposite letter — relative major/minor swap
    if num_a == num_b and let_a != let_b:
        return (0.8, "Compatible — relative key")

    # Adjacent number on the wheel (±1, same letter) — energy shift
    diff = (num_b - num_a) % 12
    if diff <= 1 or diff >= 11:
        if let_a == let_b:
            return (0.9, "Compatible — energy shift")
        else:
            return (0.6, "Moderate — adjacent + key switch")

    # 2 steps away on wheel
    if diff <= 2 or diff >= 10:
        return (0.5, "Moderate — 2 steps away")

    # Dominant relationship (7 semitones, e.g. C major → G major)
    if diff == 7 and let_a == let_b:
        return (0.55, "Compatible — dominant relationship")

    return (0.2, "Avoid — key clash")
