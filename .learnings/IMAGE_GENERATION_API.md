# Image Generation API

## MiniMax API (PRIMARY - Working 2026-03-24)
- **API URL**: `https://api.minimaxi.com`
- **Model**: `image-01` (or `image-01-live`)
- **Endpoint**: `/v1/image_generation`
- **API Key**: stored in TOOLS.md

### Minimax Image Generation (exec curl):
```bash
curl -s -X POST https://api.minimaxi.com/v1/image_generation \
  -H "Authorization: Bearer <MINIMAX_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "image-01",
    "prompt": "your prompt",
    "aspect_ratio": "16:9",
    "response_format": "url",
    "n": 1
  }'
```

### Minimax Image Download:
```bash
# URL expires in 24 hours
curl -s -o /tmp/image.jpg "<OSS_URL>"
```

## Proxy API (lemonapi) - NOT WORKING
- **API URL**: https://new.lemonapi.site/v1
- **API Key**: sk-VVxRJEEZfLu8XcelzL0dizKigbbXx6bAXsvFpR00TU0BmUsh
- **Status**: Image generation returns invalid/expired URLs, NOT recommended

## Previous Attempted (Failed)
- Using [L]gemini-3-pro-preview via chat/completions - returned fake URLs
- DO NOT use for image generation

## Usage with Feishu
1. Generate image via Minimax API → get OSS URL
2. Download to /tmp/
3. Upload to Feishu (exec curl /im/v1/images) → get image_key
4. Send via Feishu Messages API (exec curl /im/v1/messages with msg_type=image)

See FEISHU_IMAGE_SENDING.md for full workflow.

## Last Updated
2026-03-24
