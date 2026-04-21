# Nova Ideation — 0421-LATE

## Active Context
- GPU unavailable (3+ days)
- Workshop paper v4 published (TrACE-Video)
- CNLSA: CPU confirmed r=0.3681, Factor Separability FALSIFIED
- Nova Idea A (LCS compute gate): priority 0.92, GPU needed for full validation
- Scout: Consistency-Preserving (2602.15287) closest prior work

---

## Idea B: LCS as Semantic Anchor for Video Interpolation

### Hypothesis
Frame-level DINOv2 L2 distance can serve as a semantic anchor signal to detect low-quality interpolation regions in video generation, enabling targeted re-sampling of uncertain frames.

### Minimal CPU Experiment
1. Use CIFAR-10 or a small image set (100-200 samples)
2. Generate interpolated frames between pairs using simple bilinear interpolation
3. Compute DINOv2 L2 distance between interpolated frame and both source frames
4. Compute CLIP cosine similarity between interpolated frame and source frames
5. Measure: correlation(L2_distance, CLIP_discrepancy) — does high L2 → high CLIP discrepancy?
6. Simulate "targeted re-sampling": when L2_distance > threshold, re-generate from closer source

### Failure Condition
If DINOv2 L2 distance does NOT predict CLIP semantic discrepancy (r < 0.3), the semantic anchor idea is falsified. The interpolation quality is not predictable from L2 distance alone.

### Priority
**0.78** — CPU-feasible, addresses TrACE-Video intervention direction, but limited by not using real video model

### Why not Idea A (LCS compute gate)?
LCS compute gate requires real diffusion model to measure "step reduction." Without GPU/real diffusion, we can't validate the compute-saving claim. Idea B uses interpolation as a proxy task where we CAN run experiments.

---

## Nova Idea A Revised: LCS Compute Gate (CPU-Only Version)

### Revised Framing
Instead of "compute gate during diffusion generation" (requires GPU), reframe as "LCS metric validates semantic stability metric for video generation"

### CPU Experiment
1. Use pre-existing video frames (e.g., from a video dataset, or generate simple synthetic sequences)
2. Add noise perturbations at different levels (σ=5,10,20,40,80)
3. For each frame, compute:
   - DINOv2 L2 distance (LCS proxy)
   - CLIP cosine similarity with clean frame (semantic consistency)
4. Measure: correlation(L2, CLIP_CS) at each noise level
5. Threshold sweep: at which threshold does high L2 reliably indicate low CLIP_CS?

### Failure Condition
If DINOv2 L2 does not predict CLIP semantic inconsistency at any threshold (all r < 0.3), the LCS metric is not a valid semantic stability predictor.

### Priority
**0.92** — original priority maintained, but now scoped to CPU-only metric validation

### Output
- Correlation table (L2 vs CLIP_CS) at different noise levels
- Best threshold for distinguishing stable/unstable frames
- ROC-style analysis: at threshold T, what % of low-CLIP frames are correctly flagged?

---

## Re2Pix Follow-Up

### Why Re2Pix?
Re2Pix (arXiv:2604.11707, Apr 13) is the most concrete CNLSA treatment with confirmed code:
- VFM semantic feature prediction → pixel generation
- Two-stage: semantic planning + visual generation
- Train only on GT features → stronger semantic consistency

### How TrACE-Video metric applies to Re2Pix
1. Run Re2Pix inference on a test video
2. Extract intermediate semantic features from Re2Pix's first stage
3. Measure frame-to-frame semantic feature consistency (DINOv2 L2 on features)
4. Compare to pixel-level metrics (SSIM, LPIPS) — does semantic feature consistency predict pixel quality?

### Expected Result
Semantic feature stability (TrACE-Video metric) should correlate with Re2Pix output quality, confirming that semantic stability → pixel quality is the underlying mechanism.

### Blocked By
Need to actually run Re2Pix code, which requires GPU for video generation. Not feasible in current window.

### Next Step
When GPU restores: clone Re2Pix, run TrACE-Video metric on outputs, validate semantic feature consistency → pixel quality correlation.

---

## Consolidated Recommendations

### This Window (CPU-only)
1. **Run Nova Idea A Revised (LCS metric CPU validation)** — DINOv2 L2 vs CLIP CS correlation on noise-perturbed images
2. **Write Re2Pix follow-up plan** — document what to do when GPU restores
3. **Check ICLR Workshop deadline** — workshop paper v4 submission

### Next Window (if GPU restores)
1. Run Re2Pix + TrACE-Video metric validation
2. Full LCS compute gate experiment on real diffusion model
3. SD-VAE CNLSA-Bridge rerun

### If GPU stays down
1. Write TrACE-Video as methodology paper (unsupervised LCS metric, not compute gate)
2. Submit to workshop with current results
3. Find alternative compute validation approach (maybe use pre-trained models)
