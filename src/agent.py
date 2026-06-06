"""核心：LangGraph 状态机（核心要素：状态管理与多步骤推理）。

把原仓库的"线性单次脚本"重写成一个有状态、可观测、带条件分支的 Agent：

    recall ──► compose ──► resolve ──┬─(有 Spotify token & uri)─► publish ──► remember ──► END
                                     └─(无 token，纯生成)──────────────────► remember ──► END

每个节点是一步推理 / 一次工具调用，状态在节点间流转。
"""
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END

from . import llm, memory, tools
from . import observability as obs


class MoodState(TypedDict, total=False):
    # 输入
    mood_description: str
    num_songs: int
    user_id: str
    spotify_token: Optional[str]
    # 中间 / 输出
    history_context: str
    playlist_name: str
    songs: List[dict]
    spotify_playlist_url: Optional[str]
    error: Optional[str]


@obs.node
def recall(state: MoodState) -> dict:
    """从记忆库取该用户历史偏好。"""
    ctx = memory.load_user_context(state.get("user_id", "anon"))
    return {"history_context": ctx}


@obs.node
def compose(state: MoodState) -> dict:
    """一次结构化 LLM 调用，产出歌单名 + 候选曲目（结合历史偏好）。"""
    n = int(state.get("num_songs", 10))
    system = (
        "你是资深音乐策展人。根据用户心情给出贴合的真实存在的歌曲，"
        "兼顾多样性，尽量给出歌手与歌名。"
    )
    user = (
        f"心情描述：{state['mood_description']}\n"
        f"歌曲数量：{n}\n"
        f"{state.get('history_context', '')}\n\n"
        '请只返回 JSON：{"playlist_name": "歌单名", '
        '"songs": [{"name": "歌名", "artist": "歌手"}, ...]}'
    )
    data = llm.chat_json(system, user)
    songs = data.get("songs", [])[:n]
    return {
        "playlist_name": data.get("playlist_name", "Mood Mix"),
        "songs": songs,
    }


@obs.node
def resolve(state: MoodState) -> dict:
    """有 Spotify token 时，把候选曲目解析成真实 track（拿 uri）；否则原样保留。"""
    token = state.get("spotify_token")
    if not token:
        return {}
    resolved = []
    for s in state.get("songs", []):
        q = f"{s.get('artist', '')} {s.get('name', '')}".strip()
        try:
            hits = tools.search_tracks(q, token, limit=1)
            if hits:
                resolved.append({**s, "uri": hits[0]["uri"],
                                 "album_image": hits[0].get("album_image")})
            else:
                resolved.append(s)
        except Exception as e:  # 工具失败不应中断整个 agent（生产级容错）
            obs.log_event("resolve_error", query=q, error=str(e))
            resolved.append(s)
    return {"songs": resolved}


@obs.node
def publish(state: MoodState) -> dict:
    """把解析好的曲目写成真实 Spotify 歌单。"""
    token = state["spotify_token"]
    uris = [s["uri"] for s in state.get("songs", []) if s.get("uri")]
    try:
        url = tools.create_playlist(
            state.get("playlist_name", "Mood Mix"),
            f"Generated for mood: {state['mood_description']}",
            uris, token,
        )
        return {"spotify_playlist_url": url}
    except Exception as e:
        obs.log_event("publish_error", error=str(e))
        return {"spotify_playlist_url": None, "error": str(e)}


@obs.node
def remember(state: MoodState) -> dict:
    """把本次结果写入记忆库，供下次个性化。"""
    memory.save_interaction(
        state.get("user_id", "anon"),
        state.get("mood_description", ""),
        state.get("playlist_name", ""),
        state.get("songs", []),
    )
    return {}


def _route_after_resolve(state: MoodState) -> str:
    token = state.get("spotify_token")
    has_uri = any(s.get("uri") for s in state.get("songs", []))
    return "publish" if (token and has_uri) else "remember"


def build_graph():
    g = StateGraph(MoodState)
    g.add_node("recall", recall)
    g.add_node("compose", compose)
    g.add_node("resolve", resolve)
    g.add_node("publish", publish)
    g.add_node("remember", remember)

    g.set_entry_point("recall")
    g.add_edge("recall", "compose")
    g.add_edge("compose", "resolve")
    g.add_conditional_edges("resolve", _route_after_resolve,
                            {"publish": "publish", "remember": "remember"})
    g.add_edge("publish", "remember")
    g.add_edge("remember", END)
    return g.compile()


GRAPH = build_graph()


def run_agent(mood_description: str, num_songs: int = 10,
              user_id: str = "anon", spotify_token: Optional[str] = None) -> dict:
    """对外统一入口。"""
    obs.log_event("agent_run", user_id=user_id, mood=mood_description,
                  spotify=bool(spotify_token))
    final = GRAPH.invoke({
        "mood_description": mood_description,
        "num_songs": num_songs,
        "user_id": user_id,
        "spotify_token": spotify_token,
    })
    return {
        "playlist_name": final.get("playlist_name"),
        "songs": final.get("songs", []),
        "spotify_playlist_url": final.get("spotify_playlist_url"),
        "personalized": bool(final.get("history_context")),
        "error": final.get("error"),
    }
