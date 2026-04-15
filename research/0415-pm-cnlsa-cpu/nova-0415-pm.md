# Nova — CPU-Feasible Experiments for CNLSA (0415-PM)

## Core Insight
The CLIP semantic drift is a **pure format conversion artifact**, not a semantic phenomenon. We need to know: (a) is it CLIP-specific?, (b) where does it concentrate?, (c) what does it connect to in literature? Three CPU experiments:

---

## Experiment 1: DINOv2 Vulnerability Test

**Hypothesis:** DINOv2 features are more robust to VAE roundtrip than CLIP features, because CLIP's text encoder introduces cross-modal interference that pure vision models lack.

**Falsifiable claim:** Mean DINOv2 cosine similarity after VAE roundtrip > 0.97 (vs CLIP's 0.9388).

**Design (CPU, no GPU compute):**
- Use `facebook/dinov2-small` (ViT-S/14, ~22M params, CPU-feasible)
- Same 50 COCO val2017 images used in original CNLSA measurement
- Extract DINOv2 patch tokens (or CLS token) for original and VAE-reconstructed images
- Compute per-image cosine similarity; report mean ± std
- Control: also compute pixel-space noise baseline (Gaussian σ=0.1, 0.2) on DINOv2 features

**Why this matters:** If DINOv2 is robust, the drift is CLIP-specific (text encoder + vision encoder interaction). If DINOv2 also drifts, the VAE is destroying semantic information generally — much stronger claim.

**Minimal code path:** Load DINOv2 via `torch`, no diffusion needed. Encode original image + VAE-decode-reconstruct → DINOv2 → cosine sim.

---

## Experiment 2: Category-Level Drift Concentration

**Hypothesis:** VAE semantic drift is not uniform — categories with more fine-grained distinctions (animals, food, vehicles) suffer more than broad categories (background, indoor).

**Falsifiable claim:** ANOVA across COCO categories shows significant between-group variance in CLIP drift magnitude (F-test p < 0.05).

**Design (CPU, requires COCO annotations):**
- Download `instances_val2017.json` from COCO API (small JSON, ~1MB)
- Filter 50 val2017 images with known categories
- Group images by supercategory: `animal`, `vehicle`, `food`, `indoor`, `background`
- For each group, compute CLIP drift = 1.0 − CS(VAE_roundtrip)
- Report group means, run one-way ANOVA

**Why this matters:** If drift concentrates in semantically rich categories, it's not a floor effect — it's meaningful semantic compression. If uniform, it's just a generic reconstruction quality proxy.

**Minimal code path:** `pycocotools` for annotations, CLIP already available from experiment code.

---

## Experiment 3: Literature Synthesis — Representation Stability Map

**Hypothesis:** The VAE→CLIP drift is a known phenomenon in disguise: it maps to (a) VAE representation collapse literature, (b) CLIP robustness to input corruption studies, and (c) latent space interpolation sensitivity.

**Falsifiable claim:** Within 3 papers, find explicit mention of VAE-induced CLIP degradation OR structurally identical findings in related representation learning work.

**Design (CPU, no compute):**
- Scout targets:
  1. "CLIP robustness input corruption" — find papers on CLIP + JPEG compression, blur, noise
  2. "VAE representation stability" — find papers on VAE latent space collapse/distortion
  3. "Semantic representation drift reconstruction" — find papers on encode-decode feature drift
- For each paper, extract: (a) methodology, (b) measured drift magnitude, (c) interpretation
- Synthesize: does any paper report degradation ≥5% from format conversion alone?

**Why this matters:** Strengthens CNLSA contribution framing — if it's novel, we say "first to demonstrate". If related work exists, we position as "confirms and extends". Either direction is publishable.

**Minimal path:** Web search + paper PDF extraction, no model inference needed.

---

## Bonus: TrACE-RM "Reward Trajectory Smoothness" Sketch (Synthesizer, Not Experiment)

**Design (Synthetic Data Only, CPU):**
- Generate N=500 synthetic reward trajectories: `r_t = r_{t-1} + ε` where `ε ~ N(0, σ²)`
- Smooth trajectories: low σ²; jagged trajectories: high σ²
- Final quality score Q = 1/(1 + σ²) + small noise
- Hypothesis: Q inversely correlates with σ² (smooth → better final quality)
- Test: Pearson r(σ², Q) < 0 with p < 0.05

**Status:** This is a hypothesis generation sketch. Real validation needs real diffusion trajectories. File as "pending GPU availability."

---

## Resource Estimate

| Experiment | CPU | Time | Dependencies |
|---|---|---|---|
| DINOv2 | Yes | ~10 min | `torch`, `dinov2` weights |
| Category breakdown | Yes | ~5 min | `pycocotools`, existing CLIP code |
| Literature synthesis | Yes | ~20 min | Web search + PDF |

All three can run in parallel. No GPU required for any.
