"""Spotify 工具集（工具使用 / Function Calling 的具体工具）。

注意：只使用 search 和 create-playlist 端点——这两个在 2024-11-27
Spotify 端点收紧后对新应用仍然可用；被砍掉的 recommendations /
audio-features 等一律没用到，因此新建 Spotify app 也能跑通。

这些函数同时被：
  1) LangGraph agent 的节点直接编排调用；
  2) MCP server（mcp_server.py）暴露为标准 MCP 工具。
"""
import base64
import json
import requests

from .config import settings

SPOTIFY_API = "https://api.spotify.com/v1"
SPOTIFY_ACCOUNTS = "https://accounts.spotify.com"


def get_auth_url() -> str:
    scope = "playlist-modify-private playlist-modify-public user-read-private"
    return (
        f"{SPOTIFY_ACCOUNTS}/authorize?client_id={settings.SPOTIFY_CLIENT_ID}"
        f"&response_type=code&redirect_uri={settings.REDIRECT_URI}&scope={scope}"
    )


def exchange_code(auth_code: str) -> dict:
    auth_header = base64.b64encode(
        f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}".encode()
    ).decode()
    resp = requests.post(
        f"{SPOTIFY_ACCOUNTS}/api/token",
        headers={
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": settings.REDIRECT_URI,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def search_tracks(query: str, token: str, limit: int = 5) -> list:
    """搜索曲目，返回 [{name, artist, uri, album_image}]。"""
    token = (token or "").strip().strip('"')
    resp = requests.get(
        f"{SPOTIFY_API}/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query, "type": "track", "limit": limit},
        timeout=15,
    )
    resp.raise_for_status()
    items = resp.json().get("tracks", {}).get("items", [])
    out = []
    for it in items:
        images = it.get("album", {}).get("images", [])
        out.append({
            "name": it["name"],
            "artist": ", ".join(a["name"] for a in it["artists"]),
            "uri": it["uri"],
            "album_image": images[0]["url"] if images else None,
        })
    return out


def create_playlist(name: str, description: str, track_uris: list, token: str) -> str:
    """新建歌单并加入曲目，返回 Spotify 歌单链接。"""
    token = (token or "").strip().strip('"')
    headers = {"Authorization": f"Bearer {token}"}

    me = requests.get(f"{SPOTIFY_API}/me", headers=headers, timeout=15)
    me.raise_for_status()
    user_id = me.json()["id"]

    created = requests.post(
        f"{SPOTIFY_API}/users/{user_id}/playlists",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps({"name": name, "description": description, "public": True}),
        timeout=15,
    )
    created.raise_for_status()
    playlist = created.json()

    if track_uris:
        added = requests.post(
            f"{SPOTIFY_API}/playlists/{playlist['id']}/tracks",
            headers={**headers, "Content-Type": "application/json"},
            data=json.dumps({"uris": track_uris}),
            timeout=15,
        )
        added.raise_for_status()

    return playlist["external_urls"]["spotify"]
