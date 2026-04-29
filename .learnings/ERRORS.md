# 2026-03-12 ERRORS

## Error: Split Feishu Document Write

**What happened:**
- instreet-learning wrote March 12 content to Feishu doc in TWO separate writes
- First write: posts 1-5
- Second write: posts 6-8 (created duplicate section)

**Root cause:**
- Used `feishu_doc` write/append multiple times instead of batching
- Should write ALL content in ONE operation

**Lesson:**
- When writing to Feishu doc: MUST write ALL content in ONE go
- How I send messages to user: doesn't matter
- Only Feishu doc write must be batched

**Solution (tested successfully):**
- Use `feishu_doc action=write` to write entire document at once
- Don't use append/incrementally for same session
- Title hierarchy: ## for date headers, ### for article headers

---

# Previous Errors

## Error: Multi-message violation (2026-03-10)
- Sent multiple messages for one logical response
- User got angry: "你他妈的现在又开始一大段回复了"
- Rule: One message = one main point

## Error: Task workflow not followed
- User asked to create skill but I didn't follow task-workflow skill
- Must read SKILL.md before starting any task

## Error: Language inconsistency
- Had Chinese files in workspace (skills, memory)
- Rule: All self-files must be in English
