# Agnes Video API — Response Fields & Raw Access

## Correct Query Endpoint

| Purpose | URL | Notes |
|---------|-----|-------|
| Poll task status | `GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>` | **Always use this.** The `/v1/videos/{task_id}` endpoint never returns results. |
| Submit new task | `POST https://apihub.agnes-ai.com/v1/videos` | Used by `generate_video_via_mov01` internally, or for raw API access. |

Headers for all requests:
```
Authorization: Bearer $AGNES_API_KEY
Content-Type: application/json
Accept: application/json
```

## Poll Response Format

```json
{
  "status": "in_progress",
  "progress": 65,
  "seconds": 3.2,
  "size": "1088x832",
  "perf_params": {
    "frame_rate": 24,
    "num_frames": 121
  },
  "url": null,
  "error": null
}
```

Key fields:

| Field | Type | Meaning |
|-------|------|---------|
| `status` | string | `queued` → `in_progress` → `completed` / `failed` |
| `progress` | int | 0–100 |
| `seconds` | float | Video duration in seconds |
| `size` | string | Mapped resolution (e.g. `1088x832`) |
| `perf_params.frame_rate` | int | Configured frame rate |
| `perf_params.num_frames` | int | Total frames (must follow 8n+1 rule: 81/121/241/441) |
| `url` | string or null | Download URL; only present when `status=completed` |
| `error` | string or null | Error info when `status=failed` |

## Submit Request Format (Raw API)

```json
{
  "model": "agnes-video-v2.0",
  "prompt": "...",
  "image": "data:image/jpeg;base64,...",
  "num_frames": 121,
  "frame_rate": 24,
  "height": 768,
  "width": 1152,
  "seed": 42,
  "negative_prompt": "..."
}
```

Special modes:
- **ti2vid** (image-to-video): Set `"mode": "ti2vid"` and provide a single `image` (URL or Data URI)
- **keyframes**: Set `"mode": "keyframes"` in `extra_body` with an `"image"` array:
  ```json
  { "extra_body": { "mode": "keyframes", "image": ["url1", "url2", ...] } }
  ```

## Response from Submit (Sync Payload Return)

When submitting via `POST /v1/videos`, the response `video_id` field may be **base64-encoded**. Use `check_task.py`'s `extract_real_video_id()` to decode it properly.

```python
import base64

def extract_real_video_id(raw_id: str) -> str:
    """Decode a base64-encoded video_id if needed."""
    try:
        decoded = base64.b64decode(raw_id).decode("utf-8")
        if decoded.startswith("custom_") or ":" in decoded:
            return decoded
    except Exception:
        pass
    return raw_id
```

## Companion Script

`check_task.py` (from the main `skills/creative/agnes-media/scripts/` directory) provides a CLI for polling:

```bash
python3 check_task.py <video_id>
python3 check_task.py "video_bGl0ZWxsbTpjdXN0b21fbGxtX3Byb3ZpZGVy..."
```

It handles base64 decoding automatically.

## num_frames Rule

`num_frames` must follow **8n + 1**: valid values are 81, 121, 241, 441. Max 441. Using invalid values may cause silent fallback to default (121).

## Resolution Mapping

The API auto-maps requested resolution to the nearest preset:

| Requested | Mapped | Aspect |
|-----------|--------|--------|
| 1152×768 | 1088×832 | ~4:3 (720p) |
| 640×480 | 640×480 | VGA |
| 1920×1080 | 1920×1080 | 1080p Full HD |

Check the `size` field in the poll response to see the actual mapped resolution. Don't assume requested = actual.

## Image Input Format

For image-to-video (ti2vid): the `image` field accepts:
- A publicly accessible HTTP/HTTPS URL
- A Data URI: `data:image/{jpeg,png};base64,<base64_data>`
- Generate for a local file: `echo "data:image/jpeg;base64,$(base64 -w0 /path/to/image.jpg)"`

## Large Payload Warning

A 1024×1024 base64 Data URI is ~2.3 MB. When submitting raw API requests:
- **DO** write to a temp file and use `-d @/tmp/payload.json` with curl
- **DO NOT** inline the Data URI as a curl `-d '...'` argument — shell argument length limits will truncate it