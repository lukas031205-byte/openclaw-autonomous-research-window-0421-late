# Exp 2: Category-Level Drift ANOVA Results

**Pre-registered threshold:** ANOVA p < 0.05 → category concentration confirmed

**Result:** ❌ FAIL (Welch's ANOVA p = 0.603734)

## Group Summary (CLIP Drift = 1 − CS)

| Supercategory | n | Mean Drift | Std | Min | Max |
|---|---|---|---|---|---|
| animal | 8 | 0.0665 | 0.0413 | 0.0218 | 0.1335 |
| background | 3 | 0.0423 | 0.0241 | 0.0089 | 0.0647 |
| food | 6 | 0.0525 | 0.0554 | 0.0058 | 0.1739 |
| indoor | 16 | 0.0573 | 0.0219 | 0.0238 | 0.1082 |
| person | 8 | 0.0634 | 0.0211 | 0.0351 | 0.0978 |
| vehicle | 9 | 0.0778 | 0.0302 | 0.0449 | 0.1349 |

**Background (unannotated):** n = 3

## Welch's ANOVA

- **F(5, 55198175.74)** = **0.7261**
- **p-value** = **0.603734**
- **Decision:** Fail to reject H₀ — no significant category drift difference

## Games-Howell Post-hoc

| Pair | n₁ | n₂ | Mean₁ | Mean₂ | Δ | q | p-value | Sig |
|---|---|---|---|---|---|---|---|---|
| animal vs background | 8 | 3 | 0.0665 | 0.0423 | 0.0242 | 1.045 | 0.3388 |  |
| animal vs food | 8 | 6 | 0.0665 | 0.0525 | 0.0140 | 0.478 | 0.6447 |  |
| animal vs indoor | 8 | 16 | 0.0665 | 0.0573 | 0.0092 | 0.556 | 0.5919 |  |
| animal vs person | 8 | 8 | 0.0665 | 0.0634 | 0.0031 | 0.176 | 0.8638 |  |
| animal vs vehicle | 8 | 9 | 0.0665 | 0.0778 | -0.0113 | 0.594 | 0.5628 |  |
| background vs food | 3 | 6 | 0.0423 | 0.0525 | -0.0102 | 0.338 | 0.7451 |  |
| background vs indoor | 3 | 16 | 0.0423 | 0.0573 | -0.0149 | 0.831 | 0.4788 |  |
| background vs person | 3 | 8 | 0.0423 | 0.0634 | -0.0211 | 1.120 | 0.3460 |  |
| background vs vehicle | 3 | 9 | 0.0423 | 0.0778 | -0.0354 | 1.760 | 0.1583 |  |
| food vs indoor | 6 | 16 | 0.0525 | 0.0573 | -0.0048 | 0.187 | 0.8584 |  |
| food vs person | 6 | 8 | 0.0525 | 0.0634 | -0.0109 | 0.419 | 0.6898 |  |
| food vs vehicle | 6 | 9 | 0.0525 | 0.0778 | -0.0252 | 0.935 | 0.3814 |  |
| indoor vs person | 16 | 8 | 0.0573 | 0.0634 | -0.0062 | 0.630 | 0.5391 |  |
| indoor vs vehicle | 16 | 9 | 0.0573 | 0.0778 | -0.0205 | 1.695 | 0.1146 |  |
| person vs vehicle | 8 | 9 | 0.0634 | 0.0778 | -0.0143 | 1.075 | 0.3002 |  |

*Sig: † = p < 0.05*

## Notes

- CLIP drift = 1.0 − cosine_similarity(CLIP(original), CLIP(VAE_roundtrip))
- σ=0 baseline (VAE encode-decode with no noise)
- Welch's ANOVA does not assume equal variances
- Games-Howell uses Welch-Satterthwaite df approximation
