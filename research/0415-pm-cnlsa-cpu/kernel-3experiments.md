# Kernel 0415-PM — 3 CPU Experiments Complete

## Exp 1 — DINOv2 Vulnerability: ❌ FAIL (threshold > 0.97)

| Metric | Value |
|---|---|
| Mean CS | 0.8155 ± 0.0938 |
| Cohen's d | 8.69 (vs zero baseline) |
| Threshold | >0.97 → FAIL |
| Range | 0.54 – 0.93 |

VAE roundtrip substantially degrades DINOv2-small (ViT-S/14) features. Prior ViT-B/14 result (CS=0.343) was even worse — smaller model is more robust but still far below threshold.

**CLIP-specificity hypothesis: FALSIFIED** — DINOv2 also fails.

---

## Exp 2 — Category-Level Drift ANOVA: ❌ FAIL (threshold p < 0.05)

| Metric | Value |
|---|---|
| Welch F(5, ~55M) | 0.726 |
| p-value | 0.6037 → FAIL |
| Games-Howell | 0 pairs significant |

VAE drift is **category-uniform** at σ=0. Vehicle highest (0.078), background lowest (0.042) — but high within-group variance washes out all differences. The VAE distortion is spatially uniform, not content-selective.

**Category concentration hypothesis: FALSIFIED** — no semantic selectivity.

---

## Exp 3 — Literature Synthesis: "confirms and extends"

- **REED-VAE (CGF 2025):** Iterative VAE cycles → high-freq loss, artifact accumulation, images "essentially destroyed" after 5–10 iterations. [arXiv 2504.18989]
- **PS-VAE (arXiv 2512.17909):** Off-manifold latents → unreliable decoding, structural/texture artifacts exceeding reconstruction metric predictions.

Both confirm VAE causes distributional/semantic shift across modalities. CNLSA is **first to demonstrate in CLIP semantic space** — defensible "first" claim, conservative alternative is "confirms and extends."

---

## Synthesis

Three experiments, two falsifications, one confirmation:
1. **CLIP is not uniquely vulnerable** — DINOv2 also fails (CS=0.82), prior Random baseline passes
2. **Drift is uniform** — no category concentration (ANOVA p=0.60)
3. **Prior art exists** — REED-VAE + PS-VAE document VAE distributional shift in other spaces; CNLSA extends to CLIP

**CNLSA framing stands:** *VAE-induced cross-modal semantic drift*, with CLIP as a documented case of a broader phenomenon. "First in CLIP semantic space" is defensible.

---

## Artifacts
- `exp1_dinov2_results.json`
- `exp2_anova_results.md`
- `exp3_literature_synthesis.md`
