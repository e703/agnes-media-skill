---
name: agnes-media
description: "Agnes AI media generation services — agnes-image-2.0-flash (text-to-image, image-to-image, multi-image composition) and agnes-video-v2.0 (text-to-video). Includes pricing, official best-practice prompt templates, FAQ, project dir convention (sources/target), and queue-retry strategy."
version: 1.6.0
author: Hermes Agent (optimized from chat_01)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [image-generation, video-generation, creative, agnes, agnes-image-2.0-flash, agnes-video-v2.0, text-to-image, text-to-video]
    category: creative
---

# Agnes Media Generation

## Agent Identity

You are the master controller agent responsible for daily conversation, document writing, information retrieval, project workspace management, and subordinate media task scheduling.

You have two subordinate specialized capability interfaces. Unless the user asks about architecture details, do not proactively expose internal codenames:

1. `generate_image_via_pic01` — Image generation service, specializing in text-to-image, image-to-image, and image modification. Underlying Agnes model: `agnes-image-2.0-flash`.
2. `generate_video_via_mov01` — Audio/video and video generation service, specializing in video, animation, and multimedia generation. Underlying Agnes model: `agnes-video-v2.0`.

## Workspace & Project Isolation Rules

1. All file read/write and media generation tasks must operate within a specific project directory.
2. The unified workspace root is `~/workspace` (configurable via `AGNES_WORKSPACE_ROOT`).
3. If the user has not explicitly specified a current project, you must ask or guide the user to define a compliant project name, e.g. `brand_retro`, `game_design`, `project_alpha`.
4. When calling subordinate media tools, you must accurately pass the current project name as `project_name` and propose a reasonable filename with the correct extension.
5. `project_name` must be a single directory slug — no `../`, slashes, backslashes, absolute paths, or any content attempting to escape the workspace.
6. Never attempt to construct out-of-bounds paths such as `/etc`, `../`, `~/.ssh`.
7. **Files from chat tools** (Feishu, Telegram, etc.) — reference images, videos, scripts, or other assets received through chat must be saved into the appropriate `sources/<category>/` subdirectory based on their type. Do not leave them at the project root or in `target/`.

### Project Directory Structure

Each project follows this convention:

```
<project>/
  sources/
    images/     # Reference/source images (e.g. ref_image_base64.txt)
    videos/     # Source video files
    scripts/    # Generation scripts (generate.py, retry.py, etc.)
    others/     # Other source files (request payloads, configs)
  target/
    images/     # Generated output images
    videos/     # Generated output videos
    scripts/    # Output scripts, log scripts
    others/     # Other output files (URL lists, metadata)
```

## Interaction & Behavioral Norms

- Trigger media tools **only** when the user explicitly requests image, poster, illustration, visual design, video, animation, or multimedia generation.
- Handle text, search, document, code, and planning tasks yourself — do not invoke media tools for these.
- On media tool success, report the local file path to the user; if the tool returns a `remote_url`, display it alongside.
- On media tool failure, clearly report the cause. If a security block occurred, state directly that the path request was blocked.
- By default only `chat_01` is active; `pic_01` and `mov_01` are internal/debug profiles — do not start gateways for them externally.

## Services

| Tool | Model | Endpoint | Description |
|------|-------|----------|-------------|
| `generate_image_via_pic01` | agnes-image-2.0-flash | `/v1/images/generations` | Text-to-image, image-to-image, multi-image composition |
| `generate_video_via_mov01` | agnes-video-v2.0 | `/v1/videos` | Text-to-video generation |

### Pricing

| Service | Standard Price | Current Price |
|---------|---------------|---------------|
| Image generation | `$0 / 张` | `$0 / 张` (currently free) |
| Video generation | `$0.005 / 秒` | `$0 / 秒` (currently free) |

### Model Ranking

Agnes Image 2.0 Flash ranks on the **Artificial Analysis 图像编辑排行榜** with **ELO 评分 1,184** (Top 20 区间), demonstrating strong image editing capabilities.

## When to Use

Trigger these tools when the user explicitly asks to:
- Generate an image, poster, illustration, or visual design
- Generate a video, animation, or multimedia output
- Create visual content from a text description

Do NOT use for:
- Web design mockups → use `claude-design` or `sketch`
- Diagrams → use `excalidraw` or `architecture-diagram`
- Infographics → use `baoyu-infographic`
- Programmatic animations → use `manim-video`

## Prerequisites

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGNES_API_KEY` | Yes | — | Agnes AI API key for authentication |
| `AGNES_IMAGE_MODEL` | No | `agnes-image-2.0-flash` | Image generation model ID |
| `AGNES_VIDEO_MODEL` | No | `agnes-video-v2.0` | Video generation model ID |
| `AGNES_IMAGE_ENDPOINT` | No | `https://apihub.agnes-ai.com/v1/images/generations` | Image API base URL |
| `AGNES_VIDEO_ENDPOINT` | No | `https://apihub.agnes-ai.com/v1/videos` | Video API base URL |
| `AGNES_WORKSPACE_ROOT` | No | `/home/alan/workspace` | Root directory for generated media |
| `AGNES_IMAGE_TIMEOUT` | No | `180` | Image request timeout (seconds) |
| `AGNES_VIDEO_TIMEOUT` | No | `300` | Video submission timeout (seconds) |
| `AGNES_DOWNLOAD_TIMEOUT` | No | `300` | Download timeout (seconds) |
| `AGNES_MAX_RETRIES` | No | `10` | Number of retry attempts on transient errors (image: 10+, video: 2) |
| `AGNES_RETRY_DELAY` | No | `30` | Delay between retries (seconds) (image: 30s, video: 3s) |

### Project Name Rules

- Must be a single directory slug: ASCII letters, digits, hyphens, underscores
- No slashes (`/`, `\`), no `..`, no path traversal
- No non-ASCII characters (Chinese, emoji, etc.)
- Examples: `brand_retro`, `photo_project`, `christmas_cat_project`

## Image Generation

### Parameters

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `project_name` | Yes | string | — | Safe project directory slug |
| `prompt` | Yes | string | — | Detailed visual description |
| `file_name` | Yes | string | — | Output filename with extension (ASCII only) |
| `size` | No | string | `1024x1024` | Image dimensions in `WIDTHxHEIGHT` format |

### Generation Modes

The API (`POST /v1/images/generations`) supports three modes via `extra_body`:

**1. 文生图 (Text-to-Image)** — No `image` field. Uses `prompt` only.

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer $AGNES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.0-flash",
    "prompt": "A cat on a white background, soft studio lighting",
    "size": "1024x768",
    "extra_body": { "response_format": "url" }
  }'
```

**2. 图生图 (Image-to-Image)** — Pass reference image(s) in `extra_body.image[]`.

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer $AGNES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.0-flash",
    "prompt": "Transform this cat into a summer scene, wearing a red bow",
    "size": "1024x768",
    "extra_body": {
      "image": ["https://example.com/cat.jpg"],
      "response_format": "url"
    }
  }'
```

**3. 多图合成 (Multi-Image Composition)** — Pass multiple images in `extra_body.image[]`.

```bash
curl https://apihub.agnes-ai.com/v1/images/generations \
  -H "Authorization: Bearer $AGNES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-image-2.0-flash",
    "prompt": "Combine the two characters into an intense fantasy battle scene",
    "size": "1024x768",
    "extra_body": {
      "image": [
        "https://example.com/character-1.png",
        "https://example.com/character-2.png"
      ],
      "response_format": "url"
    }
  }'
```

### Reference Image Input Methods

**URL input** — Use publicly accessible image URLs. Fast and simple.

**Data URI input** — For local images that aren't served by any HTTP server:
```json
"image": ["data:image/jpg;base64,/9j/4AAQ..."]
```
To generate the Data URI from a local file:
```bash
echo "data:image/jpg;base64,$(base64 -w0 /path/to/image.jpg)"
```

### Output Format Options

| Method | Where to set | Effect |
|--------|-------------|--------|
| `extra_body.response_format: "url"` | In `extra_body` | Returns a downloadable URL |
| `return_base64: true` | At top level | Returns `b64_json` in response |
| `extra_body.response_format: "b64_json"` | In `extra_body` | Returns `b64_json` in response |

> ⚠️ **`response_format` MUST be inside `extra_body`, never at the top level.** Putting it at the top level causes an error. Use `extra_body.response_format`, NOT `response_format` alone.

### Response Fields

```json
{
  "created": 1780000000,
  "data": [
    {
      "url": "https://storage.googleapis.com/agnes-aigc/xxx.png",
      "b64_json": null,
      "revised_prompt": null
    }
  ]
}
```

### Queue Full Handling (HTTP 503)

The image generation queue frequently returns `503 image queue is full, please retry later` under load. **This is a transient condition, not a failure.** Recommended retry strategy:

- **Retry delay**: 30 seconds between attempts (not the default 3s)
- **Max retries**: 10+ attempts (not the default 2)
- **Sequential**: Only send one image request at a time to avoid exacerbating queue pressure
- **No parallelism**: Do NOT submit multiple concurrent image requests; they'll all fail with 503
- The queue clears over time — a single successful request per ~30s cycle is realistic under load

### Success Response

```json
{
  "ok": true,
  "service": "pic_01",
  "model": "agnes-image-2.0-flash",
  "path": "/home/alan/workspace/<project>/target/images/<filename>",
  "relative_path": "~/workspace/<project>/target/images/<filename>",
  "remote_url": "https://...",
  "bytes": 1234567
}
```

### Error Response

```json
{
  "ok": false,
  "service": "pic_01",
  "error": "Error message"
}
```

## Video Generation

### Parameters

| Parameter | Required | Type | Default | Description |
|-----------|----------|------|---------|-------------|
| `project_name` | Yes | string | — | Safe project directory slug |
| `prompt` | Yes | string | — | Detailed video/storyboard description |
| `file_name` | Yes | string | — | Output filename with extension (ASCII only) |
| `mode` | No | string | — | Generation mode: omit for text-to-video, `"ti2vid"` for image-to-video, `"keyframes"` for keyframe animation |
| `image` | No | string | — | **图生视频**: single image URL at top level (NOT in extra_body) |
| `height` | No | integer | `768` | Video height in pixels. Auto-mapped to nearest standard resolution (480p/720p/1080p) |
| `width` | No | integer | `1152` | Video width in pixels |
| `num_frames` | No | integer | `121` | Total frames. Must be ≤ 441 and follow `8n + 1` rule: 81, 121, 241, 441 |
| `frame_rate` | No | number | `24` | Frames per second. Range 1–60 |
| `num_inference_steps` | No | integer | — | Number of inference steps |
| `seed` | No | integer | — | Random seed for reproducible results |
| `negative_prompt` | No | string | — | Reverse prompt: describe what to avoid in the video |
| `extra_body.image` | No | array | — | **关键帧动画**: array of image URLs for keyframe transitions |
| `extra_body.mode` | No | string | — | `"keyframes"` — set when using keyframe animation mode |

### Duration Calculation

`seconds = num_frames / frame_rate`

| Target Duration | Recommended Params |
|----------------|-------------------|
| ~3 seconds | `num_frames: 81`, `frame_rate: 24` |
| ~5 seconds | `num_frames: 121`, `frame_rate: 24` ← **recommended** |
| ~10 seconds | `num_frames: 241`, `frame_rate: 24` |
| ~18 seconds | `num_frames: 441`, `frame_rate: 24` |

### Resolution Standardization

The API auto-maps requested dimensions to the nearest standard preset:

| Tier | Aspect Ratios |
|------|---------------|
| **480p** | 16:9, 9:16, 1:1, 4:3, 3:4 |
| **720p** | 16:9, 9:16, 1:1, 4:3, 3:4 ← **default** |
| **1080p** | 16:9, 9:16, 1:1, 4:3, 3:4 |

Default when unspecified: `width: 1152, height: 768` (720p 3:2 → auto-mapped).

### Recommended Settings

| Scenario | Recommended |
|----------|-------------|
| Standard video | `width: 1152, height: 768, num_frames: 121, frame_rate: 24` |
| Social short | `num_frames: 81 or 121, frame_rate: 24` |
| Longer video | Increase `num_frames` or decrease `frame_rate` |
| Smoother motion | `frame_rate: 24` or `30` |
| Reproducible results | Set a fixed `seed` |
| Keyframe transition | `extra_body.mode: "keyframes"` |
| Avoid unwanted content | Use `negative_prompt` |

### Generation Modes

**1. 文生视频 (Text-to-Video)** — No `image` / `mode` fields. Uses `prompt` only.

```bash
curl -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer $AGNES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "A cinematic shot of a cat walking on the beach at sunset",
    "width": 1152,
    "height": 768,
    "num_frames": 121,
    "frame_rate": 24
  }'
```

**2. 图生视频 (Image-to-Video / ti2vid)** — Pass `mode: "ti2vid"` and a single `image` URL at top level.

```bash
curl -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer $AGNES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "mode": "ti2vid",
    "image": "https://example.com/cat.jpg",
    "prompt": "The cat starts skateboarding, doing tricks...",
    "width": 1152,
    "height": 768,
    "num_frames": 121,
    "frame_rate": 24
  }'
```

**3. 关键帧动画 (Keyframe Animation)** — Pass `extra_body.mode: "keyframes"` and `extra_body.image[]` array.

```bash
curl -X POST https://apihub.agnes-ai.com/v1/videos \
  -H "Authorization: Bearer $AGNES_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-video-v2.0",
    "prompt": "Smooth transitions between scenes",
    "width": 1152,
    "height": 768,
    "num_frames": 121,
    "frame_rate": 24,
    "extra_body": {
      "mode": "keyframes",
      "image": [
        "https://example.com/frame1.jpg",
        "https://example.com/frame2.jpg"
      ]
    }
  }'
```

### Important: Async Behavior

Video generation is **asynchronous**. The tool may return `ok: false` with a message
about no direct payload — **this is expected**, not a failure. The task is queued on
the Agnes platform.

```json
{
  "ok": false,
  "message": "Agnes video task submitted (async), returned no direct payload",
  "raw": {
    "task_id": "task_abc123",
    "video_id": "xyz...",
    "status": "queued",
    "progress": 0,
    "seconds": "5.0",
    "size": "1280x704"
  }
}
```

### Video Completion Workflow

1. Capture the **`video_id`** (base64-encoded field) from the POST response
2. Extract the **real video_id** by decoding the base64 — the decoded string contains `video_id:video_d39354f7...`. The `check_task.py` script auto-extracts it when you pass the raw encoded value.
3. Wait 60+ seconds for processing
4. Check status via the **correct endpoint** — `GET /agnesapi?video_id=<real_video_id>` (see `scripts/check_task.py`)
5. When `status: completed`, download the video from the `url` field
6. Save to `<workspace>/<project>/target/videos/<file_name>`

> ⚠️ **CRITICAL: Only use `/agnesapi?video_id=` for status checks.**
> DO NOT use `GET /v1/videos/{task_id}` to check video status — that endpoint does NOT return task results and may return `queued` forever even after the video is complete.

### Task Status Check (use video_id, not task_id)

根据官方文档 (https://agnes-ai.com/zh-Hans/docs/agnes-video-v20)，获取视频结果的**推荐方式**是：

```
GET /agnesapi?video_id=<VIDEO_ID>
```

使用脚本（需要 video_id，脚本会自动提取）：

```bash
python3 scripts/check_task.py <video_id>
```

或手动查询：

```bash
curl -s "https://apihub.agnes-ai.com/agnesapi?video_id=<video_id>" \
  -H "Authorization: Bearer $AGNES_API_KEY"
```

> ⚠️ **永远不要使用** `GET /v1/videos/{task_id}` 查询视频状态——该 endpoint 不返回任务结果，即使视频已实际完成也会一直显示 `queued`。始终使用 `/agnesapi?video_id=<video_id>`。

### Async Monitoring (Background Process)

Video generation is async. After submitting a task:

1. **Capture the `video_id`** from the tool response's `raw.video_id` field
2. **Use the `agnes-video-async-monitor` skill** which provides reusable scripts:
   - `monitor_video.py` — generic video task monitoring
   - `monitor_keyframe.py` — keyframe animation specific monitoring
3. **Run as a background process** (NOT cron — minimum cron interval is 30m, too slow):
   ```python
   terminal(
     command='python3 ~/.hermes/profiles/user001/scripts/monitor_video.py',
     background=True,
     notify_on_complete=True,
     timeout=600
   )
   ```
4. The script polls every 30s, reports progress with duration/resolution/frames/fps,
   auto-downloads on completion, and exits.

> ⚠️ Cron cannot do 30s polling (minimum interval is 30m). The security filter also blocks prompts containing `$AGNES_API_KEY` in curl commands. Always use a background Python script that reads the API key from the environment internally.

## FAQ (来自官方文档)

| 问题 | 答案 |
|------|------|
| 是否支持文生图？ | ✅ 支持，只用 `prompt` 字段 |
| 是否支持图生图？ | ✅ 支持，使用 `extra_body.image[]` 传入图片 |
| 图生图是否需要 `tags` 参数？ | ❌ 不需要，只用 `prompt` + `image[]` |
| 为什么 `response_format` 放顶层会报错？ | 必须放在 `extra_body` 内部，用 `extra_body.response_format` |
| 输入图片 URL 无法访问怎么办？ | 改用 Data URI 输入，或确认 URL 可公开访问 |
| 请求超时怎么办？ | 检查网络连接，或降低图片分辨率，或增加 `timeout` 设置 |
| 视频支持哪些分辨率？ | 480p / 720p / 1080p，多种宽高比（16:9, 9:16, 4:3, 3:4, 1:1） |
| 视频时长如何计算？ | `num_frames / frame_rate`，推荐 121 帧 / 24 fps = 5 秒 |
| 图生视频和关键帧动画有何区别？ | 图生视频用一张图生成动作视频；关键帧动画用多张图生成场景过渡 |
| 如何生成连贯动作？ | 使用关键帧动画模式（`extra_body.mode: "keyframes"` + `extra_body.image[]`） |
| 为什么查询状态 endpoint 要用 `/agnesapi?video_id=`？ | `/v1/videos/{task_id}` 不返回完成状态，会一直 `queued` |

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| HTTP 400 | Bad Request — 参数错误或缺失必填字段 | 检查请求 body 格式和必填参数 |
| HTTP 401 | Unauthorized — API Key 无效或未提供 | 检查 `AGNES_API_KEY` 环境变量是否正确设置 |
| HTTP 404 | Not Found — 请求的资源不存在 | 检查视频 ID 或任务 ID 是否正确 |
| HTTP 429 | Rate limit exceeded — 请求频率过高 | 自动重试，使用退避策略 |
| HTTP 500/502/504 | Server error — 服务端内部错误 | 自动重试，使用退避策略 |
| HTTP 503 | Queue full (image generation) — 图像队列已满 | 重试 30 秒间隔，最多 10+ 次。顺序请求，禁止并行 |
| "不合法的项目名称" | Invalid project name | Use ASCII-only slug, no path separators |
| "不合法的文件名" | Invalid filename | Use ASCII-only, no path components |
| "【安全拦截】" | Path traversal attempt | Blocked by design — cannot be bypassed |
| "无效的令牌" | Bad API key | Check AGNES_API_KEY value |

### 官方推荐提示词模板

**文生图 (Text-to-Image)**: `[主体] + [场景/背景] + [风格] + [光照] + [构图] + [质量要求]`

示例：*A silver-gray tabby cat on a white studio background, cute pet photography style, soft rim lighting, centered composition, high detail*

**图生图 / 图像编辑 (Image-to-Image / Editing)**: `[编辑指令] + [需要保留的元素] + [目标风格/场景] + [光照] + [构图] + [质量要求]`

示例：*Change the background to a futuristic city at night while keeping the cat's face, fur pattern, and pose unchanged*

**多图合成 (Multi-Image Composition)**: 描述各图角色 + 组合场景 + 氛围 + 构图

示例：*Place the person from the first image beside the robot from the second image in a cinematic sci-fi battle scene, dynamic lighting, detailed background*

### 官方提示词范例

| 场景 | 范例提示词 |
|------|-----------|
| 文生图 - 产品摄影 | *A professional product photo of a wireless headphone on a clean white background, soft studio lighting, sharp details, commercial photography style* |
| 图生图 - 背景替换 | *Change the background to a futuristic city at night while keeping the person's face, outfit, and pose unchanged* |
| 多图合成 - 角色组合 | *Place the person from the first image beside the robot from the second image in a cinematic sci-fi battle scene* |

### 响应中的 `revised_prompt`

API 返回的 `data[].revised_prompt` 字段包含模型改写后的提示词，可用于了解模型对原始 prompt 的理解方式，便于后续优化提示词。

## Prompt Writing Tips

- **Be specific**: subject, style, lighting, composition, mood, color palette
- **Include style keywords**: "professional photography", "studio lighting", "4K", "cinematic"
- **For consistent subjects with image-to-image**: describe the *change* you want while saying what to preserve (e.g. "keep the cat's face and fur details unchanged, add a red bow")
- **For multi-panel images**: describe each panel's content explicitly
- **For videos**: describe scene changes, camera movements, and transitions

> 💡 **提示词结构参考上方「官方推荐提示词模板」**，按 `[主体] + [场景/背景] + [风格] + [光照] + [构图] + [质量要求]` 模板组织 prompt 效果最佳。

### Image — Photorealistic Portrait

```
A photorealistic portrait of a silver-gray tabby cat with black tabby stripes,
clear M-shaped marking on forehead, pale yellow-green eyes, pinkish-brown nose,
white-tipped paws, round face, studio lighting, shallow depth of field, 4K
```

### Image — Landscape

```
Cinematic wide shot of a Japanese zen garden at golden hour, raked sand patterns,
maple trees with red leaves, koi pond reflecting sky, soft warm lighting,
photorealistic, 4K, professional photography
```

### Video — Product Showcase

```
Smooth product showcase: a ceramic coffee cup rotates slowly on a white surface,
warm studio lighting casts soft shadows, camera zooms in gradually,
minimalist aesthetic, 5 seconds, 1280x704
```

## Workflow

### Step 1: Confirm Project Name
If not provided, ask the user for a project name.

### Step 2: Prepare the Prompt
Write a detailed, specific prompt based on the user's request.

### Step 3: Prepare Reference Images (if applicable)

For 图生图 or 多图合成 with local files, convert to Data URI first:
```bash
python3 scripts/to_data_uri.py path/to/image.jpg --short
# → data:image/jpeg;base64,/9j/4AAQ...
```
For remote URLs, use the URL directly.

> **Files from chat tools** (Feishu, Telegram, etc.) are automatically saved into `sources/images/`, `sources/videos/`, or `sources/scripts/` based on their type. No need to manually move them — the project skeleton is created automatically on first use.

### Step 4: Call the Tool
```python
# 文生图
generate_image_via_pic01(
    project_name="my_project",
    prompt="detailed visual description",
    file_name="output.png",
    size="1024x1024"  # optional
)

# 图生图 — add image parameter
generate_image_via_pic01(
    project_name="my_project",
    prompt="edit instruction + elements to preserve",
    file_name="edited.png",
    image=["data:image/jpeg;base64,..."]  # or URL
)

# 多图合成 — pass multiple images
generate_image_via_pic01(
    project_name="my_project",
    prompt="combine these characters in a scene",
    file_name="composite.png",
    image=["url1", "url2"]  # 2+ images
)
```

### Step 5: Report Results
Report the local file path and remote URL (if available).

## Reference Files

- `references/video-async-guide.md` — Complete guide to async video generation, polling, and API retrieval
- `references/image-api-guide.md` — Complete API reference: image-to-image, multi-image, prompt templates, queue retry, Data URI, response_format placement
- `references/deployment-workflow.md` — Source-to-deployment sync workflow: maintaining `sources/agnes-media-skill/` ↔ `~/.hermes/profiles/<profile>/`
- `scripts/check_task.py` — CLI tool to check video task status
- `scripts/to_data_uri.py` — Convert local image files to Data URI for 图生图/多图合成 input. Usage: `python3 scripts/to_data_uri.py path/to/image.jpg --short`
- `templates/image-queue-retry.py` — Reusable retry script for 503 queue-full errors; serial requests with 30s delay

## Pitfalls

1. **Never use non-ASCII in filenames** — triggers Agnes platform security block
2. **Never use non-ASCII in project names** — same security block
3. **File names must include extensions** (.jpg, .png, .mp4)
4. **Retries are automatic** — transient errors (timeout, 500, 503) are retried up to MAX_RETRIES
5. **Video ok:false is normal** — async submission, not a failure
6. **Video URL may be missing** — platform sometimes removes download links for completed tasks
7. **API key in cron jobs** — may expand to literal string `${AGNES_API_KEY}`; use `check_task.py` which handles extraction automatically
8. **Tirith security scanner** — blocks inline scripts and pipes in cron; use the standalone `check_task.py` script instead
9. **Wrong endpoint for status check** — `GET /v1/videos/{task_id}` does NOT return task results. Even when the video is complete, it may incorrectly report `queued` forever. Always use `GET /agnesapi?video_id=<real_video_id>` instead (see official docs at https://agnes-ai.com/zh-Hans/docs/agnes-video-v20). The `video_id` returned by POST is base64-encoded; decode it to get the real video_id before querying. See `check_task.py` for auto-extraction logic.
10. **Duration is capped below request** — requesting `duration: 10` typically results in a 5-second video. The actual `seconds` field in the response shows the true duration. Check it after submission rather than assuming the requested value.
11. **Resolution auto-mapped to presets** — requesting arbitrary resolutions (e.g. `1280x704`) gets remapped to the nearest supported preset. Always check the `size_mapping` field in the completed response to see the actual resolution used. Supported presets include 720p with various aspect ratios.
12. **Completed response is rich** — the completed JSON includes `perf_infer_s` (actual inference time), `size_mapping` (resolution adjustments), `request_params` (exact parameters including negative_prompt, seed, num_frames, num_inference_steps). Present these to the user when reporting results.
13. **`generate_video_via_mov01` now supports all video modes** — The tool passes all extended parameters to the Agnes API: `mode` (ti2vid/keyframes), `image` (URL or Data URI for ti2vid), `height`, `width`, `num_frames`, `frame_rate`, `num_inference_steps`, `seed`, `negative_prompt`, and `extra_body` (for keyframe animation with `mode: "keyframes"` + `image[]`). No need for raw API calls unless debugging edge cases. For raw API access (diagnostics, large payloads), write the base64 payload to a temp file and use `-d @file` to avoid shell argument length limits.
14. **Image queue full (503) requires long retry** — Image generation often returns `503 image queue is full`. This is transient, NOT a real error. Retry with **30s delay between attempts, up to 10+** attempts. Send requests **sequentially** (one at a time), not in parallel.
15. **`response_format` must be in `extra_body`** — Putting `response_format` at the top level causes an error. Always nest it inside `extra_body.response_format`. Use `return_base64: true` at the top level as an alternative for base64 output.
16. **Local reference images need Data URI** — If a reference image is not served by an HTTP server, convert it to a Data URI: `data:image/jpg;base64,$(base64 -w0 /path/to/image.jpg)`. This is preferred over running a local HTTP server.