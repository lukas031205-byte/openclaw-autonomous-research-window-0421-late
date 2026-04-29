# HEARTBEAT.md

## Harness Heartbeat Policy

Heartbeat is now a light pulse, not a freeform autonomous worker.

Rules:

- Do not write durable long-term memory directly.
- Do not silently mix background observations into the main conversation.
- Prefer creating triggers, task briefs, and memory candidates through Harness tools.
- If a heartbeat produces reusable lessons, stage them with `memory_bridge_candidate_create`; never commit them directly.
- If a check is low-value or noisy, batch it instead of escalating immediately.

## Every 30 minutes: lightweight health sampling

### 1. Sample public endpoints

- Fetch `https://dashboard.kasssssss.com/`
- Fetch `https://watchclaw.kasssssss.com/`

### 2. Sample local dependencies

- Local 8080: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/`
- Local 19000: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:19000/`
- cloudflared presence: `ps aux | grep cloudflared | grep -v grep`

### 3. Route all findings through Harness

- For each observation, use `harness_trigger_ingest`.
- Healthy/no-change observations should usually become `batch` or `ignore`.
- Repeated failures on the same target should share one `dedupeKey`.
- Only create a task or alert when the trigger policy says it matters.
- If there are mature batched triggers, flush them with `harness_trigger_batch_flush` instead of opening new duplicate loops.
- For repeated but non-urgent patterns, use `memory_bridge_flush` or a `memory_bridge_candidate_create` only after summarizing the pattern with provenance.

Suggested trigger kinds:

- `state_trigger` for service status changes
- `content_trigger` for broken pages or error bodies
- `reflection_trigger` if the same failure repeats and current policy is insufficient

### 4. Recovery policy

- If a local process is clearly down and restart is safe, Kernel may restart it.
- After any restart, create another `harness_trigger_ingest` with the post-recovery result.
- If confidence is low, escalate to Domain instead of improvising.

### Recovery commands

```bash
# Restart http.server (dashboard)
cd /home/kas/.openclaw/workspace-domain/public && python3 -m http.server 8080 &

# Restart Star-Office-UI (watchclaw)
cd /home/kas/github/Star-Office-UI/backend && python3 app.py &

# Restart cloudflared
/home/kas/.local/bin/cloudflared tunnel --config /home/kas/.cloudflared/config.yml run dashboard &
```
