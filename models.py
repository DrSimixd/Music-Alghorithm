from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Track:
    id: str
    title: str
    artist: str
    duration_ms: int
    bpm: float              # audio_features.tempo
    key: int                # Spotify pitch class (0=C … 11=B), -1 if unknown
    mode: int               # 0=minor, 1=major
    camelot: str            # e.g. "4B", "11A", "?" if key unknown
    energy: float           # 0.0–1.0
    danceability: float     # 0.0–1.0
    loudness: float         # dB (typically -60 to 0)
    valence: float          # 0.0–1.0 (sad → happy)
    # Optional — populated when --fast is NOT used
    sections: list[dict] = field(default_factory=list)
    beats: list[dict] = field(default_factory=list)

    @property
    def duration_str(self) -> str:
        total_sec = self.duration_ms // 1000
        minutes = total_sec // 60
        seconds = total_sec % 60
        return f"{minutes}:{seconds:02d}"


@dataclass
class TransitionData:
    track_a: Track
    track_b: Track
    bpm_diff: float
    halftime_compatible: bool       # True if one BPM ≈ 2× the other
    key_compatibility: str          # "Perfect" | "Compatible" | "Moderate" | "Avoid"
    compatibility_score: float      # 0.0–1.0
    # Transition timing
    mixout_time_sec: float          # seconds into track_a to start fading (-1 if unknown)
    mixout_bar: int                 # same as above, in bars (-1 if unknown)
    transition_bars: int            # 2 | 4 | 8 | 16
    transition_sec: float           # transition_bars × (4 × 60 / avg_bpm)
    # Spotify "Edit Transition" UI fields
    volume_type: str                # "Overlap" | "Fade" | "Rise" | "Blend"
    eq: str                         # "None" | "Bass cut"
    filter_type: str                # "None" | "High-pass" | "Low-pass"
    style: str                      # "Auto" | "Fade" | "Rise" | "Blend"

    def to_dict(self) -> dict:
        return {
            "track_a": {
                "title": self.track_a.title,
                "artist": self.track_a.artist,
                "bpm": round(self.track_a.bpm, 1),
                "camelot": self.track_a.camelot,
                "energy": round(self.track_a.energy, 3),
                "duration": self.track_a.duration_str,
            },
            "track_b": {
                "title": self.track_b.title,
                "artist": self.track_b.artist,
                "bpm": round(self.track_b.bpm, 1),
                "camelot": self.track_b.camelot,
                "energy": round(self.track_b.energy, 3),
                "duration": self.track_b.duration_str,
            },
            "compatibility": {
                "score": round(self.compatibility_score * 100),
                "key": self.key_compatibility,
                "bpm_diff": round(self.bpm_diff, 1),
                "halftime": self.halftime_compatible,
            },
            "transition": {
                "bars": self.transition_bars,
                "seconds": round(self.transition_sec, 2),
                "mixout_time": round(self.mixout_time_sec, 2) if self.mixout_time_sec >= 0 else None,
                "mixout_bar": self.mixout_bar if self.mixout_bar >= 0 else None,
                "volume": self.volume_type,
                "eq": self.eq,
                "filter": self.filter_type,
                "style": self.style,
            },
        }
