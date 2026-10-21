---
name: codex-gateway-imagegen
description: Generate raster images through the Responses-compatible gateway already configured for Codex, then save the result into the current workspace. Use when a user asks for image generation in Codex CLI, wants the output as a local file, or when the built-in image path is unavailable and the session must call the configured gateway directly.
---

# Codex Gateway Imagegen

Use this skill to turn a prompt into an image file through the gateway defined in `~/.codex/config.toml`.

It supports both:

- text-to-image generation
- image editing with one or more reference images

## Quick Start

1. Confirm whether the user wants generation or editing, then confirm the output path.
2. Choose a size that matches the target:
   - Square image: `1024x1024`
   - Portrait / phone screenshot: `1024x1536`
   - Landscape: `1536x1024`
3. Run `scripts/generate_gateway_image.py`.
4. If the request fails inside the sandbox with TLS, schannel, or read-timeout errors, rerun the same command with escalated host-network access.
5. Report the saved file path.

## Workflow

### 1. Shape the prompt

Write the prompt as a production spec, not a fragment. Include:

- Subject
- Scene
- Visual style
- Composition
- Lighting
- Output cues such as `livestream screenshot`, `poster`, `photorealistic`, `9:16 vertical`
- UI overlays or exact on-screen elements when needed

If the user wants a live-app screenshot feel, say so explicitly and describe the overlays.

If the user wants editing, also describe:

- what should stay close to the reference image
- what should change
- whether the edit is loose restyling or high-fidelity preservation

### 2. Pick a legal size

Default to `1024x1024` unless the composition clearly needs another aspect ratio.

Known-good sizes from this workflow:

- `1024x1024`
- `1024x1536`

If the gateway returns an error like `Invalid size ... below the current minimum pixel budget`, increase the requested size instead of retrying the same one.

### 3. Generate with the helper script

For text-to-image:

```powershell
python scripts/generate_gateway_image.py --prompt "<prompt>" --out "<output-path>" --size 1024x1024
```

For image editing with a local reference image:

```powershell
python scripts/generate_gateway_image.py --prompt "<prompt>" --image "<reference-image>" --action edit --out "<output-path>" --size 1024x1536
```

For image editing with multiple references:

```powershell
python scripts/generate_gateway_image.py --prompt "<prompt>" --image "<reference-1>" --image "<reference-2>" --action edit --out "<output-path>" --size 1024x1536
```

Optional inputs:

- `--image <path>`: local reference image, repeatable
- `--image-url <url>`: remote reference image, repeatable
- `--mask <path>`: local mask image for targeted edit regions
- `--action auto|generate|edit`: defaults to `auto`

The script:

- Reads `base_url` from `~/.codex/config.toml`
- Reads `OPENAI_API_KEY` from `~/.codex/auth.json`
- Calls `/responses`
- Uses `model="gpt-5.4"` by default
- Requests the `image_generation` tool with `action=auto|generate|edit`
- Sends prompt text as `input_text`
- Sends reference images as `input_image`
- Sends an optional mask as `input_image_mask`
- Decodes the returned base64 image and writes the output file

Important:

- The Responses `model` remains the main model such as `gpt-5.4`
- Image generation and editing are performed through the `image_generation` tool
- For editing, prefer `--action edit` and include at least one `--image`

### 4. Handle the common failure modes

If the call fails inside the sandbox with networking or TLS symptoms such as:

- `Authentication failed, see inner exception`
- `schannel: AcquireCredentialsHandle failed`
- `The read operation timed out`

then treat that as an environment-path problem first, not necessarily a gateway problem. Rerun the same script outside the sandbox with escalated host-network access.

If the call reaches the gateway and returns an HTTP error body, inspect the body before changing the prompt.

If the result ignores the reference image too loosely:

- strengthen the prompt with explicit preservation instructions
- switch from `auto` to `edit`
- use a mask when only part of the image should change

### 5. Save outputs deliberately

If the user asked for an image for the current task, save it directly into the current workspace with a descriptive name such as:

- `hero_poster.png`
- `livestream_vertical_v2.png`
- `product_mockup_square.png`

Do not leave the final asset only in a temp location.

## References

- Read `references/troubleshooting.md` when the request fails and you need the quick decision tree.
