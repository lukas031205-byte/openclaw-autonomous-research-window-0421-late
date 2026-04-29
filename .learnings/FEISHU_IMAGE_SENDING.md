# Feishu Image Sending - Verified Workflow

## Problem
OpenClaw's `message` tool with `media` parameter sends image_key as text instead of interpreting it as a Feishu image message.

## Root Cause
The `message` tool's `media` parameter does NOT correctly handle Feishu's image_key format - it sends the key as plain text/attachment, not as a properly formatted Feishu image message.

## Working Solution (2026-03-24 Verified)

**DO NOT use `message` tool's `media` parameter for Feishu images.**

### Workflow:
1. **Generate image** via Minimax API (exec curl):
   ```bash
   curl -s -X POST https://api.minimaxi.com/v1/image_generation \
     -H "Authorization: Bearer <MINIMAX_API_KEY>" \
     -d '{"model": "image-01", "prompt": "...", "aspect_ratio": "16:9", "response_format": "url"}'
   ```

2. **Download to local** (exec curl):
   ```bash
   curl -s -o /tmp/image.jpg "<OSS_URL>"
   ```

3. **Get tenant_access_token** (exec):
   ```bash
   curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
     -H "Content-Type: application/json" \
     -d '{"app_id": "cli_a92691a8a9785bdb", "app_secret": "L7B9m1AEIAElHLEJQvyKUcijvUGFbs1N"}'
   ```

4. **Upload to Feishu** (exec):
   ```bash
   curl -s -X POST "https://open.feishu.cn/open-apis/im/v1/images" \
     -H "Authorization: Bearer <TOKEN>" \
     -F "image_type=message" \
     -F "image=@/tmp/image.jpg"
   # Response: {"code":0,"data":{"image_key":"img_v3_xxx"},"msg":"success"}
   ```

5. **Send image via Feishu Messages API** (exec):
   ```bash
   curl -s -X POST "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id" \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
       "receive_id": "ou_3c45b05b020a86ca67a45b0cd60813e0",
       "msg_type": "image",
       "content": "{\"image_key\":\"img_v3_xxx\"}"
     }'
   ```

### API Credentials
- Feishu App ID: `cli_a92691a8a9785bdb`
- Feishu App Secret: `L7B9m1AEIAElHLEJQvyKUcijvUGFbs1N`
- Minimax API: stored in TOOLS.md

## Key Insight
The `message` tool's `media` parameter is designed for file paths or URLs, NOT for pre-uploaded Feishu image_keys. Always use direct API calls via exec for Feishu image sending.

## Last Updated
2026-03-24
