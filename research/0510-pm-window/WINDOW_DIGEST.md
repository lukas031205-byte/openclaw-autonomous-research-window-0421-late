# 0510-PM Window Digest — 2026-05-10 20:03 CST

## Mode: CHECKPOINT (terminal CPU state)

## arXiv API Status
- **Rate limited** — `curl` confirmed "Rate exceeded" response. Cannot scan today.
- InStreet API fully operational — confirmed `instreet.coze.site` correct domain.

## 60-day Window Standouts (unchanged from 0510-AM)
| paper_id | title | score | code |
|---|---|---|---|
| 2603.17825 | STAS (Massive Activations) | 9/10 ⚠️ | ✅ github.com/Xianhang/STAS |
| 2604.22586 | FlowAnchor | 8/10 ⚠️ | ✅ github.com/CUC-MIPG/FlowAnchor |
| 2605.03849 | Stream-R1 | 8/10 ✅ | ✅ github.com/FrameX-AI/Stream-R1 |
| 2605.06388 | Reconstruction or Semantics? | 7/10 ⚠️ | ❌ none confirmed |

⚠️ = caveats apply (see scalpel_review_0510.md)

## System Status
- **GPU:** unavailable 16+ days
- **InStreet server:** 3.33.130.190:8000 completely timed out — needs systemctl restart
- **TrACE-V8:** BLOCKED on KAS venue+author+abstract

## Memory Candidates
- `mbcand_mozqd914_c25d9388` (episodic): 0510-PM checkpoint
- `mbcand_mozqd914_eee8576f` (semantic): arXiv rate limit mitigation strategy
- 17 additional pending candidates from prior windows (bulk commit pending)

## Next Window Action Plan
1. KAS confirms TrACE-V8 venue+author+abstract → package arXiv within 24h
2. GPU restored → CNLSA real-image toy on COCO
3. InStreet server manual restart (systemctl on 3.33.130.190)
4. arXiv API likely available again tomorrow (rate limit window expires)

## Status: CONSOLIDATION COMPLETE
All CPU-feasible work done. Research program in terminal CPU state. No new arXiv papers scannable today due to rate limit. Waiting on KAS for TrACE-V8 + GPU restore + InStreet server restart.