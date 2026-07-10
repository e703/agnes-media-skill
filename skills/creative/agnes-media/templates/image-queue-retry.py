#!/usr/bin/env python3
"""Agnes Image Queue Retry — handles 503 queue-full errors with long retry.

The Agnes image generation API frequently returns 503 "image queue is full" under load.
This is a transient condition, not a real error. This script provides a reusable retry
wrapper with the recommended 30s delay and 10+ max attempts.

Usage:
    python3 image-queue-retry.py --prompt "A cat" --output cat.png
    python3 image-queue-retry.py --prompt "edit this" --image "https://..." --output edited.png
    python3 image-queue-retry.py --prompt "combine" --image "url1" "url2" --output combined.png
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


# Defaults — overridable via env
API_KEY = os.environ.get("AGNES_API_KEY") or os.environ.get("API_KEY", "")
ENDPOINT = os.environ.get(
    "AGNES_IMAGE_ENDPOINT",
    "https://apihub.agnes-ai.com/v1/images/generations",
)
MODEL = os.environ.get("AGNES_IMAGE_MODEL", "agnes-image-2.0-flash")
MAX_RETRIES = int(os.environ.get("AGNES_MAX_RETRIES", "10"))
RETRY_DELAY = float(os.environ.get("AGNES_RETRY_DELAY", "30"))
REQUEST_TIMEOUT = int(os.environ.get("AGNES_IMAGE_TIMEOUT", "180"))


def generate_image(
    prompt: str,
    output_path: str,
    images: list[str] | None = None,
    size: str = "1024x1024",
) -> dict:
    """Submit image generation with retry for 503 queue-full errors."""

    if not API_KEY:
        return {"ok": False, "error": "AGNES_API_KEY not set"}

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "n": 1,
        "size": size,
    }

    if images:
        payload["extra_body"] = {"image": images}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            break
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:2000]
            last_err = exc

            # Queue full — retry with long delay
            if exc.code == 503:
                print(
                    f"  ⏳ 尝试 {attempt}/{MAX_RETRIES} — 队列已满，等待 {RETRY_DELAY}s...",
                    file=sys.stderr,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue

            # Other retryable status codes
            elif exc.code in (429, 500, 502, 504):
                delay = RETRY_DELAY * (attempt)
                print(
                    f"  ⏳ 尝试 {attempt}/{MAX_RETRIES} — HTTP {exc.code}，等待 {delay:.0f}s...",
                    file=sys.stderr,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(delay)
                    continue

            # Non-retryable
            return {
                "ok": False,
                "error": f"HTTP {exc.code}",
                "detail": body,
            }

        except urllib.error.URLError as exc:
            last_err = exc
            delay = RETRY_DELAY * attempt
            print(
                f"  ⏳ 尝试 {attempt}/{MAX_RETRIES} — 网络错误，等待 {delay:.0f}s...",
                file=sys.stderr,
            )
            if attempt < MAX_RETRIES:
                time.sleep(delay)
                continue
    else:
        return {
            "ok": False,
            "error": f"请求失败 {MAX_RETRIES} 次后放弃",
            "detail": str(last_err),
        }

    # Parse response
    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        return {"ok": False, "error": f"非 JSON 响应: {body[:500]}"}

    # Extract URL
    url = None
    if isinstance(result.get("data"), list) and result["data"]:
        first = result["data"][0]
        url = first.get("url")

    if not url:
        return {
            "ok": False,
            "error": "响应中未找到图片 URL",
            "raw": result,
        }

    # Download
    print(f"  ↓ 下载: {url}", file=sys.stderr)
    try:
        dl_req = urllib.request.Request(url, headers={"User-Agent": "Agnes-Retry/1.0"})
        with urllib.request.urlopen(dl_req, timeout=REQUEST_TIMEOUT) as resp:
            content = resp.read()
    except Exception as e:
        return {"ok": False, "error": f"下载失败: {e}"}

    # Save
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(content)

    return {
        "ok": True,
        "path": str(out.resolve()),
        "bytes": len(content),
        "remote_url": url,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Agnes image generation with queue-full retry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--prompt", "-p", required=True, help="Image prompt")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    parser.add_argument("--image", "-i", nargs="*", help="Image URL(s) for i2i/multi")
    parser.add_argument("--size", "-s", default="1024x1024", help="Image size (WxH)")

    args = parser.parse_args()

    print(f"→ 生成图像: {args.prompt[:60]}...", file=sys.stderr)
    if args.image:
        print(f"  参考图片: {len(args.image)} 张", file=sys.stderr)

    result = generate_image(
        prompt=args.prompt,
        output_path=args.output,
        images=args.image,
        size=args.size,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()