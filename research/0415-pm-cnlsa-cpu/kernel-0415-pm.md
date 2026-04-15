# Kernel 0415-PM — DINOv2 Control Results + Design Update

## Key Finding: CLIP-Specificity Hypothesis FALSIFIED

**DINOv2 Control Experiment (already run, prior session):**

| Model | CS (σ=0) | Cohen's d | Verdict |
|-------|-----------|-----------|---------|
| DINOv2 ViT-B/14 | **0.343** | -3.296 | Catastrophic drift |
| CLIP ViT-B/32 | **0.615** | -7.046 | Even more damaged |

**Failure condition for modality-specificity claim:** NOT survived.
- DINOv2 is NOT robust to VAE encode-decode (CS = 0.343 ≪ 0.94)
- CLIP is MORE damaged than DINOv2 (d=-7.046 vs d=-3.296)

**Scientific interpretation:** VAE damage is modality-general (universal to vision encoders). CLIP's text-conditioning **amplifies** the damage without **causing** it.

## CNLSA Path Forward

- **Option A (diffusion generation)** is now the ONLY viable path
- Options B/C are moot without GPU validation
- GPU is the remaining blocker

## CORRECTED_CNLSA_EXPERIMENT_DESIGN.md updated
Added section "DINOv2 as Control Encoder (CPU Experiment — COMPLETED)" documenting:
- Pre-specified failure condition: CS ≥ 0.94 at σ=0 → CLIP-specific hypothesis survives
- Actual result: CS = 0.343, failure condition tripped in the opposite direction
- Scientific implications

## Artifacts
- `dinov2_control_exp.py`
- `dinov2_control_results.json`
- `dinov2_control_results.md`
