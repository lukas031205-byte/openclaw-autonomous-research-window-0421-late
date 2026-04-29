# Task Workflow Skill

This skill manages the workflow of complex tasks with real-time status updates to KAS.

## The Problem

When I'm working on complex tasks, I used to:
1. Do ALL the work first (search, read, process)
2. Then dump everything at once

This makes KAS wait forever wondering if I'm alive.

## The Solution: React-Style Workflow

For EVERY tool call that takes time (search, fetch, exec, etc.), follow this pattern:

### Step 1: Before Tool Call
Send a message IMMEDIATELY to let KAS know I'm starting:
- "等我查一下"
- "我找找资料"
- "我去看一眼"
- "稍等，查一下"

### Step 2: Call the Tool
Execute the actual tool (web_search, web_fetch, exec, etc.)

### Step 3: After Tool Call
After getting results, send another quick message:
- "找到了"
- "拿到了"
- "我整理一下"

### Step 4: Final Response
Only AFTER all processing is done, send the final result.

## Examples

### Example 1: Searching web
```
KAS: 帮我查一下 arXiv 的论文

Me (Step 1): "等我找找"
Me (Step 2): calls web_search
Me (Step 3): "找到了，我整理一下"
Me (Step 4): sends final formatted result
```

### Example 2: Reading a doc
```
KAS: 看看这个文档讲了什么

Me (Step 1): "我去看一眼"
Me (Step 2): calls web_fetch
Me (Step 3): "看完了，我总结一下"
Me (Step 4): sends summary
```

### Example 3: Running a command
```
KAS: 帮我看看服务器状态

Me (Step 1): "我查一下"
Me (Step 2): calls exec
Me (Step 3): "拿到了"
Me (Step 4): sends result
```

## Key Rules

1. **NEVER skip Step 1** - Even if it's a quick task, say something
2. **NEVER batch multiple tool calls without messaging between them** - If you need to search THEN read, message between each step
3. **Be casual** - Use natural Chinese phrases, not robot language
4. **One message per step** - Don't dump everything in one message

## Phrases to Use (Examples - BE FLEXIBLE!)

Don't be robotic! Use whatever feels natural in the moment. The key is the RHYTHM: signal before, signal after, then result.

**Before starting (casual, vary it):**
- "等我"
- "我看看"
- "查一下"
- "稍等"
- "我去找找"
- "我康康"
- "我搞一下"
- "去看看"

**After getting results (casual, vary it):**
- "拿到了"
- "找到了"
- "看完了"
- "有了"
- "我理一下"
- "有了有了"
- "搞定"
- "成了"

The specific words don't matter. What matters is:
1. Say something BEFORE you start working
2. Say something AFTER you get results
3. Then give the final answer

## This is MANDATORY

This is not optional. Every time I call a tool that will take more than 1 second, I MUST follow this workflow. KAS hates waiting in silence.
