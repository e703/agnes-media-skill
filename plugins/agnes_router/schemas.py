"""Tool schemas for the Agnes media router plugin."""

GENERATE_IMAGE_VIA_PIC01 = {
    "name": "generate_image_via_pic01",
    "description": (
        "Generate an image through the Agnes pic_01 image service and save it "
        "safely under <workspace_root>/<project_name>/images/. Use only when "
        "the user explicitly asks to create, edit, or render an image. A concrete "
        "project_name is required.\n\n"
        "Supported modes:\n"
        "1. 文生图 (Text-to-Image): prompt only — generate from text description\n"
        "2. 图生图 (Image-to-Image): prompt + 1 image URL/Data URI — edit/transform existing image\n"
        "3. 多图合成 (Multi-Image): prompt + 2+ image URLs/Data URIs — combine multiple reference images"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": (
                    "Single safe project directory slug. No slashes, dots, path "
                    "traversal, or non-ASCII characters. Examples: brand_retro, "
                    "photo_project, christmas_cat_project"
                ),
            },
            "prompt": {
                "type": "string",
                "description": (
                    "Detailed visual description of the image to generate. Be specific "
                    "about subject, style, lighting, composition, and mood.\n"
                    "For 图生图: describe the edit instruction + elements to preserve.\n"
                    "For 多图合成: describe each image's role + combined scene."
                ),
            },
            "file_name": {
                "type": "string",
                "description": (
                    "Output filename with extension (e.g. poster.png, photo_01.jpg). "
                    "Must be ASCII-only. Path components are stripped."
                ),
            },
            "size": {
                "type": "string",
                "description": "Optional image dimensions. Format: WIDTHxHEIGHT. Default: 1024x1024.",
                "default": "1024x1024",
            },
            "image": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Optional image URL(s) or Data URI(s) for 图生图 (image-to-image) "
                    "or 多图合成 (multi-image composition).\n"
                    "- 1 URL/Data URI → 图生图: edit/transform the image\n"
                    "- 2+ URLs/Data URIs → 多图合成: combine multiple reference images\n"
                    "Use Data URI for local files: data:image/png;base64,...\n"
                    "Generate with: echo \"data:image/jpg;base64,$(base64 -w0 /path/to/image.jpg)\""
                ),
            },
        },
        "required": ["project_name", "prompt", "file_name"],
    },
}

GENERATE_VIDEO_VIA_MOV01 = {
    "name": "generate_video_via_mov01",
    "description": (
        "Generate a video through the Agnes mov_01 video service and save it "
        "safely under <workspace_root>/<project_name>/videos/. Use only when "
        "the user explicitly asks to create video, animation, or multimedia output. "
        "A concrete project_name is required.\n\n"
        "Supported modes:\n"
        "1. 文生视频 (Text-to-Video): prompt only\n"
        "2. 图生视频 (Image-to-Video / ti2vid): prompt + mode='ti2vid' + single image URL\n"
        "3. 关键帧动画 (Keyframe Animation): prompt + extra_body mode='keyframes' + image[]"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": (
                    "Single safe project directory slug. No slashes, dots, path "
                    "traversal, or non-ASCII characters."
                ),
            },
            "prompt": {
                "type": "string",
                "description": (
                    "Detailed video or storyboard description. Include scene changes, "
                    "camera movements, style, and duration expectations."
                ),
            },
            "file_name": {
                "type": "string",
                "description": (
                    "Output filename with extension (e.g. intro.mp4). Must be ASCII-only."
                ),
            },
            "mode": {
                "type": "string",
                "description": (
                    "Generation mode. Omit for text-to-video, "
                    "'ti2vid' for image-to-video, "
                    "'keyframes' for keyframe animation."
                ),
                "enum": ["ti2vid", "keyframes"],
            },
            "image": {
                "type": "string",
                "description": (
                    "Single image URL for 图生视频 (ti2vid mode). "
                    "Must be a publicly accessible URL or Data URI. "
                    "Set at the top level (NOT inside extra_body)."
                ),
            },
            "height": {
                "type": "integer",
                "description": "Video height in pixels. Auto-mapped to nearest standard resolution (480p/720p/1080p). Default: 768.",
                "default": 768,
            },
            "width": {
                "type": "integer",
                "description": "Video width in pixels. Default: 1152.",
                "default": 1152,
            },
            "num_frames": {
                "type": "integer",
                "description": "Total frames. Must follow 8n+1 rule: 81, 121, 241, 441. Max 441. Default: 121.",
                "default": 121,
            },
            "frame_rate": {
                "type": "number",
                "description": "Frames per second. Range 1-60. Default: 24.",
                "default": 24,
            },
            "num_inference_steps": {
                "type": "integer",
                "description": "Number of inference steps (optional).",
            },
            "seed": {
                "type": "integer",
                "description": "Random seed for reproducible results (optional).",
            },
            "negative_prompt": {
                "type": "string",
                "description": "Reverse prompt: describe what to avoid in the video (optional).",
            },
            "extra_body": {
                "type": "object",
                "description": (
                    "Additional parameters passed as extra_body.\n"
                    "- mode: 'keyframes' for keyframe animation\n"
                    "- image: array of image URLs for keyframe transitions\n"
                    "Example: {\"mode\": \"keyframes\", \"image\": [\"url1\", \"url2\"]}"
                ),
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["keyframes"],
                    },
                    "image": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "required": ["project_name", "prompt", "file_name"],
    },
}
