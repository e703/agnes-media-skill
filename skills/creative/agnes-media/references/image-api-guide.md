# Agnes Image 2.0 Flash — API Reference

Model: `agnes-image-2.0-flash`
Endpoint: `POST https://apihub.agnes-ai.com/v1/images/generations`
Price: $0/image (free tier)
Ranking: ELO 1,184 on Artificial Analysis image editing, Top 20

## Supported Workflows

| Mode | How | Description |
|------|-----|-------------|
| 文生图 (Text-to-Image) | `prompt` only | Generate from text description |
| 图生图 (Image-to-Image) | `extra_body.image[]` | Edit/transform existing images |
| 多图合成 (Multi-Image) | `extra_body.image[]` (2+) | Combine multiple reference images |

## Applicable Scenarios

- Creative design (posters, concept art, social media)
- Marketing content (product ads, campaigns, banners)
- Image editing (object replacement, background change, style transfer, local edits)
- Character composition (combining multiple characters in one scene)
- E-commerce (product enhancement, scene staging, hero images)
- Social content (memes, avatars, thumbnails, lifestyle visuals)

## Request Headers

```
Authorization: Bearer <AGNES_API_KEY>
Content-Type: application/json
```

## Request Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | `agnes-image-2.0-flash` |
| `prompt` | string | Yes | Image description or edit instruction |
| `size` | string | No | `WIDTHxHEIGHT`, e.g. `1024x768`, `1024x1024` |
| `return_base64` | bool | No | Set `true` to return base64 output (alternative to `extra_body.response_format: "b64_json"`) |
| `extra_body.response_format` | string | No | `"url"` or `"b64_json"` — **MUST be inside `extra_body`** |
| `extra_body.image` | array[string] | For i2i/multi | Array of image URLs or Data URIs |

## Output Format

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

## Image Input Methods

### URL Input
Pass a publicly accessible URL:
```json
"image": ["https://example.com/input-image.png"]
```

### Data URI Input
For local files not served by HTTP:
```json
"image": ["data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."]
```
Generate with:
```bash
echo "data:image/jpg;base64,$(base64 -w0 /path/to/image.jpg)"
```
Note: The MIME type in the data URI must match the actual image format (`image/jpg`, `image/png`, `image/webp`, etc.).

## Queue Full Handling

When the API returns:
```json
{"error":{"message":"image queue is full, please retry later","type":"do_request_failed","code":"do_request_failed"}}
```

This is **transient** — retry with these parameters:
- Delay: **30 seconds** between attempts
- Max attempts: **10+** (queue can be full for several minutes under load)
- Strategy: **Sequential only** — never submit concurrent image requests
- One at a time works; the queue clears every ~30-60s for one request to get through

## Best Practice Prompt Templates

### 文生图
```
[主体] + [场景/背景] + [风格] + [光照] + [构图] + [质量要求]
```
Example: *A silver tabby cat on a white studio background, cute pet photography, soft rim lighting, centered, high detail, 4K*

### 图生图 / 图像编辑
```
[编辑指令] + [需要保留的元素] + [目标风格/场景] + [光照] + [构图] + [质量要求]
```
Example: *Change the background to a futuristic city at night while keeping the person's face, outfit, and pose unchanged*

### 多图合成
Describe each image's role + combined scene + atmosphere + composition.
Example: *Place the person from the first image beside the robot from the second image in a cinematic sci-fi battle scene*

## Curveball: response_format Location

**WRONG** (causes error):
```json
{
  "model": "agnes-image-2.0-flash",
  "response_format": "url"
}
```

**RIGHT**:
```json
{
  "model": "agnes-image-2.0-flash",
  "extra_body": { "response_format": "url" }
}
```

Alternative: use `return_base64: true` at the top level (works correctly).

## FAQ from Official Docs

1. **支持文生图？** ✅ Yes
2. **支持图生图？** ✅ Yes
3. **图生图需要 tags？** No — just use `extra_body.image[]`
4. **response_format 放顶层报错？** Yes — must be in `extra_body`
5. **输入图片 URL 无法访问？** Use Data URI instead
6. **请求超时？** Check network, lower image resolution, or retry