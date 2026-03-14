"""
Music-Algorithm Web UI — Streamlit application.

Replaces the CLI interface with a browser-based UI that includes:
  - Phase 1: Clean web interface (paste a playlist URL)
  - Phase 2: One-click Spotify OAuth login
  - Phase 3: "Save to my Spotify" button
  - Phase 4: DJ export formats (JSON, M3U, Rekordbox XML)
  - Phase 5: Energy arc visualization (BPM + energy line charts)

Usage:
    streamlit run app.py
"""

import os
from urllib.parse import urlencode

import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from spotify_auth import (
    create_playlist,
    exchange_code,
    extract_code_from_url,
    get_auth_manager,
    get_authorize_url,
    get_spotify_client,
)
from spotify_client import fetch_playlist
from ordering import order_tracks
from mixer import build_transitions
from exporters import export_json, export_m3u, export_rekordbox_xml


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Music Algorithm — DJ Transition Optimizer",
    page_icon="🎧",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_redirect_uri() -> str:
    """Build the OAuth redirect URI from the current Streamlit server URL."""
    return os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8501/")


def _score_color(score: float) -> str:
    """Return a hex color for a compatibility score."""
    if score >= 0.8:
        return "#2ecc71"
    if score >= 0.5:
        return "#f1c40f"
    return "#e74c3c"


def _score_emoji(score: float) -> str:
    if score >= 0.8:
        return "🟢"
    if score >= 0.5:
        return "🟡"
    return "🔴"


# ---------------------------------------------------------------------------
# Phase 2 — Spotify OAuth
# ---------------------------------------------------------------------------

def _handle_auth() -> bool:
    """
    Handle the Spotify OAuth flow. Returns True if authenticated.

    Flow:
    1. User clicks "Log in with Spotify" → redirected to Spotify
    2. Spotify redirects back with ?code=... in the URL
    3. We exchange the code for a token and store it in session state
    """
    # Already authenticated?
    if st.session_state.get("spotify_token"):
        return True

    # Check if we're returning from Spotify with an auth code
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        try:
            auth_manager = get_auth_manager(redirect_uri=_get_redirect_uri())
            token_info = exchange_code(auth_manager, code)
            st.session_state["spotify_token"] = token_info
            # Clear the code from the URL
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Authentication failed: {e}")
            return False

    return False


def _show_login():
    """Display the login section."""
    st.markdown("### Connect to Spotify")
    st.markdown(
        "Click the button below to log in with your Spotify account. "
        "This lets us read your playlists and save optimized versions back."
    )
    auth_manager = get_auth_manager(redirect_uri=_get_redirect_uri())
    auth_url = get_authorize_url(auth_manager)
    st.link_button("🎵  Log in with Spotify", auth_url, type="primary")


# ---------------------------------------------------------------------------
# Phase 5 — Energy Arc Visualization
# ---------------------------------------------------------------------------

def _render_energy_chart(tracks):
    """Plot BPM and energy flow across the playlist using Plotly."""
    titles = [f"{i+1}. {t.title[:25]}" for i, t in enumerate(tracks)]
    bpms = [t.bpm for t in tracks]
    energies = [t.energy for t in tracks]
    indices = list(range(1, len(tracks) + 1))

    fig = go.Figure()

    # Energy trace (primary y-axis)
    fig.add_trace(go.Scatter(
        x=indices,
        y=energies,
        name="Energy",
        mode="lines+markers",
        line=dict(color="#1DB954", width=3),
        marker=dict(size=8),
        hovertext=titles,
        hovertemplate="%{hovertext}<br>Energy: %{y:.2f}<extra></extra>",
        yaxis="y",
    ))

    # BPM trace (secondary y-axis)
    fig.add_trace(go.Scatter(
        x=indices,
        y=bpms,
        name="BPM",
        mode="lines+markers",
        line=dict(color="#1E90FF", width=2, dash="dot"),
        marker=dict(size=6),
        hovertext=titles,
        hovertemplate="%{hovertext}<br>BPM: %{y:.0f}<extra></extra>",
        yaxis="y2",
    ))

    fig.update_layout(
        title="Playlist Energy & BPM Flow",
        xaxis=dict(title="Track #", dtick=1),
        yaxis=dict(
            title="Energy (0–1)",
            titlefont=dict(color="#1DB954"),
            range=[0, 1.05],
            side="left",
        ),
        yaxis2=dict(
            title="BPM",
            titlefont=dict(color="#1E90FF"),
            overlaying="y",
            side="right",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        template="plotly_dark",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Phase 1 — Main application UI
# ---------------------------------------------------------------------------

def _run_analysis(playlist_url: str, use_arc: bool, fast: bool):
    """Run the full analysis pipeline and store results in session state."""
    sp = get_spotify_client(st.session_state["spotify_token"])
    status = st.empty()

    def update_status(msg: str):
        status.info(msg)

    # Step 1: Fetch
    update_status("Fetching playlist from Spotify...")
    tracks = fetch_playlist(playlist_url, fast=fast, sp=sp, on_progress=update_status)

    if len(tracks) < 2:
        st.error("Need at least 2 tracks to generate transitions.")
        return

    # Step 2: Reorder
    update_status("Optimizing track order...")
    tracks = order_tracks(tracks, use_arc=use_arc, on_progress=update_status)

    # Step 3: Transitions
    update_status("Generating transition recommendations...")
    transitions = build_transitions(tracks)

    status.success(f"Done! Analyzed {len(tracks)} tracks with {len(transitions)} transitions.")

    # Store in session
    st.session_state["tracks"] = tracks
    st.session_state["transitions"] = transitions


def _render_tracklist(tracks):
    """Render the optimized track list as a Streamlit table."""
    rows = []
    for i, t in enumerate(tracks, 1):
        rows.append({
            "#": i,
            "Title": t.title,
            "Artist": t.artist,
            "BPM": f"{t.bpm:.0f}",
            "Key": t.camelot,
            "Energy": f"{t.energy:.2f}",
            "Duration": t.duration_str,
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_transitions(transitions):
    """Render transitions as expandable cards."""
    for i, t in enumerate(transitions, 1):
        score_pct = int(t.compatibility_score * 100)
        color = _score_color(t.compatibility_score)
        emoji = _score_emoji(t.compatibility_score)
        label = (
            f"{emoji} **{i}→{i+1}** | "
            f"{t.track_a.title[:30]} → {t.track_b.title[:30]} | "
            f"Score: {score_pct}%"
        )
        with st.expander(label):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Track {i}:** {t.track_a.title}")
                st.markdown(
                    f"`{t.track_a.bpm:.0f} BPM` · `{t.track_a.camelot}` · "
                    f"Energy {t.track_a.energy:.2f}"
                )
            with col2:
                st.markdown(f"**Track {i+1}:** {t.track_b.title}")
                st.markdown(
                    f"`{t.track_b.bpm:.0f} BPM` · `{t.track_b.camelot}` · "
                    f"Energy {t.track_b.energy:.2f}"
                )

            st.divider()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Bars", t.transition_bars)
            c2.metric("Volume", t.volume_type)
            c3.metric("Filter", t.filter_type)
            c4.metric("Style", t.style)

            st.caption(
                f"Compatibility: {score_pct}% · {t.key_compatibility} · "
                f"ΔBPM={t.bpm_diff:.1f} · EQ: {t.eq} · "
                f"Transition: {t.transition_sec:.1f}s"
            )


# ---------------------------------------------------------------------------
# Phase 3 & 4 — Save & Export sidebar
# ---------------------------------------------------------------------------

def _render_export_sidebar(tracks, transitions):
    """Render export options in the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Export")

    # Phase 4: DJ export formats
    export_fmt = st.sidebar.radio(
        "Format",
        ["JSON", "M3U (Serato/Traktor)", "Rekordbox XML"],
        index=0,
    )

    if export_fmt == "JSON":
        data = export_json(transitions)
        filename = "transitions.json"
        mime = "application/json"
    elif export_fmt.startswith("M3U"):
        data = export_m3u(tracks, transitions)
        filename = "playlist.m3u"
        mime = "audio/x-mpegurl"
    else:
        data = export_rekordbox_xml(tracks, transitions, "DJ Mix")
        filename = "playlist.xml"
        mime = "application/xml"

    st.sidebar.download_button(
        label=f"Download {export_fmt.split(' ')[0]}",
        data=data,
        file_name=filename,
        mime=mime,
    )

    # Phase 3: Save to Spotify
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Save to Spotify")
    playlist_name = st.sidebar.text_input(
        "New playlist name",
        value="DJ Mix — Optimized",
    )
    if st.sidebar.button("Save to my Spotify", type="primary"):
        try:
            sp = get_spotify_client(st.session_state["spotify_token"])
            user = sp.current_user()
            track_ids = [t.id for t in tracks]
            url = create_playlist(
                sp,
                user["id"],
                playlist_name,
                track_ids,
                description="Optimized by Music-Algorithm for smooth DJ transitions.",
            )
            st.sidebar.success(f"Playlist created!")
            st.sidebar.markdown(f"[Open in Spotify]({url})")
        except Exception as e:
            st.sidebar.error(f"Failed to save: {e}")


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------

def main():
    st.title("🎧 Music Algorithm")
    st.caption("Analyze Spotify playlists and generate DJ-style mixing recommendations")

    # Handle OAuth flow
    is_authenticated = _handle_auth()

    if not is_authenticated:
        st.markdown("---")
        _show_login()
        st.markdown("---")
        st.markdown(
            "#### How it works\n"
            "1. **Log in** with your Spotify account\n"
            "2. **Paste** a playlist URL\n"
            "3. **Get** optimized track order with transition recommendations\n"
            "4. **Save** the optimized playlist back to Spotify or export for DJ software"
        )
        return

    # Authenticated — show the main interface
    st.sidebar.markdown("### Settings")
    user_info = None
    try:
        sp = get_spotify_client(st.session_state["spotify_token"])
        user_info = sp.current_user()
        st.sidebar.success(f"Logged in as **{user_info['display_name']}**")
    except Exception:
        st.sidebar.warning("Session expired. Please log in again.")
        st.session_state.pop("spotify_token", None)
        st.rerun()

    if st.sidebar.button("Log out"):
        st.session_state.clear()
        st.rerun()

    # Analysis options
    use_arc = st.sidebar.checkbox("Energy Arc (buildup → peak → cooldown)", value=False)
    fast_mode = st.sidebar.checkbox("Fast mode (skip detailed analysis)", value=True)

    # Playlist input
    st.markdown("---")
    playlist_url = st.text_input(
        "Spotify Playlist URL",
        placeholder="https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
    )

    if st.button("Analyze Playlist", type="primary", disabled=not playlist_url):
        _run_analysis(playlist_url, use_arc=use_arc, fast=fast_mode)

    # Show results if available
    tracks = st.session_state.get("tracks")
    transitions = st.session_state.get("transitions")

    if tracks and transitions:
        st.markdown("---")

        # Phase 5: Energy arc visualization
        st.markdown("### Energy & BPM Flow")
        _render_energy_chart(tracks)

        # Tracklist
        st.markdown("### Optimized Track Order")
        _render_tracklist(tracks)

        # Transitions
        st.markdown("### Transition Guide")
        _render_transitions(transitions)

        # Export sidebar (Phase 3 & 4)
        _render_export_sidebar(tracks, transitions)


if __name__ == "__main__":
    main()
