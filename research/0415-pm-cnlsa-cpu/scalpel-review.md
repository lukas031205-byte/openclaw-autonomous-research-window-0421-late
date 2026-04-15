# Scalpel Review — CNLSA CPU Experiments (0415-PM)

## Verdict Summary

| Exp | Verdict | Blocker |
|---|---|---|
| Exp 1 DINOv2 | ✅ RUN | No — calibrate noise σ to actual VAE reconstruction error (optional improvement) |
| Exp 2 Category ANOVA | ✅ RUN | No — use Welch's ANOVA + post-hoc pairwise (not standard ANOVA) |
| Exp 3 Literature | ✅ RUN | No — operationalize "structurally identical" before execution |
| Bonus TrACE-RM | ✅ `not_available` | Correct call — GPU required |

---

## Critical Issues (None Blockers)

### Exp 1: DINOv2
- **Architectural confound:** ViT-S/14 vs ViT-B/32 ≠ clean comparison (different architectures, different pretraining). Still provides directional evidence.
- **Fix:** Don't let perfect control be the enemy of good data. Run as-is.
- **Optional improvement:** Calibrate noise σ to actual VAE reconstruction error rather than arbitrary σ values.

### Exp 2: Category ANOVA
- **COCO person dominance:** ~50% of instances are "person" — must treat person as its own supercategory group or it swallows all between-group variance.
- **Post-hoc required:** F-test only tells you "some difference exists," not which categories. Need Games-Howell or Tukey HSD to identify WHERE drift concentrates.
- **Fix:** Welch's ANOVA (robust to unequal variances) + Games-Howell post-hoc.

### Exp 3: Literature Synthesis
- **"Structurally identical" needs definition before execution.**
- **Recommended criterion:** Any paper noting VAE causes semantic/distributional shift in downstream embeddings qualifies.

---

## Minimum Viable Versions

| Exp | MVP |
|---|---|
| Exp 1 | DINOv2-VAE CS alone (vs CLIP's 0.9388 baseline) |
| Exp 2 | 10 images × 6-8 supercategories, Welch's ANOVA |
| Exp 3 | 1 paper with explicit statement |

---

## Pre-registration Recommended

Lock thresholds before running:
- DINOv2 CS > 0.97 → CLIP-specificity survives
- ANOVA p < 0.05 → category concentration confirmed
- 3+ structurally identical papers → confirms vs extends framing

---

## Scalpel's Assessment

All three experiments are executable and informative at CPU scale. No fatal flaws. The DINOv2 confound is real but acceptable for directional evidence. The ANOVA person-dominance issue is fixable. TrACE-RM correctly marked not_available pending GPU.
