# Agnes Media Skill

Hermes Agent plugin and skill for Agnes AI media generation. Provides
safe, configurable tools for **text-to-image**, **image-to-image**,
**multi-image composition**, and **video** generation with
workspace isolation, retry logic, and async video polling.

## Quick Start

1. Clone this repository
2. Set `AGNES_API_KEY` environment variable
3. Deploy as a Hermes Agent plugin or skill

## Project Structure

```
agnes-media-skill/
├── plugins/
│   └── agnes_router/           # Hermes Agent plugin (tool handlers)
│       ├── __init__.py         # Tool registration
│       ├── plugin.yaml         # Plugin manifest + configurable parameters
│       ├── schemas.py          # Tool parameter schemas
│       ├── tools.py            # Image/video generation handlers
│       └── workspace_manager.py # Path validation + security
├── skills/
│   ├── creative/
│   │   └── agnes-media/        # Hermes Agent skill (main)
│   │       ├── SKILL.md        # Skill documentation
│   │       ├── scripts/
│   │       │   ├── check_task.py        # Video task status checker
│   │       │   └── to_data_uri.py       # File → Data URI converter
│   │       ├── templates/
│   │       │   └── image-queue-retry.py # Image 503 retry example
│       │       └── references/
│       │           ├── image-api-guide.md            # Image API reference (i2i, multi-image, queue retry)
│       │           ├── video-async-guide.md          # Async video workflow guide
│       │           ├── deployment-workflow.md        # Source-to-deployment sync workflow
│       │           └── png-metadata-extraction.md    # Extract embedded prompt metadata from PNGs
│   └── media/
│       └── agnes-video-async-monitor/   # Async video polling skill
│           └── SKILL.md                  # Background-process polling workflow
├── examples/                   # Example prompts and configurations
├── DEPLOYMENT_MANUAL.md        # Deployment guide
├── README.md                   # This file
├── LICENSE
└── .gitignore
```

## Features

- **Three image generation modes** — 文生图 (text-to-image), 图生图 (image-to-image), 多图合成 (multi-image composition). Supports URL and Data URI image input.
- **Three video generation modes** — 文生视频 (text-to-video), 图生视频 (image-to-video / ti2vid), 关键帧动画 (keyframe animation). Configurable resolution, frame count, frame rate, seed, and negative prompt.
- **Secure workspace isolation** — all generated files saved under a configurable workspace root with path traversal protection
- **Automatic retry** — transient errors (timeout, 503, rate limit) are retried with configurable delay (30s for image queue, 3s for general errors)
- **Async video support** — video generation is handled correctly with background-process polling (30s interval) and automatic download on completion
- **Environment configurable** — every parameter (endpoints, timeouts, models, workspace root) can be overridden via environment variables
- **Cron-safe** — works in scheduled jobs with automatic API key extraction. Note: video polling uses background processes (not cron) because cron's minimum recurring interval is 30 minutes.

## Project Directory Convention

Generated media files follow a structured project layout under the workspace root. The full skeleton is created automatically on first use:

```
~/workspace/
└── <project_name>/
    ├── sources/          ← Input assets: reference images, source files
    │   ├── images/       ← Reference images (e.g. from chat tools)
    │   ├── videos/       ← Source video files
    │   ├── scripts/      ← Generation scripts
    │   └── others/       ← Other input files (configs, payloads)
    └── target/           ← Output results: generated media files
        ├── images/       ← Image outputs (from generate_image_via_pic01)
        ├── videos/       ← Video outputs (from generate_video_via_mov01)
        ├── scripts/      ← Output scripts, logs
        └── others/       ← Other output files (URL lists, metadata)
```

All media tools save outputs to `target/images/` or `target/videos/` automatically.
Input assets (reference images from chat tools, local files, etc.) should be placed in the corresponding `sources/<category>/` subdirectory.

## Configuration

### Environment Variables

All variables are optional except `AGNES_API_KEY`.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AGNES_API_KEY` | string | **(required)** | Agnes AI API key |
| `AGNES_IMAGE_MODEL` | string | `agnes-image-2.0-flash` | Image generation model |
| `AGNES_VIDEO_MODEL` | string | `agnes-video-v2.0` | Video generation model |
| `AGNES_IMAGE_ENDPOINT` | URL | `https://apihub.agnes-ai.com/v1/images/generations` | Image API endpoint |
| `AGNES_VIDEO_ENDPOINT` | URL | `https://apihub.agnes-ai.com/v1/videos` | Video API endpoint |
| `AGNES_WORKSPACE_ROOT` | path | `~/workspace` | Root directory for media |
| `AGNES_IMAGE_TIMEOUT` | int | `180` | Image request timeout (seconds) |
| `AGNES_VIDEO_TIMEOUT` | int | `300` | Video submission timeout (seconds) |
| `AGNES_DOWNLOAD_TIMEOUT` | int | `300` | Media download timeout (seconds) |
| `AGNES_MAX_RETRIES` | int | `10` | Max retry attempts (image queue 503: 10+) |
| `AGNES_RETRY_DELAY` | float | `30.0` | Delay between retries (image queue: 30s) |

### Plugin YAML Configuration

The `plugins/agnes_router/plugin.yaml` file defines additional configuration
options that can be set in the Hermes Agent config:

```yaml
plugins:
  entries:
    agnes_router:
      workspace_root: /data/media        # Override default workspace
      image_endpoint: https://...        # Custom API endpoint
      video_endpoint: https://...        # Custom API endpoint
      image_model: agnes-image-2.0-flash
      video_model: agnes-video-v2.0
      image_timeout: 180
      video_timeout: 300
      download_timeout: 300
      max_retries: 10
      retry_delay: 30.0
```

## Deployment

### Option 1: Hermes Agent Plugin (Recommended)

1. Copy the `plugins/agnes_router` directory to your Hermes Agent plugins path:

   ```bash
   cp -r plugins/agnes_router ~/.hermes/profiles/<profile>/plugins/
   ```

2. Enable the plugin in `config.yaml`:

   ```yaml
   plugins:
     enabled:
       - agnes_router
   ```

3. Set the API key:

   ```bash
   export AGNES_API_KEY="sk-…"
   ```

4. Restart Hermes Agent.

### Option 2: Hermes Agent Skills

1. Copy the skills to your skills path:

   ```bash
   # Main skill (docs + scripts)
   cp -r skills/creative/agnes-media ~/.hermes/profiles/<profile>/skills/creative/
   
   # Async video monitoring skill (background-process polling workflow)
   cp -r skills/media/agnes-video-async-monitor ~/.hermes/profiles/<profile>/skills/media/
   ```

2. The skills document the tool usage patterns and best practices.
   The actual tool handlers come from the plugin (Option 1).

### Option 3: Standalone Script Usage

Use `check_task.py` independently:

```bash
python3 skills/creative/agnes-media/scripts/check_task.py <video_id>
```

## Tool Reference

### generate_image_via_pic01

Generates images from text, edits existing images, or composites multiple images.

**Parameters:**

| Param | Required | Type | Default | Description |
|-------|----------|------|---------|-------------|
| `project_name` | Yes | string | — | Project slug (ASCII only, no slashes) |
| `prompt` | Yes | string | — | Detailed visual description or edit instruction |
| `file_name` | Yes | string | — | Output filename with extension |
| `size` | No | string | `1024x1024` | Image dimensions (WIDTHxHEIGHT) |
| `image` | No | array[string] | — | Image URL(s) or Data URI(s) for 图生图/多图合成 |

**Modes:**
- **文生图**: `image` not set — generate from prompt
- **图生图**: `image: [1 URL]` — edit/transform existing image
- **多图合成**: `image: [2+ URLs]` — combine multiple reference images

**Output:** Image saved to `<workspace>/<project>/target/images/<file_name>`

### generate_video_via_mov01

Generates videos from text, images, or keyframe sequences.

**Parameters:**

| Param | Required | Type | Default | Description |
|-------|----------|------|---------|-------------|
| `project_name` | Yes | string | — | Project slug (ASCII only, no slashes) |
| `prompt` | Yes | string | — | Detailed video/storyboard description |
| `file_name` | Yes | string | — | Output filename with extension |
| `mode` | No | string | — | `"ti2vid"` (image-to-video) or `"keyframes"` |
| `image` | No | string | — | Single image URL for ti2vid mode |
| `height` | No | int | 768 | Video height (auto-mapped to preset) |
| `width` | No | int | 1152 | Video width |
| `num_frames` | No | int | 121 | Total frames (81, 121, 241, 441) |
| `frame_rate` | No | number | 24 | Frames per second |
| `num_inference_steps` | No | int | — | Inference steps |
| `seed` | No | int | — | Random seed |
| `negative_prompt` | No | string | — | Content to avoid |
| `extra_body` | No | object | — | For keyframes: `{mode: "keyframes", image: [...]}` |

**Output:** Video saved to `<workspace>/<project>/target/videos/<file_name>`

**Note:** Video generation is async. The tool returns immediately with a task ID.
Use `monitor_video.py` (or `monitor_keyframe.py` for keyframes) from the `agnes-video-async-monitor` skill for background polling, or `check_task.py` for manual status checks.
Always query `GET /agnesapi?video_id=<real_video_id>` — never `GET /v1/videos/{task_id}`.

## Security & Operational Guidelines

### Agent Identity

You are the master controller agent responsible for daily conversation, document writing, information retrieval, project workspace management, and subordinate media task scheduling.

You have two subordinate specialized capability interfaces. Unless the user asks about architecture details, do not proactively expose internal codenames:

1. `generate_image_via_pic01` — Image generation service, specializing in text-to-image, image-to-image, and image modification. Underlying Agnes model: `agnes-image-2.0-flash`.
2. `generate_video_via_mov01` — Audio/video and video generation service, specializing in video, animation, and multimedia generation. Underlying Agnes model: `agnes-video-v2.0`.

### Workspace & Project Isolation Rules

1. All file read/write and media generation tasks must operate within a specific project directory.
2. The unified workspace root is `~/workspace` (configurable via `AGNES_WORKSPACE_ROOT`).
3. If the user has not explicitly specified a current project, you must ask or guide the user to define a compliant project name, e.g. `brand_retro`, `game_design`, `project_alpha`.
4. When calling subordinate media tools, you must accurately pass the current project name as `project_name` and propose a reasonable filename with the correct extension.
5. `project_name` must be a single directory slug — no `../`, slashes, backslashes, absolute paths, or any content attempting to escape the workspace.
6. Never attempt to construct out-of-bounds paths such as `/etc`, `../`, `~/.ssh`.
7. Follow the project directory convention: `<project>/sources/` for inputs, `<project>/target/` for outputs.

### Interaction & Behavioral Norms

- Trigger media tools **only** when the user explicitly requests image, poster, illustration, visual design, video, animation, or multimedia generation.
- Handle text, search, document, code, and planning tasks yourself — do not invoke media tools for these.
- On media tool success, report the local file path to the user; if the tool returns a `remote_url`, display it alongside.
- On media tool failure, clearly report the cause. If a security block occurred, state directly that the path request was blocked.
- By default only `chat_01` is active; `pic_01` and `mov_01` are internal/debug profiles — do not start gateways for them externally.

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `ok: false` with async message | Video queued | Poll task status via `/agnesapi?video_id=` |
| `ok: false` with `security_blocked` | Invalid project/filename | Use ASCII-only slugs |
| `ok: false` with HTTP 503 | Image queue full | Retry with 30s delay, up to 10+ times |
| `ok: false` with HTTP error | API returned error | Check logs, retry |
| `ok: false` with connection error | Network issue | Retry (automatic) |
| `ok: false` with "无效的令牌" | Bad API key | Check AGNES_API_KEY |
| `ok: false` with 400 Bad Request | Invalid params | Check request body format |

## Maintenance

### Updating the Plugin

1. Edit files in `plugins/agnes_router/`
2. Restart Hermes Agent to pick up changes
3. Test with a simple image generation

### Updating the Skill

1. Edit `skills/creative/agnes-media/SKILL.md` or `skills/media/agnes-video-async-monitor/SKILL.md`
2. Update version number in frontmatter
3. Commit changes

### Troubleshooting

1. **API key not working**: Verify `AGNES_API_KEY` is set and not a literal string
2. **Videos never complete**: Check task status via `check_task.py` — use `video_id` not `task_id`
3. **Image gets 503 error**: Increase `AGNES_MAX_RETRIES` to 10+ and `AGNES_RETRY_DELAY` to 30s
4. **Path errors**: Ensure project_name contains only ASCII letters, digits, `-`, `_`
5. **Rate limits**: Increase `AGNES_MAX_RETRIES` or `AGNES_RETRY_DELAY`
6. **Timeouts**: Increase `AGNES_IMAGE_TIMEOUT` or `AGNES_VIDEO_TIMEOUT`
7. **response_format error**: Must be in `extra_body`, never at top level

## License

MIT License — see LICENSE file.

## Compatibility

- Python 3.9+
- Hermes Agent (any version supporting plugins and skills)
- Linux, macOS, Windows
- Agnes AI API (apihub.agnes-ai.com)