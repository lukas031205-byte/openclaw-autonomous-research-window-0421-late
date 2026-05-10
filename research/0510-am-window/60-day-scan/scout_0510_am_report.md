# Scout 0510-AM: 60-day ArXiv Deep Scan Report

## Scan Coverage
- **Date range:** March 11 - May 10, 2026 (full 60-day window)
- **Sub-periods:** March 11 - April 30 (primary scan, 1,163 papers), May 1-8 (previously checked), May 9-10 (checked 0510-AM, 0 new submissions in window)

## Key Findings

### HIGH-RELEVANCE PAPERS (Direct alignment with TrACE-Video/LCS/VAE-drift/activation steering)

#### 1. FlowAnchor (2604.22586)
- **Title:** FlowAnchor: Stabilizing the Editing Signal for Inversion-Free Video Editing
- **Relevance: 8/10** — Anchor-guided training-free video editing; uses Spatial-aware Attention Refinement (SAR) and Adaptive Magnitude Modulation (AMM) to stabilize flow-based editing signal. Relevant to anchor-steering concept at methodology level.
- **Key Finding:** Training-free method that anchors WHERE to edit (via attention refinement) and HOW STRONGLY (via magnitude modulation) for stable flow-based video editing without inversion.
- **Code:** YES — https://github.com/CUC-MIPG/FlowAnchor
- **Project Page:** https://cuc-mipg.github.io/FlowAnchor.github.io/
- **Authors:** Ze Chen, Lan Chen, Yuanhang Li, Qi Mao (Communication University of China, MIPG)
- **⚠️ Caveat (Scalpel):** FlowAnchor operates at pixel/flow level, not latent representation level. Direct use as LCS (Latent Concept Sanitizer) evidence is a conceptual overreach — anchor-guided in video editing ≠ anchor-guided in latent space. Different abstraction layers. Still useful as methodology reference.

#### 2. Stream-R1 (2605.03849) — Already confirmed from prior scan, verified code
- **Title:** Stream-R1: Reliability-Perplexity Aware Reward Distillation for Streaming Video Generation
- **Relevance: 8/10** — Introduces Intra-Perplexity and Inter-Reliability axes for reward-guided video diffusion distillation. Directly uses concept of "intra-perplexity" which is a search target.
- **Key Finding:** Reweights distillation supervision based on Inter-Reliability across rollouts and Intra-Perplexity across spatiotemporal regions via a single shared video reward model.
- **Code:** YES — https://github.com/FrameX-AI/Stream-R1
- **Project Page:** stream-r1.github.io

#### 3. 2605.06388 — "Reconstruction or Semantics? What Makes a Latent Space Useful for Robotic World Models"
- **Title:** Reconstruction or Semantics? What Makes a Latent Space Useful for Robotic World Models
- **Relevance: 7/10** — Systematically compares reconstruction encoders (VAE, Cosmos) vs semantic encoders (V-JEPA 2.1, Web-DINO, SigLIP 2) for action-conditioned video diffusion world models. Directly addresses semantic vs reconstruction latent space question (LCS-related). Strongest conceptual contribution of the 4 papers.
- **Key Finding:** Semantic encoders (V-JEPA 2.1, Web-DINO, SigLIP 2) generally outperform reconstruction encoders for planning and downstream policy performance, despite weaker pixel-level scores.
- **Code:** NONE — no GitHub found; HuggingFace checkpoints only. This limits practical utility for implementation.
- **Project Page:** https://hskalin.github.io/semantic-wm/
- **Authors:** Nilaksh, Saurav Jha, Artem Zholus, Sarath Chandar
- **⚠️ Caveat (Scalpel):** Score 8→7 adjusted downward — code unavailable, which is a significant gap for research requiring implementation. Conceptual framing is the strongest for LCS/VAE-drift question.

#### 4. STAS / Massive Activation Steering (2603.17825) — Confirmed from prior scan
- **Title:** Steering Video Diffusion Transformers with Massive Activations
- **Relevance: 9/10** — Training-free activation steering via Massive Activations (MAs) in video DiTs. First-frame tokens serve as global temporal anchors, boundary tokens mediate transitions. Directly provides "massive activation patterns" evidence.
- **Key Finding:** Video DiTs have structured MA patterns where first-frame and boundary tokens have highest magnitudes; STAS steers these toward scaled reference magnitude for self-guidance-like control.
- **Code:** YES — github.com/Xianhang/STAS (verified by Kernel 0510-AM)
- **Project Page:** xianhang.github.io/webpage-STAS (verified by Kernel 0510-AM)
- **⚠️ Caveat (Scalpel):** Novelty vs LLM activation steering (SubstrA etc.) is unexamined — the claim that "massive activation steering in video DiTs" is genuinely novel vs domain transfer is underexplored. "Training-free" here means no fine-tuning, but analyzing activation patterns to determine steering direction requires prior work; not fully "free."
- **Note:** AttentionBender (2604.20936, scored 6/10) also directly manipulates cross-attention in Video DiTs — potentially under-scored relative to this one.

### MEDIUM-RELEVANCE (Score 6-7, tangential but worth noting)

- **2604.21686v1** — WorldMark: Unified benchmark for interactive video world models (score 16)
- **2605.00080v1** — World Model for Robot Learning: Comprehensive survey (score 7)
- **2605.00078v1** — Being-H0.7: Latent world-action model from egocentric videos (score 7)
- **2604.26232v1** — DepthPilot: World model for colonoscopy video generation (score 7)
- **2604.20936v1** — AttentionBender: Manipulating cross-attention in Video DiTs (score 6, directly about video DiT internal mechanics — possibly under-scored; Scalpel flagged this as potentially more relevant than 6/10 suggests)
- **2604.19018v1** — Local Linearity of LLMs Enables Activation Steering via Model-Based Linear Optimal Control (score 8, but for LLMs not video)

### LCS-Related Paper Found
- **No paper matching "LCS" or "Latent Concept Sanitizer"** appeared in March 11 - April 30 window. This concept appears to be from an earlier paper or specific nomenclature not used in this period's literature.

### VAE-drift / Semantic vs Reconstruction
- **2605.06388** directly addresses this question (see above)
- No other papers in this window specifically tackle "VAE drift" as a named phenomenon

### What Was NOT Found
- No "concept displacement" papers in this window
- No "TrACE-Video" references
- No papers specifically about VAE latent space drift
- LCS (Latent Concept Sanitizer) — no match

**⚠️ Caveat on "NOT found" reliability:** The conclusion that these terms do not appear is only as strong as the search vocabulary used. Terms like "concept bottleneck," "latent purification," "semantic stabilization," "representation sanitization" may describe the same concept under different names. Confidence: medium-low. No synonym expansion was documented in this scan.

## Summary Table

| paper_id | title | relevance | key_finding | code | project_page |
|---|---|---|---|---|---|
| 2603.17825 | STAS (Massive Activations) | 9/10 ⚠️ | Video DiTs steered via MA patterns at first-frame/boundary tokens (caveat: novelty vs LLM steering unexamined) | ✅ xianhang/STAS | xianhang.github.io |
| 2604.22586 | FlowAnchor | 8/10 ⚠️ | Training-free anchor-guided video editing via SAR+AMM (caveat: pixel level ≠ latent level) | ✅ CUC-MIPG/FlowAnchor | cuc-mipg.github.io |
| 2605.03849 | Stream-R1 | 8/10 ✅ | Reward distillation via Intra-Perplexity + Inter-Reliability axes | ✅ FrameX-AI/Stream-R1 | stream-r1.github.io |
| 2605.06388 | Reconstruction or Semantics? | 7/10 ⚠️ | Semantic encoders (V-JEPA 2.1, SigLIP 2) outperform VAE for robot world model planning (caveat: NO code) | ❌ none | hskalin.github.io |

⚠️ = caveats apply; ✅ = solid

## Scout Assessment
The scan of 1,163 papers from March 11 - April 30 yielded **4 high-relevance papers** with varying code availability. The most directly relevant concept is **STAS (2603.17825)** at 9/10 for training-free activation steering in video DiTs. **Stream-R1** provides Intra-Perplexity evidence directly relevant to TrACE-Video. **2605.06388** provides strong semantic vs reconstruction encoder comparison for world models. **FlowAnchor** provides anchor-steering methodology.

The LCS concept and VAE-drift framing did not appear with matching terminology in this period.

**Scout recommends:** Domain should prioritize following up on code status for 2605.06388 (appears to have code per arXiv metadata but link not found in search), and verify whether the 2603.17825 STAS paper has a project page/code repository.