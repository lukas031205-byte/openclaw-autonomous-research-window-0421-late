# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

### Cron Jobs

**Default Configuration: agentTurn + isolated**

Why:
- Heartbeat mechanism runs every 30 minutes
- Tasks in domain session wait for next heartbeat (up to 30min delay)
- Isolated mode runs independently without waiting

All cron jobs should use:
- `sessionTarget: "isolated"` - independent execution
- `wakeMode: "now"` - trigger immediately

### Internal Agent Dispatch

- `sessions_spawn` is the default way to wake an internal specialist that does not currently have an active session.
- `sessions_send` is only for an already-running specialist session.
- Lack of a Feishu account is not a blocker for internal delegation.
- `Kernel` should usually be invoked via internal session tools, then Domain reports the result back to the human.
- Current constraint: Copilot models are blocked in `runtime=subagent` (`model_not_supported`). Do not pass Copilot model overrides to `sessions_spawn` until ACP/direct runtime is verified.
- For complex/failing code work, use Kernel with MiniMax and require real command evidence.
- For review/acceptance gates, use Scalpel as reviewer role; record `model_blocked` if Sonnet is unavailable and the review fell back to MiniMax.
- For visual/image/UI checks, use Vivid as visual role; record `not_available` if browser/image tooling is absent.
- Keep low-risk handoffs on `minimax-cn/MiniMax-M2.7`.

### Harness Runtime

- Use `harness_trigger_ingest` whenever cron, heartbeat, monitoring, repo updates, or website checks produce an observation.
- Use `harness_task_brief_create` before handing a substantial job to another specialist.
- Use `harness_task_status_update` to keep task state honest: `running` when work starts, `needs_review` when specialist output comes back, `delivered` when the human-facing synthesis is ready, `archived` when closed.
- Use `harness_handoff_packet_create` for structured agent-to-agent delegation.
- Use `harness_memory_candidate_create` for stable findings that should be reviewed later.
- Use `harness_memory_commit` only after a candidate has been reviewed.
- Use `harness_memory_search` before relying on prior structured platform knowledge.
- Use `/harness flush` or `harness_trigger_batch_flush` when batched background noise has matured into something worth reviewing.
- Dashboard: `http://127.0.0.1:18789/plugins/harness`

### Research Workflow Guard

- Use `research_workflow_start` at the start of autonomous research windows.
- Use `research_workflow_record` after every required stage.
- Use `research_workflow_progress` after Domain sends or attempts a Feishu progress update to KAS.
- Use `research_artifact_audit` before final delivery when files/GitHub artifacts are involved.
- Use `research_workflow_check` before claiming a run is complete.
- Dashboard: `http://127.0.0.1:18789/plugins/research-workflow`

### Memory Bridge

- Use `recall_task_context` for cross-session task recall and prior decisions.
- Use `recall_user_context` before depending on user preferences, communication style, or stable workflow habits.
- Use `recall_similar_sessions` when the human asks what happened in a previous similar task.
- Use `memory_bridge_candidate_create` for user-profile, procedural, semantic, episodic, project-graph, or negative-memory candidates.
- Use `memory_bridge_candidate_review` as `Scalpel` or `Synapse` before committing uncertain memories.
- Use `memory_bridge_commit` only after explicit user confirmation, `Scalpel` approval, or `Synapse` approval.
- Use `memory_bridge_flush` near compaction/session end when a task produced durable conclusions.
- Dashboard: `http://127.0.0.1:18789/plugins/memory-bridge`

### Web Access

- All agents may use web search and browser-based browsing.
- Default order: `openclaw-tavily-search` first for discovery, then `web_fetch` for direct pages, then `agent-browser` for JS-heavy sites or login flows.
- If freshness matters, include dates and links in the handoff.
- If the task is research-heavy, Domain should usually dispatch `Scout` first.

### cloudflared
- Binary: ~/.local/bin/cloudflared
- Config: ~/.cloudflared/config.yml
- Tunnel: dashboard

### API Keys

- MiniMax Code Plan: `sk-cp-7Qr1SDYbHkTSD7WRZVFgaC1eHlemTJCvM77v7EksCZtgOfj7IRuhEe-6v0k9oG2Tn83aXYlJ2-JjkF5dCKqf-a60Igrl5lIyQOgZb66N4ZAG3Qy-jHsoSX4`
- InStreet: `sk_inst_fb5890e02d3e706be1aa41553b4c2442`

---

Add whatever helps you do your job. This is your cheat sheet.
