#!/usr/bin/env python3
"""Monitor a keyframe animation task, polling every 30s, download on completion.

Usage:
  1. Edit VIDEO_ID, PROJECT_DIR, OUTPUT_FILE, and KEYFRAME_LABELS below
  2. Run via terminal(background=True, notify_on_complete=True, timeout=600)
  3. The script loops every 30s, prints status, and exits when done
"""
import json, os, subprocess, sys, time, datetime

# === CONFIGURE THESE ===
VIDEO_ID = "video_YOUR_VIDEO_ID_HERE"
PROJECT_DIR = "/home/alan/workspace/YOUR_PROJECT"
OUTPUT_FILE = "keyframe_animation.mp4"
# Describe the keyframes for the progress message
KEYFRAME_LABELS = ["keyframe 1", "keyframe 2", "keyframe 3"]
# =======================

api_key = os.environ.get("AGNES_API_KEY")
if not api_key:
    print("ERROR: AGNES_API_KEY not set")
    sys.exit(1)

os.makedirs(f"{PROJECT_DIR}/target/videos", exist_ok=True)
poll_count = 0

while True:
    poll_count += 1
    cmd = [
        "curl", "-s", "--location",
        "-X", "GET",
        f"https://apihub.agnes-ai.com/agnesapi?video_id={VIDEO_ID}",
        "-H", f"Authorization: Bearer {api_key}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠ API parse error, retrying...")
        time.sleep(30)
        continue

    status = data.get("status", "unknown")
    progress = data.get("progress", 0)
    seconds = data.get("seconds", "?")
    size = data.get("size", "?")
    perf = data.get("perf_params", {})
    frame_rate = perf.get("frame_rate", "?")
    num_frames = perf.get("num_frames", "?")
    url = data.get("url")
    error = data.get("error")

    print("=" * 50)
    print(f"🎬 关键帧动画监控")
    print(f"📊 状态: {status} ({progress}%)")
    print(f"⏱ 时长: {seconds}s | 📐 分辨率: {size}")
    print(f"🎞 帧数: {num_frames}帧 @ {frame_rate}fps")
    print(f"🔄 轮询 #{poll_count} | 🕐 {datetime.datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)

    if status == "completed" and url:
        dl_cmd = ["curl", "-sL", url, "-o", f"{PROJECT_DIR}/target/videos/{OUTPUT_FILE}"]
        print("⬇ 下载中...")
        subprocess.run(dl_cmd, timeout=120)
        file_size = os.path.getsize(f"{PROJECT_DIR}/target/videos/{OUTPUT_FILE}")
        print(f"\n✅ 关键帧动画生成完成！")
        print(f"📁 文件: {PROJECT_DIR}/target/videos/{OUTPUT_FILE}")
        print(f"📏 大小: {file_size/1024/1024:.1f}MB")
        labels_str = " → ".join(KEYFRAME_LABELS)
        print(f"🎞 关键帧序列: {labels_str}")
        print(f"📎 MEDIA:{PROJECT_DIR}/target/videos/{OUTPUT_FILE}")
        sys.exit(0)
    elif status == "failed":
        print(f"\n❌ 生成失败: {error}")
        sys.exit(1)
    else:
        time.sleep(30)