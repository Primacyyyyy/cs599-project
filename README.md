# Mood Agent · 心情驱动的 Agentic 音乐歌单系统

## 项目简介
用一句自然语言描述心情，由 Agent 自动完成"理解情绪 → 生成歌单 → （可选）落地到 Spotify → 记住口味"的完整闭环。解决传统歌单生成听不懂情绪、不记得用户、无多步推理的问题。

## 方向
方向一：Agentic AI 原生开发（在开源项目基础上重构为 Agentic 系统）

## 技术栈
- AI IDE: Trae CN
- LLM: DeepSeek API（`deepseek-chat`，OpenAI 兼容）
- Agent 框架: LangGraph
- 协议: MCP（`mcp_server.py` 暴露音乐工具）、Function Calling
- 服务: FastAPI + Uvicorn
- 记忆: SQLite
- 容器: Docker

## 目录结构
```
cs599-project/
├── src/
│   ├── config.py        # 配置与特性开关
│   ├── llm.py           # DeepSeek 接入层
│   ├── memory.py        # SQLite 跨会话记忆
│   ├── tools.py         # Spotify 工具（search / create-playlist）
│   ├── agent.py         # LangGraph 状态机（核心）
│   ├── observability.py # 结构化日志 + tracing
│   └── api.py           # FastAPI 服务
├── mcp_server.py        # MCP server（暴露音乐工具）
├── selftest.py          # 离线自测（mock LLM，无需 key/外网）
├── docs/                # Product / Architecture / API 三份 Spec
├── Dockerfile
├── requirements.txt
├── .env.example
└── LICENSE / NOTICE
```

## 环境搭建
1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
2. 配置环境变量（**不硬编码 key**）
   ```bash
   cp .env.example .env
   # 编辑 .env，至少填入 DEEPSEEK_API_KEY；Spotify 可留空
   ```
3. 启动服务
   ```bash
   uvicorn src.api:app --reload --port 8888
   ```
4. 调用（无需 Spotify）
   ```bash
   curl -X POST "http://localhost:8888/generate" \
     -H "Content-Type: application/json" \
     -d '{"mood_description":"雨夜赶due的专注背景乐","num_songs":8,"user_id":"stu_2025"}'
   ```
5. （可选）离线验证编排逻辑：`python selftest.py`
6. （可选）启动 MCP server：`python mcp_server.py`

## 项目状态
- [x] Proposal
- [x] MVP（心情→歌单核心闭环、记忆、可观测，已离线自测通过）
- [ ] Final（多智能体 / Agentic RAG / 云部署）

## 学生信息
- 学号：2025303043
- 姓名：许锦瀚
- 专业：软件工程
- 指导教师：戚欣
