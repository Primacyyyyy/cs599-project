"""MCP Server：把音乐工具按 MCP 协议标准暴露出去（对应加分项 +3）。

任何支持 MCP 的客户端（Claude Desktop、Trae、其它 agent）都能发现并调用
这里的 search_music / create_music_playlist 工具。

运行： python mcp_server.py   （stdio 传输）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from src.tools import search_tracks, create_playlist

mcp = FastMCP("music-tools")


@mcp.tool()
def search_music(query: str, spotify_token: str, limit: int = 5) -> list:
    """在 Spotify 搜索曲目。返回 [{name, artist, uri, album_image}]。"""
    return search_tracks(query, spotify_token, limit)


@mcp.tool()
def create_music_playlist(name: str, description: str,
                          track_uris: list, spotify_token: str) -> str:
    """用给定曲目 uri 新建一个 Spotify 歌单，返回歌单链接。"""
    return create_playlist(name, description, track_uris, spotify_token)


if __name__ == "__main__":
    mcp.run()
