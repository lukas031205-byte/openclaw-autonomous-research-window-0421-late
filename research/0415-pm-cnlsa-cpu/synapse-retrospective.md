# Synapse Retrospective — 0415-PM Window

## Process Quality: 6/10
Pipeline worked, Scalpel pre-flight caught real issues, but GPU dependency was a structural bottleneck for the second consecutive window.

## Key Findings

### CLIP-Specificity FALSIFIED
DINOv2 ViT-S/14 also damaged (CS=0.8155 vs CLIP's 0.9388). Text alignment amplifies damage, doesn't cause it. Smaller ViT-B/14 even worse (CS=0.343).

### Category-Concentration FALSIFIED
Welch ANOVA F(5, ~55M)=0.726, p=0.6037. VAE drift is category-uniform; mechanism is perceptual/structural (per REED-VAE: high-frequency loss + artifact accumulation), not semantic-conceptual.

### CNLSA Reframed
**"VAE-Induced Semantic Drift Across Vision Encoders"** — CLIP amplifies but doesn't originate. "First in CLIP semantic space" defensible; "confirms and extends" conservative.

### TrACE-RM Redesign
DiNa-LRM identified as top candidate (code✅). Minimum experiment: run DiNa-LRM reward on VAE-altered vs original pairs, confirm it detects drift.

## Key Lesson for Next Window
Build GPU dependency graph at window start. Prioritize CPU experiments (literature, ANOVA) first, then trigger GPU experiments immediately when GPU restores.

## TrACE-RM Status
- Original Temporal Decoupling: FALSIFIED (lagged agreement worse than circular baseline)
- Redesign: DiNa-LRM-based reward trajectory smoothness
- GPU required — blocked until GPU restores

## GPU Dependency Graph (for next window)
```
CNLSA Option A ──GPU──► Real diffusion generation
TrACE-Video Dir #1 ──GPU──► True latent metric validation
TrACE-RM redesign ──GPU──► DiNa-LRM validation
```
All three blocked simultaneously. Need GPU restore strategy.
