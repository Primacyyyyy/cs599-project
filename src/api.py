"""FastAPI 服务层：对外暴露 agent。

核心端点 /generate 不需要 Spotify token 也能跑通（MVP 核心闭环）；
配了 Spotify 后，传 token 即可顺带生成真实歌单。
"""
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agent import run_agent
from .config import settings
from . import tools, memory
from . import observability as obs

obs.setup_logging()
app = FastAPI(title="Mood Agent · CS599",
              description="基于 mood-playlist-ai 改造的 Agentic 音乐歌单系统")


class MoodRequest(BaseModel):
    mood_description: str
    num_songs: int = 10
    user_id: str = "anon"


class Song(BaseModel):
    name: str
    artist: str
    uri: Optional[str] = None
    album_image: Optional[str] = None


class PlaylistResponse(BaseModel):
    playlist_name: str
    songs: List[Song]
    spotify_playlist_url: Optional[str] = None
    personalized: bool = False


class AuthRequest(BaseModel):
    code: str


@app.get("/health")
def health():
    return {"status": "ok", "llm_ready": settings.llm_ready,
            "spotify_enabled": settings.spotify_enabled}


@app.post("/generate", response_model=PlaylistResponse)
def generate(req: MoodRequest, spotify_token: Optional[str] = None):
    """根据心情生成歌单。spotify_token 可选——不传则只返回 LLM 歌单（MVP）。"""
    if not settings.llm_ready:
        raise HTTPException(500, "DEEPSEEK_API_KEY 未配置")
    result = run_agent(req.mood_description, req.num_songs, req.user_id, spotify_token)
    return PlaylistResponse(
        playlist_name=result["playlist_name"] or "Mood Mix",
        songs=[Song(**s) for s in result["songs"]],
        spotify_playlist_url=result.get("spotify_playlist_url"),
        personalized=result.get("personalized", False),
    )


@app.get("/memory/{user_id}")
def view_memory(user_id: str):
    """查看某用户的历史记忆（演示记忆机制）。"""
    return {"user_id": user_id, "history": memory.get_history(user_id)}


@app.get("/auth-url")
def auth_url():
    if not settings.spotify_enabled:
        raise HTTPException(400, "未配置 Spotify 凭据（可选功能）")
    return {"auth_url": tools.get_auth_url()}


@app.post("/token")
def token(req: AuthRequest):
    if not settings.spotify_enabled:
        raise HTTPException(400, "未配置 Spotify 凭据（可选功能）")
    try:
        return tools.exchange_code(req.code)
    except Exception as e:
        raise HTTPException(400, str(e))
