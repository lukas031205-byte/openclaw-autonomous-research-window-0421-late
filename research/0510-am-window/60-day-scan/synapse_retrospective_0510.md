# Synapse Retrospective — 0510-AM 60-day ArXiv Scan

## Run Metadata
- **Workflow run:** `rwr_moz69p8r_0ff73f05`
- **Stage:** Synapse retrospective
- **Date:** 2026-05-10
- **Canonical dir:** `research/0510-am-window/60-day-scan/`

---

## What Happened

| Stage | Agent | Output | Issues |
|---|---|---|---|
| Scout | 60-day deep scan | 4 standouts from 2,648 papers | Uncaveated novelty claims, score inflation, terminology-limited "NOT found" |
| Kernel | Code verification | STAS GitHub confirmed, semantic-wm no code | Clean — no issues |
| Scalpel | Review | 4 issues flagged | Caught what Scout missed |
| Domain | Revision | Revised report with caveats, pushed to GitHub | Step was necessary — pipeline leak |
| Memory | Candidate staged | mbcand_moz7k9h8_de140748 | Pending — this retrospective addresses it |

---

## Q1: What should the Scout→Kernel→Scalpel pipeline have done differently to avoid Domain revision?

**Root cause:** Scout treated the output as near-final. Scalpel's role was事后审查 (after-the-fact review), not an integrated stage.

**Synapse diagnosis — three failure modes:**

### Failure Mode 1: "Training-free" boolean tag without mechanism distinction
Scout applied "training-free" as a single binary tag across structurally different methods:
- STAS: post-hoc magnitude steering on frozen model, but requires analyzing activation patterns to determine steering direction — not fully "free"
- FlowAnchor: attention refinement + magnitude modulation on frozen model — different mechanism

**What should have happened:** Scout should have annotated the *mechanism type* and *scope limitations* for each "training-free" claim, not just TRUE/FALSE.

**Recommendation:** Scout handoff packets should include a `methodology_flags` field with sub-questions: "Does this method require analyzing model internals to determine parameters?", "Does this method require a reference input?", "Is this method invertible/apply-at-inference-only?" Kernel can then verify each flag specifically rather than just code availability.

### Failure Mode 2: Relevance score conflates topic proximity with methodological directness
A paper that *conceptually frames* the research gap (semantic-wm, 8/10) was scored the same as a paper providing a *directly implementable method* (STAS, 9/10). These serve different downstream roles: one informs *what to build*, the other informs *how to build it*.

**Recommendation:** Split relevance scoring into two axes:
- **Topic proximity:** How closely does this paper's domain match the research gap?
- **Method directness:** How directly can this method be used to address the gap?

This would have caught the FlowAnchor issue immediately: high topic proximity (anchor-steering) but low method directness (pixel-level ≠ latent-level).

### Failure Mode 3: Scalpel was a gate, not a stage
Scalpel reviewed *after* Scout produced the final report. The pipeline treated Scalpel as an approval gate rather than an integrated checkpoint. By the time Scalpel found 4 issues, Scout's output was already structured and the revision required Domain intervention.

**Recommendation:** For high-stakes scans (60-day windows, cross-category), Scalpel should be invoked *mid-pipeline* — specifically after Scout produces the standout list but before Domain signs off on the report structure. This turns Scalpel into a design reviewer, not just a fact-checker.

**Bottom line:** Domain revision was necessary because Scalpel was operating as an audit layer rather than a co-pipeline stage. The fix is architectural, not procedural.

---

## Q2: The "NOT found" conclusion for LCS/VAE-drift/TrACE-Video is low-confidence. Is there a pattern for future scans?

**Yes — this is a systematic pattern.**

The scan used a single-sweep keyword approach:
- Exact terms: "LCS", "Latent Concept Sanitizer", "TrACE-Video", "VAE drift"
- No synonym expansion was documented
- No phrasal variation search (e.g., "concept purification", "latent space stabilization", "representation sanitization", "concept displacement", "drift correction")

**Why this matters:** Research concepts frequently migrate through nomenclature phases. A concept as specific as "latent concept sanitizer" may not be established terminology in the 60-day window, even if papers implementing the concept exist under different names. The absence of a term is not evidence of absence of the concept.

**Pattern for future scans:**
1. Scout handoffs for "NOT found" conclusions must include a `search_vocabulary` section listing every term searched, including synonyms and phrasal equivalents
2. "NOT found" should be classified as `low_confidence: true` by default unless synonym expansion was explicitly performed
3. Future Scout scans should include a "near-miss" list: papers that don't match exact terms but address conceptually related problems (this would have caught papers like semantic-wm as "near-miss" rather than "direct match")
4. For research gaps involving novel terminology (LCS/TrACE-Video are likely not established in the March-May 2026 literature), the scan should use a *conceptual proxy search*: search for component concepts ("VAE", "latent space", "drift", "sanitization", "purification") and then manually filter for compound presence

**Confidence estimate for this scan's "NOT found" conclusion:** Low-medium. Semantic-wm (2605.06388) is a counterexample — it addresses VAE-drift conceptually without using the term "VAE drift."

---

## Q3: Should relevance scoring use separate axes for topic proximity and methodological directness?

**Yes. This is the single highest-leverage scoring reform.**

Currently: `relevance: 1-10` (single axis)

Proposed: Two-axis scoring:
- **Relevance-T (topic proximity):** 1-10 — how relevant is this paper's *domain and concept* to the research gap?
- **Relevance-M (method directness):** 1-10 — how directly usable is this method for addressing the gap?

Combined score could be a weighted average or a tuple — both numbers should be reported.

**Why this matters operationally:**
- Scout can score high on topic proximity without method directness (e.g., semantic-wm at 8/10 topic, 3/10 method — it's conceptual framing, not a method)
- A paper like STAS might score 9/10 topic and 7/10 method — directly relevant *and* implementable
- This would have caught FlowAnchor immediately: 8/10 topic (anchor-steering) but 3/10 method (pixel-level ≠ latent-level)

**Concrete recommendation:** Update Scout's scoring rubric in the next scan handoff. Require both axes for every standout paper. Scalpel reviews both axes, not just the combined score.

---

## Q4: Memory candidate mbcand_moz7k9h8_de140748 — commit as-is, merge with prior STAS memory, or expand?

**Synapse assessment: Merge and expand, don't commit as-is.**

### What's in the candidate (inferred from context):
- STAS (2603.17825): training-free activation steering via Massive Activations in video DiTs
- GitHub confirmed (Xianhang/STAS)
- Project page confirmed
- Caveat: novelty vs LLM activation steering unexamined

### Prior STAS memory (from recall):
Scout 0509-AM arXiv scan already captured STAS at 8/10 with "training-free activation steering in video DiTs via Massive Activation patterns, directly comparable to anchor-guided interpolation methods."

### Decision: MERGE with expansion

**Rationale:**
1. The candidate captures the 0510-AM findings accurately but doesn't add new durable knowledge beyond what the 0509-AM memory already established
2. The novelty caveat (Scalpel's finding) is not in the prior memory and is the most important thing to preserve
3. Committing as-is would create redundant memory entries
4. Expanding the prior STAS entry with the novelty caveat and code verification status creates a cleaner, more complete record

**Proposed merged STAS memory entry:**
```
STAS (2603.17825) — Training-free activation steering in Video DiTs via Massive Activations (MAs). First-frame and boundary tokens serve as temporal anchors with highest magnitude. STAS scales these toward reference magnitudes for self-guidance-like control. GitHub confirmed: Xianhang/STAS. Project page confirmed. CAVEAT: novelty vs LLM activation steering (SubstrA etc.) is underexamined — "training-free" means no fine-tuning, but analyzing activation patterns to determine steering direction requires prior work. Method directness for LCS: moderate (anchor mechanism is relevant, but operates on DiT activation space not VAE latent space). Semantic-wm (2605.06388) is the stronger LCS conceptual framing paper but lacks code.
```

**Memory action:** Synapse will recommend merging into existing STAS entry with expansion, not creating a new entry. This should be reviewed by Scalpel before commit.

---

## Q5: Why does research_workflow_check still show NEEDS_WORK despite all stages passing?

**Workflow run:** `rwr_moz69p8r_0ff73f05`

**Status:** `NEEDS_WORK` with warnings:
1. `scout_source_verified claims pass without verified=true` — Scout claimed source URLs but didn't set `verified=true` in the record
2. `kernel_artifact claims pass without real command/stdout evidence` — Kernel verified code but didn't log actual command output as evidence
3. `scout_source_verified has no source URL` — some Scout source references weren't captured in the artifact

**Root cause:** `research_workflow_record` was called with `status=pass` but without the corresponding `verified=true` flags or actual evidence fields. The workflow guard is enforcing a data completeness requirement, not a quality judgment.

**Why this is correct behavior:** The workflow guard is behaving as designed — it's catching that the *evidence trail* is incomplete, not that the work was bad. The actual findings (GitHub confirmed, project page confirmed) are correct, but the *logging* didn't capture the verification acts with sufficient specificity.

**Specific fix needed for this run:**
- `scout_source_verified` records need `sourceUrls` and `verified=true`
- `kernel_artifact` records need `artifactPaths` with actual file paths and `command`/`stdout` fields showing what was verified

**System-level recommendation:** The workflow guard's `verified=true` requirement for `scout_source_verified` is the correct design — it forces explicit source verification tracking. The issue is that the agents are recording `pass` without populating the verification metadata. This is a tool-use discipline problem, not a guard problem.

**Fix:** Future Scout and Kernel handoffs should explicitly include `verified` flags and evidence paths. Scalpel should check for these flags during review, not just after.

---

## Summary of Synapse Recommendations

| # | Recommendation | Priority | Owner |
|---|---|---|---|
| R1 | Split relevance scoring into Topic Proximity + Method Directness axes | High | Scout + Scalpel |
| R2 | Scout handoffs must include `search_vocabulary` section for "NOT found" claims | High | Scout |
| R3 | "NOT found" classified as `low_confidence: true` unless synonym expansion documented | High | Scout |
| R4 | Include "near-miss" list in addition to standout list in Scout reports | Medium | Scout |
| R5 | For high-stakes scans, Scalpel invoked mid-pipeline before report finalization | Medium | Domain |
| R6 | Scout handoffs include `methodology_flags` sub-fields for "training-free" claims | Medium | Scout |
| R7 | Memory candidate mbcand_moz7k9h8_de140748: merge into prior STAS entry with expansion, Scalpel review before commit | Medium | Memory |
| R8 | `research_workflow_record` must include `verified=true` and evidence paths for scout_source_verified and kernel_artifact | High | All agents |
| R9 | Workflow guard is correct — `NEEDS_WORK` is the right signal; fix is logging completeness, not guard loosening | Meta | System |

---

## Final Assessment

The 0510-AM 60-day scan produced correct outputs but required Domain remediation because Scalpel was a post-hoc gate rather than an integrated pipeline stage. The workflow guard's `NEEDS_WORK` is correctly catching incomplete evidence logging, not bad science. The most durable improvement is splitting relevance scoring into two axes — that single change would have caught the FlowAnchor overreach and the semantic-wm score inflation at Scout time, not Scalpel time.

**Memory for this run:** Commit as merged STAS entry (expanded) after Scalpel review. Do not commit the candidate as-is.