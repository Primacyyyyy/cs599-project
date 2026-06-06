"""离线自测：用假的 LLM 替换真实调用，验证整条 LangGraph 流程能跑通
（含状态流转、条件分支、记忆读写），无需任何 API key 或外网。

真实使用时不需要这个文件，它只是验证编排逻辑正确。
运行： python selftest.py
"""
import os
import tempfile

# 用临时数据库，避免污染 data/memory.db
os.environ["DB_PATH"] = os.path.join(tempfile.gettempdir(), "selftest_memory.db")
if os.path.exists(os.environ["DB_PATH"]):
    os.remove(os.environ["DB_PATH"])

import src.llm as llm

# --- 替换真实 DeepSeek 调用为固定返回 ---
_FAKE = {
    "late night rainy coding focus": {
        "playlist_name": "Rainy Night Code",
        "songs": [
            {"name": "Weightless", "artist": "Marconi Union"},
            {"name": "Intro", "artist": "The xx"},
            {"name": "Nightcall", "artist": "Kavinsky"},
        ],
    },
    "default": {
        "playlist_name": "Bright Morning",
        "songs": [
            {"name": "Lovely Day", "artist": "Bill Withers"},
            {"name": "Here Comes the Sun", "artist": "The Beatles"},
        ],
    },
}


def fake_chat_json(system, user, model=None):
    for key, val in _FAKE.items():
        if key != "default" and key in user:
            return val
    return _FAKE["default"]


llm.chat_json = fake_chat_json  # monkeypatch

from src.agent import run_agent
from src import memory


def main():
    print("\n===== 第 1 次：新用户，无 Spotify token（MVP 核心闭环）=====")
    r1 = run_agent("late night rainy coding focus", num_songs=3, user_id="stu_2025")
    print("歌单名:", r1["playlist_name"])
    print("歌曲:", [f"{s['artist']} - {s['name']}" for s in r1["songs"]])
    print("个性化(用到历史)?", r1["personalized"])
    print("Spotify 链接:", r1["spotify_playlist_url"], "(无 token 时为 None，符合预期)")

    print("\n===== 第 2 次：同一用户再来，应能读到上一次的记忆 =====")
    r2 = run_agent("happy morning", num_songs=2, user_id="stu_2025")
    print("歌单名:", r2["playlist_name"])
    print("个性化(用到历史)?", r2["personalized"], "<- 应为 True，证明跨会话记忆生效")

    print("\n===== 记忆库内容 =====")
    for h in memory.get_history("stu_2025"):
        print(f"  心情「{h['mood']}」→《{h['playlist_name']}》，{len(h['songs'])} 首")

    assert r1["playlist_name"] == "Rainy Night Code"
    assert len(r1["songs"]) == 3
    assert r2["personalized"] is True, "第二次应读到记忆"
    print("\n✅ 全部断言通过：LangGraph 编排 / 条件分支 / 跨会话记忆 均正常。")


if __name__ == "__main__":
    main()
