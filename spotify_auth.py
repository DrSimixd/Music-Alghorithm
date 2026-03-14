"""
Spotify OAuth 2.0 Authorization Code Flow for web applications.

Handles the browser-based "Log in with Spotify" flow so end-users
never need their own CLIENT_ID / CLIENT_SECRET.  The app owner's
credentials live server-side in environment variables.
"""

import os
import urllib.parse

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Scopes needed: read playlists + create/modify playlists for "Save to Spotify"
_SCOPES = (
    "playlist-read-private "
    "playlist-read-collaborative "
    "playlist-modify-public "
    "playlist-modify-private"
)


def get_auth_manager(redirect_uri: str, cache_path: str = ".cache-web") -> SpotifyOAuth:
    """
    Build a SpotifyOAuth manager using server-side app credentials.

    Args:
        redirect_uri: The OAuth callback URL (must match Spotify dashboard setting).
        cache_path: Where to store the token cache file.

    Returns:
        A SpotifyOAuth instance ready for the Authorization Code Flow.
    """
    return SpotifyOAuth(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=redirect_uri,
        scope=_SCOPES,
        cache_path=cache_path,
        show_dialog=True,
    )


def get_authorize_url(auth_manager: SpotifyOAuth) -> str:
    """Return the Spotify authorization URL the user should visit."""
    return auth_manager.get_authorize_url()


def exchange_code(auth_manager: SpotifyOAuth, code: str) -> dict:
    """
    Exchange an authorization code for an access token.

    Args:
        auth_manager: The SpotifyOAuth instance.
        code: The authorization code from Spotify's redirect.

    Returns:
        Token info dict with access_token, refresh_token, expires_at, etc.
    """
    return auth_manager.get_access_token(code, as_dict=True)


def get_spotify_client(token_info: dict) -> spotipy.Spotify:
    """
    Build a Spotify client from an existing token dict.

    Args:
        token_info: Dict containing at minimum 'access_token'.

    Returns:
        An authenticated spotipy.Spotify client.
    """
    return spotipy.Spotify(auth=token_info["access_token"])


def create_playlist(
    sp: spotipy.Spotify,
    user_id: str,
    name: str,
    track_ids: list[str],
    description: str = "",
) -> str:
    """
    Create a new playlist in the user's Spotify account and populate it.

    Args:
        sp: Authenticated Spotify client.
        user_id: The Spotify user ID.
        name: Playlist name.
        track_ids: Ordered list of Spotify track IDs.
        description: Optional playlist description.

    Returns:
        The URL of the newly created playlist.
    """
    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=False,
        description=description,
    )
    # Spotify API accepts max 100 tracks per add call
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i : i + 100]
        sp.playlist_add_items(playlist["id"], batch)
    return playlist["external_urls"]["spotify"]


def extract_code_from_url(url: str) -> str | None:
    """Extract the 'code' query parameter from a callback URL."""
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    codes = params.get("code")
    return codes[0] if codes else None
