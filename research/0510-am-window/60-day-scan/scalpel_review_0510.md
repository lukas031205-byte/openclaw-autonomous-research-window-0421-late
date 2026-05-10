## Scalpel Review — 2026-05-10

### Papers Assessed

**2603.17825 (STAS): OVERHYPED — 9/10 score not fully justified**
- The "training-free" claim holds up structurally (no fine-tuning, post-hoc magnitude steering), but the novelty vs LLM activation steering is underexamined. SubstrA/activation engineering in LLMs predates this work; the report never addresses whether "massive activation steering in video DiTs" is genuinely novel or just domain transfer.
- The 9/10 score reflects relevance to the research gap but conflates "directly relevant topic" with "well-supported claim." The core mechanism (first-frame tokens as temporal anchors, boundary tokens mediating transitions) is described from the Scout report abstract only — no independent verification of magnitude-scaling claim or steering effectiveness.
- GitHub confirmed by Kernel (Xianhang/STAS), project page confirmed. That's good evidence for reproducibility, but doesn't validate the scientific claim.
- **Missing caveat:** No comparison to attention-based editing methods (AttentionBender, 2604.20936, also in scan at 6/10 — suspiciously low given it directly manipulates cross-attention in Video DiTs).

**2604.22586 (FlowAnchor): UNCERTAIN — 8/10 score conflates distinct concepts**
- "Training-free anchor-guided video editing" — training-free is plausible (no fine-tuning mentioned).
- But the anchor-steering concept here is about stabilizing flow-based editing signal, not about latent concept sanitization. The Scout report stretches "anchor-guided" into direct alignment with LCS/TrACE-Video research gap, which is a conceptual leap.
- Anchor-guided in video editing ≠ anchor-guided in latent space. FlowAnchor operates on pixel/flow level; LCS would operate on latent representation level. These are different abstraction layers.
- GitHub confirmed (CUC-MIPG/FlowAnchor). Project page confirmed. But relevance to the specific research gap (VAE drift, latent concept displacement) is weak — this is a video editing paper, not a latent space analysis paper.
- **Verdict:** Worth monitoring but should not be used as primary evidence for anchor-guided latent space steering.

**2605.03849 (Stream-R1): SOLID — 8/10 justified**
- Prior Scalpel review already validated Intra-Perplexity + Inter-Reliability framing as directly relevant to TrACE-Video. This scan confirms it appeared in the 60-day window.
- GitHub confirmed (FrameX-AI/Stream-R1). Code availability is strong positive evidence.
- The "training-free" framing does not apply here (it's a reward distillation paper with training), so no false claim issue.
- **Caveat:** The paper is about reward distillation for streaming video generation, not about latent space analysis. Relevance is via concept terminology (Intra-Perplexity), not method directness.

**2605.06388 (semantic-wm): UNCERTAIN — 8/10 inflated by proximity, not directness**
- Conceptually relevant: semantic vs reconstruction encoders for world models directly addresses the LCS/VAE-drift question. This is the strongest conceptual contribution of the 4 papers.
- However: no GitHub found (Kernel verified: code_url=null), project page exists (hskalin.github.io/semantic-wm/), HuggingFace checkpoints available. Without code, validation is limited.
- The 8/10 score reflects the conceptual relevance but does not account for code unavailability. A paper without code, for a research gap that involves implementation (LCS), scores lower on practical utility.
- **Missing caveat in Scout report:** Does not flag code unavailability as a scoring factor. The report says "appears to have code per arXiv metadata but link not found" — this should reduce the score, not just be a footnote.

### Cross-Cutting Issues

**Issue 1 — "NOT found" conclusion is presented as definitive but is terminology-limited:**
The scan covered 2,648 papers in a 60-day window across 4 categories. "LCS" as an exact acronym or "Latent Concept Sanitizer" as a phrase may not appear in papers that implement the concept under different names (e.g., "concept bottleneck," "latent purification," "semantic stabilization," "representation sanitization"). The conclusion "no match found" is only as strong as the search vocabulary. No evidence that Scout used synonym expansion or alternative term search. Confidence: medium-low.

**Issue 2 — Relevance scores conflate topic proximity with methodological directness:**
A paper that addresses a related *concept* (semantic-wm) is scored the same as a paper that provides a *directly applicable method* (STAS). These serve different roles in research — conceptual framing vs. implementation building block. Scoring them on the same axis masks this difference.

**Issue 3 — "Training-free" claim used loosely across structurally different methods:**
STAS: training-free via post-hoc magnitude steering on frozen model. FlowAnchor: training-free via attention refinement + magnitude modulation on frozen model. These are similar in spirit but not identical mechanisms. The Scout report treats "training-free" as a single boolean tag without distinguishing the specific mechanism or its limitations. A method that requires analyzing activation patterns to determine steering direction is less "free" than one that uses a reference image directly.

**Issue 4 — AttentionBender (2604.20936) scored 6/10 despite directly manipulating cross-attention in Video DiTs:**
This seems systematically low. If the research gap involves understanding and controlling internal representations in video DiTs, a paper specifically about cross-attention manipulation should score higher. The 6/10 score may reflect that Scout was optimizing for "activation steering" and "latent concepts" specifically, but AttentionBender provides a relevant mechanism that should be noted even if the framing differs.

**Issue 5 — Time range inconsistency in Scout report:**
The report header says "Date range: March 11 - April 30, 2026" but the task was "March 11 - May 10, 2026." May 1-10 is handled separately ("Previously checked" and "May 9-10: 0 new submissions"). This is documented but creates confusion about actual coverage. The 60-day window appears to have been split into two sub-scans with different reporting.

### Verdict Summary

The Scout report identifies 4 relevant papers but the relevance scores need downgrading before using them as research gap evidence. STAS (9/10) is the most directly relevant but its novelty claim vs LLM activation steering is unexamined and should be caveated; FlowAnchor (8/10) is anchor-steering in pixel space, not latent space, and should not be used as LCS evidence; Stream-R1 (8/10) is solid for Intra-Perplexity terminology; semantic-wm (8/10) is the strongest conceptual contribution but lacks code. The "NOT found" conclusion for LCS/VAE-drift/TrACE-Video is only as reliable as the search vocabulary used — synonym expansion was not documented. **Needs revision before GitHub publication**: Scout should either (a) add novelty comparison for STAS against LLM activation steering literature, (b) clarify the distinction between pixel-level and latent-level anchor steering for FlowAnchor, and (c) document the search vocabulary used for the "NOT found" claim to support its reliability.