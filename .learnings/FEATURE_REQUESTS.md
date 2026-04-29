# Feature Requests Log

## Format
See SKILL.md for full format template.

<!-- Add entries below -->

## Feishu Image Sending - SOLVED (2026-03-12)

**Problem**: OpenClaw message tool sends local image paths as text links instead of uploading to Feishu

**Root Cause**: 
1. `mediaLocalRoots` config missing `/home/kas` path
2. Feishu app missing `im:resource:upload` permission

**Solution Implemented**:
- Use subagent with direct Feishu API calls (upload image → get image_key → send message)
- See FEISHU_IMAGE_SENDING.md for detailed steps

**Status**: ✅ SOLVED - Can now send images directly to Feishu
