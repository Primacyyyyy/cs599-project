# API Spec · Mood Agent

Base URL: `http://localhost:8888`

## GET /health
健康检查与能力探测。
```json
{ "status": "ok", "llm_ready": true, "spotify_enabled": false }
```

## POST /generate
核心端点。根据心情生成歌单。**无需 Spotify token 也可调用。**

Query（可选）：`spotify_token` —— 传入后会解析真实曲目并落地为 Spotify 歌单。

Request body：
```json
{ "mood_description": "雨夜赶due需要的专注背景乐", "num_songs": 10, "user_id": "stu_2025" }
```
Response：
```json
{
  "playlist_name": "Rainy Night Code",
  "songs": [
    { "name": "Weightless", "artist": "Marconi Union", "uri": null, "album_image": null }
  ],
  "spotify_playlist_url": null,
  "personalized": false
}
```
- `personalized=true` 表示本次推荐参考了该用户历史记忆。
- 配置并传入 `spotify_token` 后，`songs[].uri` 会被填充，`spotify_playlist_url` 返回真实链接。

## GET /memory/{user_id}
查看某用户的历史记忆（演示记忆机制）。
```json
{ "user_id": "stu_2025", "history": [ { "mood": "...", "playlist_name": "...", "songs": [], "ts": 0 } ] }
```

## GET /auth-url
（需配置 Spotify）返回 Spotify 授权 URL。

## POST /token
（需配置 Spotify）用授权 code 换 access token。
Request：`{ "code": "..." }`

## MCP 工具（通过 mcp_server.py 暴露）
| 工具 | 入参 | 返回 |
| --- | --- | --- |
| `search_music` | query, spotify_token, limit | 曲目列表 |
| `create_music_playlist` | name, description, track_uris, spotify_token | 歌单链接 |
