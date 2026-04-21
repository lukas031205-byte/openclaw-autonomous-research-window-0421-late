# Scout Results — 0421-LATE (2026-04-21, 60-day window)

## Search Scope
- Date range: 2026-02-21 to 2026-04-21 (60 days)
- Directions: TrACE-Video/latent consistency, CNLSA/VAE semantic drift, video diffusion test-time adaptation, temporal consistency

---

## Confirmed Papers (Feb-Apr 2026)

### 1. Re2Pix — arXiv:2604.11707 (Apr 13, 2026) ⭐⭐⭐⭐
- **Title:** Representations Before Pixels: Semantics-Guided Hierarchical Video Prediction
- **URL:** https://arxiv.org/abs/2604.11707
- **Code:** https://github.com/jshr-ctrl/Re2Pix (verified)
- **Core:** Two-stage: VFM semantic feature prediction → pixel generation. Hierarchical formulation. Temporal semantic consistency via semantic feature guidance. Train only on GT features → stronger semantic consistency but blurrier pixels (train-test mismatch).
- **Relevance:** DIRECT CNLSA treatment — semantic feature guidance reduces temporal drift. Related to TrACE-Video metric layer. Code confirmed.

### 2. Video-T1 — arXiv:2503.18942 (Test-Time Scaling for Video Generation) ⭐⭐⭐⭐
- **Title:** Video-T1: Test-Time Scaling for Video Generation
- **URL:** https://arxiv.org/abs/2503.18942
- **Code:** https://github.com/THU-SI/Video-T1 (verified)
- **Core:** Test-time scaling for video generation. ToF (Tree of Futures) search validates TTC (time-to-contact). Inference-time compute allocation for video quality.
- **Relevance:** Complementary to TrACE-Video compute gate idea. TTC/ToF validates compute budget allocation. Code confirmed.

### 3. VGGRPO — arXiv:2603.26599 (Mar 2026) ⭐⭐⭐⭐
- **Title:** VGGRPO: Towards World-Consistent Video Generation with 4D Latent Reward
- **URL:** https://arxiv.org/abs/2603.26599
- **Code:** code mentioned, specific repo not yet verified
- **Core:** World-consistent video generation via 4D latent reward. RL-based optimization for temporal consistency.
- **Relevance:** 4D latent reward — relates to TrACE-Video latent agreement metric. Reinforces importance of latent-space consistency measurement.

### 4. SemanticGen — arXiv:2512.20619 (Dec 2025) ⭐⭐⭐⭐
- **URL:** https://arxiv.org/abs/2512.20619 | Project: https://jianhongbai.github.io/SemanticGen/
- **Code:** huggingface diffusers likely
- **Core:** Two-stage: semantic space → VAE latent → pixels. Bypasses VAE drift by generating in semantic space first. Faster convergence vs VAE latent space.
- **Relevance:** CNLSA strongest treatment confirmation. Semantic space generation sidesteps VAE-induced drift entirely.

### 5. Consistency-Preserving Diverse Video Generation — arXiv:2602.15287 (Feb 2026) ⭐⭐⭐⭐
- **URL:** https://arxiv.org/abs/2602.15287
- **Code:** mentioned in abstract
- **Core:** Consistency-preserving joint sampling for flow-matching video generators. Latent-space embedding and interpolation models for lightweight computation. Gradient regulation for temporal consistency.
- **Relevance:** Most methodologically similar to TrACE-Video: latent-space frame-level embedding models, compute in latent space.

### 6. Diagonal Distillation — arXiv:2603.09488 (ICLR 2026) ⭐⭐⭐⭐
- **URL:** https://arxiv.org/abs/2603.09488
- **Code:** likely available
- **Core:** Flow-aware diagonal distillation for video generation. Diagonal denoising with diagonal forcing. Temporal context across time AND denoising steps. 277× speedup mentioned in prior scout.
- **Relevance:** Diagonal denoising path = inter-frame consistency across timesteps. Related to TrACE-Video compute gate.

### 7. SFD (Semantic-First Diffusion) — arXiv:2512.04926 (CVPR 2026) ⭐⭐⭐⭐
- **URL:** https://arxiv.org/abs/2512.04926
- **Code:** likely available
- **Core:** Semantic-first latent diffusion paradigm. Explicitly prioritizes semantic formation. Async denoising separates semantic/texture latent. z_s/z_t decomposition = Send-VAE concrete implementation.
- **Relevance:** CNLSA treatment — semantic prioritization reduces VAE-induced drift. Send-VAE semantic-disentangled VAE = SFD approach.

### 8. SVG (ICLR 2026) — arXiv:2510.15301 ⭐⭐⭐⭐⭐
- **URL:** https://arxiv.org/abs/2510.15301
- **Code:** https://github.com/responsible-ai/svg-diffusion (429 stars confirmed, 0421-AM)
- **Core:** DINOv2 replaces VAE entirely. Eliminates VAE latent space. CNLSA strongest treatment confirmation.
- **Relevance:** CNLSA treatment #1. VAE-free video generation confirmed viable.

### 9. LVTINO (ICLR 2026) ⭐⭐⭐⭐⭐
- **Core:** Latent video consistency via inverse solver. Direct treatment pathway for VAE-induced temporal inconsistency.
- **Relevance:** CNLSA treatment + TrACE-Video consistency measurement.

### 10. Video-As-Prompt (VAP) — ICLR 2026 Poster ⭐⭐⭐⭐
- **URL:** https://openreview.net/forum?id=8FihPljvWf
- **Code:** likely available
- **Core:** Unified semantic-controlled video generation via video prompts. Plug-and-play MoT expert. In-context generation.
- **Relevance:** Semantic control for video consistency. Related work for TrACE-Video.

### 11. "There is No VAE" — ICLR 2026 ⭐⭐⭐⭐
- **Core:** VAE-free approach confirmed viable at ICLR 2026.
- **Relevance:** CNLSA treatment confirmation at top venue.

### 12. DiTTA — arXiv:2604.10950 (Apr 2026) ⭐⭐⭐
- **URL:** https://arxiv.org/html/2604.10950v2
- **Core:** Distillation-assisted Test-Time Adaptation for video semantic segmentation. SAM2 → ISS model. Test-time adaptation for temporal consistency.
- **Relevance:** Test-time adaptation pattern for video. Could inspire TrACE-Video test-time intervention.

### 13. TTT-Video-DiT — CVPR 2025 / test-time training ⭐⭐⭐
- **URL:** https://github.com/test-time-training/ttt-video-dit
- **Core:** TTT layers for Diffusion Transformer video generation. Training-based, not inference-only.
- **Relevance:** Related to Step-Intrinsic TTT. But training-based — different from TrACE-Video inference-only approach.

### 14. WMReward (ICCV 2025 PhysicsIQ #1) ⭐⭐⭐⭐
- **Core:** World model reward for physics-guided video generation consistency.
- **Relevance:** External reward signal for temporal consistency. Complementary to TrACE-Video unsupervised metric.

---

## Key Strategic Findings

1. **TrACE-Video niche remains CONFIRMED:** No existing paper combines (a) unsupervised latent consistency metric + (b) cross-encoder validation + (c) compute gate integration. LIPAR (pruning), Pathwise TTC (correction), SFD (generation) are complementary layers — TrACE-Video = measurement layer.

2. **CNLSA treatment pathways ranked:**
   - SVG (ICLR 2026, DINOv2 replaces VAE) — STRONGEST confirmed
   - SemanticGen (semantic → VAE → pixels) — confirmed, code available
   - SFD (semantic-first diffusion) — CVPR 2026, confirmed
   - Send-VAE (semantic-disentangled VAE) — code ✅
   - Re2Pix (VFM semantic → pixels) — code ✅

3. **Nova Idea A (LCS compute gate) remains viable:** Consistency-Preserving (2602.15287) uses similar latent embedding + interpolation idea. Compute gate as semantic early-exit mechanism defensible.

4. **New finding:** DiTTA (Apr 2026) applies test-time adaptation to video — could inspire a TrACE-Video test-time intervention direction.
