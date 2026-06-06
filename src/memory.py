"""跨会话记忆（核心要素：记忆机制）。

用 SQLite 记录每个用户历史心情 + 生成过的歌单，
下次为同一用户生成时，把历史作为上下文喂给 LLM，
实现"记住口味"的个性化推荐（这是原仓库完全没有的能力）。
"""
import os
import sqlite3
import json
import time

from .config import settings


def _conn():
    os.makedirs(os.path.dirname(os.path.abspath(settings.DB_PATH)), exist_ok=True)
    c = sqlite3.connect(settings.DB_PATH)
    c.execute(
        """CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            mood TEXT,
            playlist_name TEXT,
            songs_json TEXT,
            ts REAL
        )"""
    )
    return c


def save_interaction(user_id: str, mood: str, playlist_name: str, songs: list):
    c = _conn()
    c.execute(
        "INSERT INTO interactions (user_id, mood, playlist_name, songs_json, ts) VALUES (?,?,?,?,?)",
        (user_id, mood, playlist_name, json.dumps(songs, ensure_ascii=False), time.time()),
    )
    c.commit()
    c.close()


def load_user_context(user_id: str, limit: int = 5) -> str:
    """把该用户最近的历史拼成一段可读上下文，供 LLM 参考。"""
    c = _conn()
    rows = c.execute(
        "SELECT mood, playlist_name, songs_json FROM interactions WHERE user_id=? ORDER BY ts DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    c.close()
    if not rows:
        return ""
    lines = ["该用户的历史偏好（仅供参考，可据此微调风格，避免重复推荐相同歌曲）："]
    for mood, name, songs_json in rows:
        try:
            songs = json.loads(songs_json)
            sample = ", ".join(f"{s.get('artist','')}-{s.get('name','')}" for s in songs[:3])
        except Exception:
            sample = ""
        lines.append(f"- 心情「{mood}」→ 歌单《{name}》（如：{sample}）")
    return "\n".join(lines)


def get_history(user_id: str, limit: int = 20) -> list:
    c = _conn()
    rows = c.execute(
        "SELECT mood, playlist_name, songs_json, ts FROM interactions WHERE user_id=? ORDER BY ts DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    c.close()
    out = []
    for mood, name, songs_json, ts in rows:
        out.append({
            "mood": mood,
            "playlist_name": name,
            "songs": json.loads(songs_json) if songs_json else [],
            "ts": ts,
        })
    return out
