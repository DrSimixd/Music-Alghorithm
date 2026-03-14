"""
DJ software export formats: M3U, Rekordbox XML.

Generates playlist files importable by Rekordbox, Serato, Traktor, and
other DJ software with transition metadata preserved where the format allows.
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from models import Track, TransitionData


def export_m3u(tracks: list[Track], transitions: list[TransitionData]) -> str:
    """
    Export playlist as an Extended M3U file.

    Compatible with: VLC, Serato, Traktor, most media players.
    Includes EXTINF duration and artist/title metadata.
    Transition data is embedded as #EXTREM comments.

    Returns:
        M3U file content as a string.
    """
    lines = ["#EXTM3U", ""]

    for i, track in enumerate(tracks):
        duration_sec = track.duration_ms // 1000
        lines.append(f"#EXTINF:{duration_sec},{track.artist} - {track.title}")

        # Embed transition data as a comment (non-standard but harmless)
        if i < len(transitions):
            t = transitions[i]
            lines.append(
                f"#EXTREM:transition_bars={t.transition_bars},"
                f"volume={t.volume_type},"
                f"style={t.style},"
                f"score={t.compatibility_score:.2f}"
            )

        # Use Spotify URI as the track reference
        lines.append(f"spotify:track:{track.id}")
        lines.append("")

    return "\n".join(lines)


def export_rekordbox_xml(
    tracks: list[Track],
    transitions: list[TransitionData],
    playlist_name: str = "DJ Mix",
) -> str:
    """
    Export playlist as Rekordbox-compatible XML.

    Follows the Rekordbox XML format specification for importing
    playlists with track metadata (BPM, key, energy).

    Returns:
        XML file content as a string.
    """
    root = ET.Element("DJ_PLAYLISTS", Version="1.0.0")

    product = ET.SubElement(root, "PRODUCT")
    product.set("Name", "Music-Algorithm")
    product.set("Version", "1.0.0")
    product.set("Company", "Music-Algorithm")

    collection = ET.SubElement(root, "COLLECTION", Entries=str(len(tracks)))

    for i, track in enumerate(tracks):
        attrs = {
            "TrackID": str(i + 1),
            "Name": track.title,
            "Artist": track.artist,
            "TotalTime": str(track.duration_ms // 1000),
            "AverageBpm": f"{track.bpm:.2f}",
            "Tonality": track.camelot,
            "Kind": "Spotify",
            "Location": f"spotify:track:{track.id}",
        }
        track_elem = ET.SubElement(collection, "TRACK", **attrs)

        # Embed energy as a custom tag (Rekordbox ignores unknown tags gracefully)
        ET.SubElement(track_elem, "ENERGY", Value=f"{track.energy:.3f}")

        # Embed transition data for the next track
        if i < len(transitions):
            t = transitions[i]
            ET.SubElement(
                track_elem,
                "TRANSITION",
                Bars=str(t.transition_bars),
                Seconds=f"{t.transition_sec:.2f}",
                Volume=t.volume_type,
                EQ=t.eq,
                Filter=t.filter_type,
                Style=t.style,
                Score=f"{t.compatibility_score:.2f}",
            )

    # Playlist node
    playlists = ET.SubElement(root, "PLAYLISTS")
    node = ET.SubElement(
        playlists, "NODE", Type="1", Name="ROOT", Count="1"
    )
    playlist_node = ET.SubElement(
        node,
        "NODE",
        Name=playlist_name,
        Type="1",
        KeyType="0",
        Entries=str(len(tracks)),
    )
    for i in range(len(tracks)):
        ET.SubElement(playlist_node, "TRACK", Key=str(i + 1))

    # Pretty-print
    rough = ET.tostring(root, encoding="unicode", xml_declaration=False)
    parsed = minidom.parseString(rough)
    return parsed.toprettyxml(indent="  ", encoding=None)


def export_json(transitions: list[TransitionData]) -> str:
    """Export transition data as formatted JSON."""
    data = [t.to_dict() for t in transitions]
    return json.dumps(data, indent=2, ensure_ascii=False)
