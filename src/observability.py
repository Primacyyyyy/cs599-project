"""可观测性：结构化日志 + LangGraph 节点级 tracing 装饰器。

每个 agent 节点的进入/退出/耗时都会打成一行结构化日志，
便于演示"Agent 行为评估"，也是生产级要素之一。
"""
import json
import logging
import time
import functools

from .config import settings

logger = logging.getLogger("music_agent")


def setup_logging():
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(settings.LOG_LEVEL)
    logger.propagate = False


def log_event(event: str, **fields):
    setup_logging()
    logger.info(json.dumps({"event": event, **fields}, ensure_ascii=False))


def node(fn):
    """装饰 LangGraph 节点：自动记录开始、结束、耗时。"""
    @functools.wraps(fn)
    def wrapper(state):
        t0 = time.time()
        log_event("node_start", node=fn.__name__)
        out = fn(state)
        log_event("node_end", node=fn.__name__,
                  ms=round((time.time() - t0) * 1000, 1),
                  updates=list(out.keys()) if isinstance(out, dict) else None)
        return out
    return wrapper
