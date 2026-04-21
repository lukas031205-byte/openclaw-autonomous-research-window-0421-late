# Nova: LCS Compute Gate CPU Experiment Design

**Role:** Nova (idea generation + framing)
**Date:** 2026-04-21 11:18 CST
**Context:** GPU unavailable 4 days, CPU-only path, Workshop paper v4 complete
**Priority:** 0.92 (Nova-Idea-A)

---

## The Core Problem

The LCS Compute Gate idea has a **confound architecture** problem:

```
Past experiments:
  - 0416-PM: CLIP L2 distance vs semantic inconsistency → r=0.9895 (SAME MODEL CONFUND)
  - CNLSA-Bridge: DINOv2 L2 vs CLIP drift → r=0.3681 (weak but cross-encoder)
  - Kernel's lcs_toy.py: pixel noise, DINOv2 L2 vs CLIP CS → SAME PIXEL NOISE CONFUND
```

The problem: **All past experiments use pixel-space noise**, but LCS Compute Gate is about *latent space* perturbation (VAE encode-decode or diffusion denoising). 

**We need a design that:**
1. Uses VAE latent perturbation (not pixel noise) — the actual use case
2. Employs cross-encoder measurement (DINOv2 as probe, CLIP as ground truth)
3. Runs entirely on CPU
4. Is small enough to complete in one session

---

## Hypothesis

**H₀ (Null):** DINOv2 L2 distance does NOT predict CLIP semantic inconsistency when both are measured on VAE latent-perturbed images. If r < 0.3, the LCS Compute Gate idea is falsified.

**H₁ (Alternative):** DINOv2 L2 distance (measured on VAE decode outputs) correlates with CLIP semantic inconsistency (Pearson r ≥ 0.4). If r ≥ 0.4, the LCS Compute Gate has a viable semantic probe.

**Why r ≥ 0.4 (not 0.3)?** Because r=0.3681 from CNLSA-Bridge was already weak, and that's with a different encoder (DINOv2-S vs CLIP ViT-B). If we can only match CNLSA-Bridge on VAE-latent-perturbed images, that's the baseline we need to exceed to justify compute gate.

---

## Minimal Experiment: VAE Latent Perturbation on CIFAR-10

### Design

```
Dataset:     60 CIFAR-10 test images (12 per class × 5 classes), resized to 224×224
VAE:         stabilityai/sd-vae-ft-mse (same as CNLSA experiment)
Encoders:    DINOv2 ViT-S/14 (probe) + CLIP ViT-B/32 (ground truth)
Perturbation: σ ∈ {0, 0.05, 0.1, 0.2, 0.4} injected into VAE latent space
Metric:      Pearson r( DINOv2_L2, CLIP_CS ) across all σ × image points
```

### Pipeline

For each of 60 images and each σ level:

1. `z = VAE.encode(x_orig)` — get 4×64×64 latent
2. `z_perturbed = z + N(0, σ²)` — inject noise into latent
3. `x_rec = VAE.decode(z_perturbed)` — reconstruct
4. `d_dino = ||f_DINO(x_orig) - f_DINO(x_rec)||₂` — L2 distance
5. `cs_clip = cosine(f_CLIP(x_orig), f_CLIP(x_rec))` — cosine similarity

Aggregate: 60 images × 5 σ levels = 300 data points

### Threshold & Failure

| Metric | Threshold | Interpretation |
|--------|-----------|----------------|
| Pearson r(DINO L2, CLIP CS) | < 0.3 | FALSIFIED — abandon LCS compute gate |
| Pearson r | 0.3–0.4 | Weak — CNLSA-Bridge baseline, not enough for gate |
| Pearson r | ≥ 0.4 | PROMISING — justifies compute gate design |
| Per-σ stability | r < 0.2 at ≥ 3/5 levels | Unstable — correlation is noise |

**Expected result if H₁ true:** Global r ≥ 0.4, with r > 0.3 at most individual σ levels.

**Failure condition:** Global r < 0.3 OR r < 0.2 at 4+ σ levels.

---

## Confound Mitigation: Why This Is Different from Past Experiments

The key distinction from prior experiments:

| Experiment | Noise Type | Encoder A (Probe) | Encoder B (Ground Truth) | Confound? |
|------------|-----------|-------------------|--------------------------|-----------|
| 0416-PM | Pixel noise | CLIP L2 | CLIP cosine | SAME MODEL ✗ |
| CNLSA-Bridge | VAE latent | DINOv2-S L2 | CLIP cosine | Cross-encoder ✓ |
| Kernel lcs_toy.py | Pixel noise | DINOv2 L2 | CLIP cosine | Pixel confound ✗ |
| **This design** | **VAE latent** | **DINOv2 L2** | **CLIP cosine** | **Cross + domain ✓** |

This is the **only experiment that combines**:
- VAE latent perturbation (the actual use case, not pixel noise)
- Cross-encoder measurement (no same-model confound)
- CIFAR-10 images (manageable on CPU)

---

## Resource Estimate

- **Time:** ~15-20 min CPU (60 images × 5 σ × DINOv2 + CLIP forward)
- **RAM:** < 1.5GB peak (DINOv2-S 21M + CLIP ViT-B 86M, processed one at a time)
- **GPU:** None required
- **Storage:** ~50MB for cached features

---

## Risk Assessment

### If FALSIFIED (r < 0.3):
- LCS Compute Gate direction is **abandoned** for the workshop paper
- Nova-Idea-A gets marked `falsified` in memory
- The CNLSA result (r=0.3681) becomes the ceiling — cannot improve with VAE latent perturbation
- Shift focus to: (1) Send-VAE/TTC for CNLSA treatment, (2) Re2Pix code follow-up

### If PROMISING (r ≥ 0.4):
- LCS Compute Gate has empirical foundation on VAE latent perturbation
- Short paper (Nova-Idea-A) has a **CPU-feasible validation** — highest priority
- Next step: run lcs_toy.py (Kernel's implementation) on this exact design to get numbers
- If robust, coordinate with Kernel to build actual compute gate scheduler

### If Weak (r ∈ [0.3, 0.4]):
- Not strong enough to justify compute gate alone
- Combine with CNLSA-Bridge (r=0.3681) as **corroborating evidence** for a combined claim
- Position: "L2 distance as lightweight semantic consistency proxy (weak but significant)"
- Consider: Is there a nonlinear transformation (e.g., exp(-L2), quantile mapping) that improves correlation?

---

## Implementation Note

This design is what Kernel's `lcs_toy.py` **should have measured** — but Kernel used pixel noise (Gaussian noise on pixels), not VAE latent noise. The toy experiment in lcs_toy.py is confounded by using pixel noise as a proxy for "frame drift", which is actually a VAE-latent phenomenon.

The fix: Run the same script but replace `add_gaussian_noise(images, sigma)` with:
1. VAE encode → latent
2. latent + N(0,σ) → perturbed latent
3. VAE decode → reconstructed image

This gives us VAE-latent perturbation on real CIFAR-10 images, CPU-feasible, cross-encoder measurement.

---

## References

- CNLSA-Bridge (0418-LATE): r=0.3681 on VAE latent perturbation with DINOv2-S + CLIP
- VAE: stabilityai/sd-vae-ft-mse (same as CNLSA experiment)
- DINOv2: facebook/dinov2-small (ViT-S/14, 384-dim)
- CLIP: openai/clip-vit-base-patch32 (ViT-B/32)