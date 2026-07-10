# PNG Embedded Metadata Extraction

## Problem

You need to understand the contents of a reference image (e.g. a cat photo or AI-generated artwork) but `vision_analyze` cannot access local files — the current model lacks native vision, and the fallback vision model may not work reliably.

## Solution: Extract Embedded Prompt Metadata from PNG

Many AI-generated images (ComfyUI, AUTOMATIC1111, Midjourney, DALL-E) store their generation parameters as metadata embedded in the PNG/JPEG file. The most common storage for ComfyUI is a `tEXt` PNG chunk with key `prompt` containing a JSON-serialized workflow.

### Step 1: Check if the file is PNG and has metadata

```python
python3 -c "
with open('/path/to/image.png', 'rb') as f:
    data = f.read()
# Check PNG signature
print('PNG:', data[:8] == b'\\x89PNG\\r\\n\\x1a\\n')
"
```

### Step 2: Extract all tEXt chunks

Write a Python script to read the PNG file and extract text chunks:

```python
import json

with open('/path/to/image.png', 'rb') as f:
    data = f.read()

try:
    pos = 8  # skip PNG signature
    while pos < len(data):
        length = int.from_bytes(data[pos:pos+4], 'big')
        chunk_type = data[pos+4:pos+8].decode('ascii', errors='replace')
        chunk_data = data[pos+8:pos+8+length]
        if chunk_type == 'tEXt':
            text = chunk_data.decode('utf-8', errors='replace')
            if 'prompt' in text[:10]:
                null_pos = text.index('\x00')
                value = text[null_pos+1:]
                prompt_data = json.loads(value)
                for node_id, node in prompt_data.items():
                    if isinstance(node, dict) and 'inputs' in node:
                        for k, v in node['inputs'].items():
                            if isinstance(v, str) and len(v) > 10:
                                print(f'Node {node_id} ({node.get("class_type", "?")}):')
                                print(f'  {k} = {v[:800]}')
        pos += 12 + length
        if pos >= len(data):
            break
except Exception as e:
    print(f'Error: {e}')
```

### Step 3: For JPEG — extract EXIF metadata

```bash
exiftool /path/to/image.jpg | grep -iP "prompt|parameters|workflow|description"
```

### Example

This technique was used in the "summer_cat_photos" project. The reference image was a 1024×1024 PNG with embedded ComfyUI workflow in a `tEXt` chunk. The positive prompt was discovered from Node 103 (PrimitiveStringMultiline):

```
"A photorealistic portrait of a silver-gray tabby cat with black tabby stripes,
clear M-shaped marking on forehead, pale yellow-green eyes, pinkish-brown nose,
white-tipped paws, round face, studio lighting, shallow depth of field, 4K,
professional pet photography"
```

This allowed generating 5 consistent follow-up images even though `vision_analyze` could not see the original.

## Limitations

- JPEG files with GenIC tags may use different metadata formats — try `exiftool` or check for XMP metadata.
- Midjourney stores prompt data in the filename, not embedded metadata.
- Not all images have embedded prompts — purely hand-drawn/scanned images won't have this data.
- The JSON structure varies between ComfyUI versions; adapt the extraction logic if needed.