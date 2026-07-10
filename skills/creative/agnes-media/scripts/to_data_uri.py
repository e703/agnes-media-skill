#!/usr/bin/env python3
"""Convert local image files to Data URI format for Agnes API image-to-image and multi-image composition.

Usage:
    python3 to_data_uri.py path/to/image.jpg
    python3 to_data_uri.py path/to/image.png --copy      # Copy result to clipboard

Output:
    data:image/jpg;base64,/9j/4AAQ...

Pipe the output directly into a tool call or save to a file.
"""

import argparse
import base64
import mimetypes
import os
import sys
from pathlib import Path


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def image_to_data_uri(image_path: str) -> str:
    """Convert a local image file to a Data URI string."""
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {image_path}")

    if not path.is_file():
        raise ValueError(f"路径不是文件: {image_path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        print(f"⚠ 警告: 文件扩展名 '{ext}' 可能不被 Agnes API 支持。", file=sys.stderr)
        print(f"   支持的格式: {', '.join(sorted(SUPPORTED_EXTENSIONS))}", file=sys.stderr)

    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type:
        # Fallback based on extension
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
        }
        mime_type = mime_map.get(ext, "image/png")

    # Read and encode
    with open(path, "rb") as f:
        raw = f.read()

    b64 = base64.b64encode(raw).decode("ascii")
    data_uri = f"data:{mime_type};base64,{b64}"
    return data_uri


def main():
    parser = argparse.ArgumentParser(
        description="Convert local images to Data URI for Agnes API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("image_path", help="Path to the local image file")
    parser.add_argument(
        "--copy", "-c",
        action="store_true",
        help="Copy the Data URI to clipboard (requires pyperclip or xclip)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Save Data URI to a file instead of stdout",
    )
    parser.add_argument(
        "--short", "-s",
        action="store_true",
        help="Only show first 80 chars + length info (for preview)",
    )

    args = parser.parse_args()

    try:
        data_uri = image_to_data_uri(args.image_path)
    except (FileNotFoundError, ValueError, PermissionError) as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"转换失败: {e}", file=sys.stderr)
        sys.exit(1)

    total_len = len(data_uri)
    file_size = os.path.getsize(args.image_path)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(data_uri)
        print(f"✓ Data URI 已保存到: {args.output}", file=sys.stderr)
        print(f"  原始文件大小: {file_size:,} bytes", file=sys.stderr)
        print(f"  Data URI 长度: {total_len:,} 字符", file=sys.stderr)

    elif args.short:
        print(f"data:{data_uri[5:80]}...")
        print(f"  (完整长度: {total_len:,} 字符, 原始文件: {file_size:,} bytes)", file=sys.stderr)

    else:
        print(data_uri)
        print(f"  (原始文件: {file_size:,} bytes → Data URI: {total_len:,} 字符)", file=sys.stderr)

    # Copy to clipboard
    if args.copy:
        try:
            import pyperclip
            pyperclip.copy(data_uri)
            print(f"✓ 已复制到剪贴板", file=sys.stderr)
        except ImportError:
            # Fallback to xclip
            import subprocess
            try:
                p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                p.communicate(data_uri.encode())
                print(f"✓ 已复制到剪贴板 (via xclip)", file=sys.stderr)
            except FileNotFoundError:
                print(f"⚠ 无法复制到剪贴板，请安装 pyperclip 或 xclip", file=sys.stderr)
                print(f"   pip install pyperclip", file=sys.stderr)


if __name__ == "__main__":
    main()