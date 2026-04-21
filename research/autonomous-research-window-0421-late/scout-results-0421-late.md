## Scout Results 0421-LATE

**Scout session:** 0421-LATE | **扫描范围:** 2026-03-01 至 2026-04-21 | **时间:** Tue 2026-04-21 11:13 CST

---

### Top Picks (with code)

1. [Long-Horizon Streaming Video Generation via Hybrid Attention with Decoupled Distillation (Hybrid Forcing)](https://arxiv.org/abs/2604.10103) — 2026 | VAE-aware streaming video generation, hybrid attention (linear temporal + block-sparse), 29.5 FPS on H100 | GitHub: [⭐ code released 2026.4.6](https://github.com/leeruibin/hybrid-forcing)
   - Key finding: Linear temporal attention maintains compact KV state for long-range dependencies beyond sliding window. Block-sparse attention reduces local redundancy. Decoupled distillation: dense-step initial + streaming fine-tune. Real-time 832×480 at 29.5 FPS.
   - Relevance to CNLSA/TrACE-Video: Streaming distillation directly addresses VAE latent error accumulation over time. The linear temporal attention KV-caching mechanism is conceptually similar to CNLSA's semantic consistency tracking — both maintain compressed state over time. VGGRPO (another paper this session) also uses latent geometry to avoid VAE decode overhead — this is a complementary approach.

2. [Diagonal Distillation for Streaming Autoregressive Video Generation](https://arxiv.org/abs/2603.09488) — ICLR 2026 | Streaming AR video, asymmetric step allocation (more steps early, fewer later), 277× speedup | Project page: [spherelab.ai/diagdistill/](https://spherelab.ai/diagdistill/) (code not yet on GitHub as of 2026-04-21)
   - Key finding: Addresses exposure bias in next-chunk prediction. Aligned implicit noise prediction with actual inference conditions. Implicit optical flow modeling preserves motion quality under step constraints. 5-second video in 2.61 seconds (31 FPS).
   - Relevance to CNLSA/TrACE-Video: The asymmetric denoising schedule (more steps early, fewer later) is relevant to CNLSA's finding that early frames accumulate more drift. If early steps are more important for semantic consistency, CNLSA's semantic gate could allocate compute accordingly.

3. [VGGRPO: Visual Geometry GRPO — World-Consistent Video Generation via Latent Geometry-Guided Post-Training](https://arxiv.org/abs/2603.26599) — 2026 | Latent geometry-guided RL, eliminates VAE decode overhead, 4D reconstruction | Project page: [zhaochongan.github.io/projects/VGGRPO](https://zhaochongan.github.io/projects/VGGRPO)
   - Key finding: Latent Geometry Model (LGM) stitches video diffusion latents to geometry foundation models — direct geometry decoding from latent space without VAE decode. GRPO with camera motion smoothness + geometry reprojection consistency rewards.
   - Relevance to CNLSA/TrACE-Video: **This is a direct validation of the latent-space-only paradigm.** VGGRPO shows that geometry consistency can be enforced entirely in latent space, bypassing VAE decode entirely. This is strong evidence that CNLSA's latent-space semantic consistency metric is the right approach — pixel-space metrics are unnecessary.

4. [LIPAR: Training-free Latent Inter-Frame Pruning with Attention Recovery](https://arxiv.org/abs/2603.05811) — 2026 | Training-free video latency pruning, 1.45× throughput boost, 12.2 FPS on A6000 | Code: not found (no GitHub mentioned in abstract)
   - Key finding: Detects and skips duplicated latent patches across video frames. Attention Recovery approximates attention of pruned tokens to remove artifacts. No training required, seamlessly integrated.
   - Relevance to CNLSA/TrACE-Video: Directly relevant to latent consistency — LIPAR exploits temporal redundancy in VAE latent space. The Attention Recovery mechanism is conceptually similar to CNLSA's semantic recovery mechanism. However, LIPAR targets efficiency, not semantic drift measurement.

5. [S³: Stratified Scaling Search for Test-Time in Diffusion Language Models](https://arxiv.org/abs/2604.06260) — 2026 (submitted to COLM 2026) | Test-time compute scaling, verifier-guided search over denoising trajectories, reference-free verifier | Code: not found
   - Key finding: Classical verifier-guided search over denoising trajectories. At each step, expands multiple candidates, evaluates with lightweight verifier, selectively resamples promising ones. Best gains on mathematical reasoning (not video).
   - Relevance to CNLSA/TrACE-Video: Methodologically very relevant — test-time compute reallocation based on verification signals. If a lightweight semantic verifier (DINOv2/CLIP) could guide compute allocation per-step in video diffusion, this would be a practical implementation of the CNLSA compute gate. Note: this is for DLM (Diffusion Language Model), not video — but the method is transferable.

---

### Code-verified repos

| Repo | Paper | Stars | Verified | Purpose |
|------|-------|-------|----------|---------|
| [leeruibin/hybrid-forcing](https://github.com/leeruibin/hybrid-forcing) | Hybrid Forcing (2604.10103) | released Apr 6, 2026 | 2026-04-21 | Long-horizon streaming video generation, hybrid attention distillation |
| [spherelab.ai/diagdistill](https://spherelab.ai/diagdistill/) (project page, code pending) | Diagonal Distillation (2603.09488) | project page only, no GitHub yet | 2026-04-21 | Streaming AR video distillation |
| zhaochongan.github.io/projects/VGGRPO (project page, no GitHub) | VGGRPO (2603.26599) | project page only | 2026-04-21 | Latent geometry-guided video post-training |

---

### Papers without code (if relevant)

6. [TTC: Pathwise Test-Time Correction for Autoregressive Long Video Generation](https://arxiv.org/abs/2602.05871) — v2 March 2026 | Test-time correction, initial frame as anchor to calibrate stochastic states | No code found
   - Key finding: Uses first frame as stable reference anchor to calibrate intermediate stochastic states along sampling trajectory. Mitigates drift in extended sequences for distilled AR video models.
   - Relevance to CNLSA/TrACE-Video: Test-time correction approach directly relevant to semantic drift mitigation. The "anchor frame" idea is similar to CNLSA's semantic anchor concept, but TTC operates in pixel/VAE space, not semantic space.

7. [Event-Driven Video Generation (EVD)](https://arxiv.org/abs/2603.13402) — 2026 (v2 March 18) | Event-grounded video diffusion, reduces interaction hallucinations | No code found
   - Key finding: Lightweight event head predicts token-aligned event activity. Event-gated sampling with hysteresis. Reduces contact, support relation, and state persistence failures without sacrificing appearance.
   - Relevance to CNLSA/TrACE-Video: Event grounding is a form of semantic-level guidance that bypasses VAE pixel noise. EVD shows that semantic events can guide frame-level generation more robustly than pure pixel-space signals. The "event head" is analogous to a semantic consistency monitor.

8. [Consistency-Preserving Diverse Video Generation via Joint-Sampling](https://arxiv.org/abs/2602.15287) — Feb 2026 | Diversity + temporal consistency, joint-sampling for flow-matching video generators | Code: will be released
   - Key finding: Diversity-driven updates + removes components that decrease temporal consistency. Both objectives computed in latent space using lightweight models — avoids VAE decoding and decoder backpropagation.
   - Relevance to CNLSA/TrACE-Video: The approach of computing temporal consistency in latent space (avoiding decoder) is exactly CNLSA's core argument. This paper provides additional evidence that pixel-space consistency metrics are unnecessary overhead.

---

### Notes

- **GRN (HBQ near-lossless tokenization, Apr 17)** — Not found in March-April 2026 range search. The arXiv ID appears to be either not yet published or uses a different naming scheme. The "HBQ" name suggests hierarchical binary quantization — a potential VAE-free or near-lossless tokenization method. Recommend checking later arXiv submissions or asking Scout 0422-AM to follow up.
- **VGGRPO (2603.26599) is the most important new finding** — It directly validates the latent-only paradigm for video generation consistency, using a Latent Geometry Model to bypass VAE decode entirely. This is strong evidence for CNLSA's core claim.
- **Cross-encoder validation for semantic drift** — No paper explicitly uses DINOv2/CLIP to cross-validate VAE-induced semantic drift in the March-April 2026 window. This remains an open research gap.
- **Test-time adaptation for diffusion/video** — S³ (diffusion language) and TTC (video) both show verifier/anchor-guided approaches, but none use semantic-space (DINOv2/CLIP) as the verification signal. CNLSA's compute gate using DINO semantic consistency as the verifier is novel in this regard.
- **Semantic space generation** — Hybrid Forcing, VGGRPO, and Diagonal Distillation all operate partially in or near semantic/geometry space rather than pure pixel space. Combined with SVG (ICLR 2026, DINOv3-replaced VAE), this confirms the trend of moving generation from VAE latent space to semantic space.
