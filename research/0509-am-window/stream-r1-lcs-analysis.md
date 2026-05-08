# Stream-R1 × LCS Integration Analysis
**Date:** 2026-05-08 21:03 UTC (0509-AM Window)
**Status:** READY FOR KERNEL — GPU required for implementation

---

## Stream-R1 Core Mechanism (from README)

Stream-R1 modulates the DMD generator loss:

```
L_Stream-R1 = exp(β · r_final) · mean(W_intra ⊙ L_DMD)
```

Three reward-guided components from ONE shared video reward model (VideoReward):

### 1. Inter-Reliability Weighting (W_inter)
- DMD gradient g = f_fake − f_real varies in reliability across rollouts
- Each rollout's loss is exponentially rescaled by `exp(β · r_final)`
- **Reliable rollouts dominate; low-quality rollouts are attenuated**
- This is a per-rollout scalar weight derived from the final reward

### 2. Intra-Per-Perplexity Weighting (W_intra)
- Back-propagates reward model to get per-pixel saliency volume S ∈ R^{F×H×W}
- Factorized into: temporal profile + per-frame spatial maps
- Product used as W_intra
- **Optimization pressure concentrates on regions/frames where reward landscape has NOT YET FLATTENED**
- Key config: `spatial_reward=true`, `spatial_reward_pixel_grad=true`, `temporal_saliency_weighting=true`
- `spatial_reward_min_weight=0.15`, `temporal_saliency_min_weight=0.2`

### 3. Adaptive Reward Balancing
- Tracks per-axis (VQ/MQ/TA) improvement in sliding window
- Subtracts std of per-axis deltas from reward
- Keeps three quality axes improving at similar rates

---

## LCS Integration Path

### Hypothesis: DINOv2 L2 as Semantic Reward Signal

The Intra-Perplexity mechanism's key insight — concentrating optimization where "reward landscape has not yet flattened" — maps directly to LCS-guided optimization.

**LCS connection:**
- LCS uses DINOv2 L2 distance as semantic drift metric during interpolation
- Stream-R1 Intra-Perplexity uses VideoReward gradient saliency to find "unflattened" regions
- **DINOv2 L2 distance could replace VideoReward as the Inter-Reliability rollout weight signal**
  - High L2 distance (high semantic drift) → unreliable rollout → low weight via `exp(β · r)`
  - Low L2 distance (semantic consistency) → reliable rollout → high weight

**Why DINOv2 L2 > VBench reward:**
- VBench reward is orthogonal to DINOv2 L2 (confirmed by prior analysis)
- VBench: per-frame quality / aesthetic scoring
- DINOv2 L2: semantic structure preservation across frames
- Combining them = both axes improve simultaneously

### Concrete LCS+Stream-R1 Algorithm

```
For each interpolation step t:
  1. Generate two rollouts: anchor-guided interpolation (σ_t) vs reference (σ_ref)
  2. Compute DINOv2 L2 distance: r_sem = -||DINOv2(σ_t) - DINOv2(σ_ref)||₂
  3. Inter-Reliability: weight = exp(β · r_sem) — high drift → low weight
  4. Intra-Perplexity: compute per-pixel saliency S from r_sem gradient
  5. Apply weighted DMD loss with W_inter and W_intra
  6. Adaptive balancing: ensure semantic axis doesn't degrade
```

### Alternative: Intra-Perplexity for Latent Space Navigation

Instead of using DINOv2 L2 as reward in Stream-R1's framework, use Intra-Perplexity's saliency mechanism to guide WHICH latent dimensions LCS should optimize:

- Run LCS interpolation → compute per-patch DINOv2 L2 distances
- Get spatial saliency map: which patches have highest semantic drift?
- Use this as W_intra to concentrate LCS optimization on high-drift regions
- This is a NAVIGATION aid — tells you WHERE to optimize, not WHAT reward to optimize for

---

## Scalpel Assessment (7/10 — HIGH PRIORITY MONITOR)

**Strengths:**
- Intra-Perplexity is the most concrete LCS complement found (higher than Tuna-2)
- Per-pixel/frame saliency = missing piece for LCS-guided spatial optimization
- Code+weights released ✅
- Single reward model architecture makes integration tractable

**Weaknesses:**
- **≥24GB GPU for inference, ≥80GB for training (8 GPUs)** — currently unavailable
- VideoReward model (KlingTeam) is a specific video quality model — may not capture semantic drift
- 1000 × 8 steps training recipe is heavy for our resource constraints
- No CPU-friendly path described

**Strategic relevance to LCS:**
- Intra-Perplexity spatiotemporal weight design = conceptually equivalent to "where should LCS concentrate its semantic consistency effort?"
- This is a FRAMEWORK complement, not a direct LCS component
- True integration requires: (1) GPU restore, (2) replace VideoReward with DINOv2 L2 distance

---

## Next Action (KERNEL blocked on GPU)

1. **GPU restore** → implement LCS+Intra-Perplexity hybrid in `idea_b_coco_vae.py`
2. Replace VideoReward with DINOv2 L2 distance computation
3. Use per-patch saliency to weight interpolation loss

**Until GPU restore: no action possible.**
