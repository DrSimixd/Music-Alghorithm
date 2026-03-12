"""
Output formatting: Rich CLI display and JSON export.

Renders per-transition data in a format that mirrors Spotify's
"Edit Transition" UI fields.
"""

import json
from models import Track, TransitionData
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text

console = Console()


def _score_color(score: float) -> str:
    if score >= 0.8:
        return "green"
    elif score >= 0.5:
        return "yellow"
    return "red"


def _format_mixout(t: TransitionData) -> str:
    if t.mixout_time_sec < 0:
        return "N/A"
    total_sec = int(t.mixout_time_sec)
    m = total_sec // 60
    s = total_sec % 60
    if t.mixout_bar >= 0:
        return f"{m}:{s:02d} (bar {t.mixout_bar})"
    return f"{m}:{s:02d}"


def print_tracklist(tracks: list[Track]) -> None:
    """Print the reordered tracklist as a numbered table."""
    table = Table(
        title="Optimized Playlist Order",
        box=box.ROUNDED,
        show_lines=False,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", no_wrap=True, max_width=38)
    table.add_column("Artist", no_wrap=True, max_width=22)
    table.add_column("BPM", justify="right", width=7)
    table.add_column("Key", width=5)
    table.add_column("Energy", justify="right", width=7)
    table.add_column("Duration", justify="right", width=8)

    for i, t in enumerate(tracks, 1):
        energy_str = f"{t.energy:.2f}"
        table.add_row(
            str(i),
            t.title,
            t.artist,
            f"{t.bpm:.0f}",
            t.camelot,
            energy_str,
            t.duration_str,
        )

    console.print()
    console.print(table)
    console.print()


def print_transitions(transitions: list[TransitionData]) -> None:
    """Print each transition as a panel matching Spotify's Edit Transition UI."""
    console.print()
    console.rule("[bold cyan]Transition Guide[/bold cyan]")
    console.print()

    for i, t in enumerate(transitions, 1):
        score_pct = int(t.compatibility_score * 100)
        color = _score_color(t.compatibility_score)
        halftime_note = " [yellow](half-time)[/yellow]" if t.halftime_compatible else ""

        # Build panel content
        lines = []

        # Track A
        lines.append(
            f"[bold]Track {i}:[/bold]  [white]{t.track_a.title}[/white]  —  {t.track_a.artist}"
        )
        lines.append(
            f"          [cyan]{t.track_a.bpm:.0f} BPM[/cyan]  [magenta]{t.track_a.camelot}[/magenta]"
            f"  Energy {t.track_a.energy:.2f}  {t.track_a.duration_str}"
        )
        mixout = _format_mixout(t)
        if mixout != "N/A":
            lines.append(f"          [dim]Mix-out: {mixout}[/dim]")

        lines.append("")

        # Track B
        lines.append(
            f"[bold]Track {i+1}:[/bold]  [white]{t.track_b.title}[/white]  —  {t.track_b.artist}"
        )
        lines.append(
            f"          [cyan]{t.track_b.bpm:.0f} BPM[/cyan]  [magenta]{t.track_b.camelot}[/magenta]"
            f"  Energy {t.track_b.energy:.2f}  {t.track_b.duration_str}"
        )

        lines.append("")

        # Compatibility summary
        lines.append(
            f"[bold]Compatibility:[/bold]  [{color}]{score_pct}/100[/{color}]"
            f"  {t.key_compatibility}  ΔBPM={t.bpm_diff:.1f}{halftime_note}"
        )

        lines.append("")

        # Transition settings (Spotify UI fields)
        lines.append(
            f"[bold]Transition:[/bold]    {t.transition_bars} bars  ({t.transition_sec:.1f} sec)"
        )
        lines.append(f"  Volume   [green]{t.volume_type}[/green]")
        lines.append(f"  EQ       [green]{t.eq}[/green]")
        lines.append(f"  Filter   [green]{t.filter_type}[/green]")
        lines.append(f"  Style    [green]{t.style}[/green]")

        panel = Panel(
            "\n".join(lines),
            title=f"[bold]Transition {i} → {i+1}[/bold]",
            border_style=color,
            expand=True,
        )
        console.print(panel)
        console.print()


def save_json(transitions: list[TransitionData], path: str) -> None:
    """Export all transition data to a JSON file."""
    data = [t.to_dict() for t in transitions]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    console.print(f"[dim]Saved JSON to {path}[/dim]")
