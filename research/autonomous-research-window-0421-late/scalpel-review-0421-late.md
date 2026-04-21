# Scalpel Review — 0421-LATE

## LCS Compute Gate Falsification

**Experiment:** CIFAR-10 pixel noise, DINOv2 ViT-S/14 vs CLIP ViT-B/32
**Results:**
- σ=0.1: r=-0.0718 (p=0.706) — NO correlation
- σ=0.2: r=-0.0855 (p=0.653) — NO correlation
- σ=0.4: r=-0.2989 (p=0.109) — marginal negative, not significant
- **OVERALL: r=-0.5210 (p=1.41e-07)** — driven by between-group effect

**Verdict:** LCS Compute Gate FALSIFIED at per-frame prediction level.
- Within-noise-level correlation: essentially zero
- Between-group (higher σ → higher L2 AND lower CLIP CS): yes, but this is trivial
- The per-frame predictive power of DINOv2 L2 for CLIP semantic collapse: **ABSENT**

**Implications for TrACE-Video research program:**
1. The LCS metric (DINOv2 L2) cannot serve as a per-frame "semantic early exit" signal for diffusion compute allocation
2. This aligns with the 0420-PM Frame-Level Drift FALSIFICATION: DINOv2 L2 cannot predict which images within a fixed noise level will drift more
3. The "LCS as semantic stability metric" framing survives (diagnostic tool), but "LCS as compute gate" does NOT

**What this means for Nova Idea A:**
- The CPU toy on synthetic CIFAR-10 noise is NOT the right experiment
- The right experiment is VAE latent perturbation (which 0418-LATE ran: r=0.3681)
- Nova Idea A priority 0.92 should be REVISED to "LCS metric validation on VAE perturbation data" not "pixel noise proxy"

## Scout Findings: Strategic Assessment

**Top picks and Scalpel verdicts:**
1. **Re2Pix** (2604.11707, Apr 13) ⭐⭐⭐⭐ — VFM semantic→pixels two-stage, code✅ — DIRECT CNLSA treatment, most concrete follow-up
2. **Video-T1** (2503.18942) ⭐⭐⭐⭐ — test-time scaling + ToF search for TTC — complementary to compute gate (but compute gate falsified)
3. **SVG** (2510.15301, ICLR 2026) ⭐⭐⭐⭐⭐ — DINOv2 replaces VAE — STRONGEST treatment confirmation
4. **"There is No VAE"** (ICLR 2026) ⭐⭐⭐⭐ — VAE-free confirmed at top venue
5. **DiTTA** (2604.10950, Apr 2026) ⭐⭐⭐ — test-time adaptation for video segmentation — could inspire test-time intervention but not direct TrACE-Video metric

**Re2Pix follow-up assessment:**
- Most actionable: code confirmed, semantic→pixel two-stage
- When GPU restores: run TrACE-Video metric on Re2Pix outputs
- TrACE-Video could serve as quality metric for Re2Pix's semantic planning stage
- Synergy: Re2Pix generates with semantic guidance, TrACE-Video measures if semantic stability predicts output quality

## Workshop Paper v4 Assessment

Workshop paper v4 is complete (7/10 accept per Scalpel). Next question: what next?
- Workshop submission deadline: need to check if ICLR workshop deadline has passed
- If accepted: expand to full paper with GPU validation
- If not submitted: keep as reference implementation

## Recommended Research Directions (Revised)

### Priority 1: Re2Pix + TrACE-Video Metric Validation (GPU-pending)
Design: When GPU restores → run Re2Pix inference, measure DINOv2 L2 on Re2Pix features vs output pixel quality (SSIM/LPIPS)
- Hypothesis: Re2Pix semantic feature stability → pixel quality correlation
- Failure condition: no correlation → TrACE-Video降级为 methodology paper only

### Priority 2: LCS Metric Validation on Real VAE Data (CPU-feasible)
Design: Use 0418-LATE synthetic frame data (n=250) + actual VAE encode-decode
- Previous: CNLSA-Bridge r=0.3681 (weak but significant)
- Next: measure per-frame DINOv2 L2 on VAE latents vs CLIP CS
- Different from pixel noise: this directly tests VAE-induced drift mechanism

### Priority 3: Video Interpolation Semantic Anchor (CPU-feasible, new from Nova)
Design: Bilinear interpolation between video frames → measure if DINOv2 L2 predicts CLIP discrepancy
- This is different from pixel noise: tests interpolation quality prediction
- CPU-feasible: just needs pre-trained models

## Risk Summary
- GPU unavailable: blocks Priority 1 and CNLSA SD-VAE rerun
- LCS compute gate falsified: major direction pivot needed
- Workshop paper v4: ready, need ICLR workshop deadline confirmation
- InStreet learning: platform down (DNS failure confirmed, not code issue)
