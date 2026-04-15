# Scout Literature Verification — CNLSA (0415-PM)

**Task:** Find ≥3 academic papers discussing VAE-induced semantic degradation in CLIP-like models, or structurally identical phenomena.

**Search targets:**
- Target A: CLIP robustness + input corruption (JPEG, blur, noise) ≥5% degradation
- Target B: VAE latent space collapse / encode-decode feature drift
- Target C: Semantic representation drift in vision-language models

---

## Papers Verified

```json
papers_verified = [
  {
    "title": "Enhancing Robustness of CLIP to Common Corruptions through Bimodal Test-Time Adaptation (BAT-CLIP)",
    "venue": "arXiv:2412.02837",
    "year": 2024,
    "target": "A",
    "drift_magnitude": "CLIP ResNet-101: 49% → 10.79% on CIFAR-100 with Gaussian noise severity 5 (78% relative drop). BAT-CLIP achieves +9.7%, +5.94%, +5.12% mean accuracy improvements on CIFAR-10C, CIFAR-100C, ImageNet-C respectively over base CLIP.",
    "structurally_identical": true,
    "code": true,
    "url": "https://arxiv.org/abs/2412.02837"
  },
  {
    "title": "Analysing the Robustness of Vision-Language-Models to Common Corruptions",
    "venue": "arXiv:2504.13690",
    "year": 2025,
    "target": "A",
    "drift_magnitude": "Scene text understanding (TextVQA-C) deteriorates most severely under defocus blur and snow; object reasoning (GQA-C) shows significant degradation under frost and impulse noise. VLM accuracy drops to near-random on severely corrupted inputs.",
    "structurally_identical": true,
    "code": false,
    "url": "https://arxiv.org/abs/2504.13690"
  },
  {
    "title": "REED-VAE: RE-Encode Decode Training for Iterative Image Editing with Diffusion Models",
    "venue": "Computer Graphics Forum (CGF 2025)",
    "year": 2025,
    "target": "B",
    "drift_magnitude": "Vanilla VAE exhibits significant loss of high-frequency information after several encode-decode cycles, accumulating high-frequency noise and artifacts. After ~5 encode/decode iterations, images are 'essentially destroyed'. REED training scheme proposed to mitigate this.",
    "structurally_identical": true,
    "code": true,
    "url": "https://arxiv.org/abs/2504.18989"
  },
  {
    "title": "Both Semantics and Reconstruction Matter: Making Representation Encoders Ready for Text-to-Image Generation and Editing (PS-VAE)",
    "venue": "arXiv:2512.17909",
    "year": 2025,
    "target": "B/C",
    "drift_magnitude": "Identifies 'off-manifold latents' from unconstrained representation space leading to unreliable decoding. Encoder's weak pixel-level reconstruction causes structural/texture artifacts. PS-VAE rFID: 0.534→0.203, PSNR: 26.18→28.79, SSIM: 0.715→0.817 vs vanilla VAE.",
    "structurally_identical": true,
    "code": true,
    "url": "https://arxiv.org/abs/2512.17909"
  }
]
```

---

## Analysis

**claims_verified = 4**

All 4 papers provide structurally identical evidence for VAE-induced or input-corruption-induced semantic degradation in vision-language pipelines:

| # | Paper | Core Finding | Target |
|---|-------|-------------|--------|
| 1 | BAT-CLIP | CLIP zero-shot accuracy craters under Gaussian noise/blur — 78% relative drop on CIFAR-100 at severity 5. TTA adaptation recovers 5-10% but corruption still degrades. | A |
| 2 | VLM Corruption (2504.13690) | Text recognition deteriorates severely under blur/snow; object reasoning fails under frost/impulse noise. Explicitly maps corruption type → frequency domain characteristics → VLM failure modes. | A |
| 3 | REED-VAE | Vanilla VAE encode-decode cycles destroy images through artifact accumulation and high-frequency loss. "Essentially destroyed" after ~5 iterations. Cites specific perceptual quality degradation from reconstruction error. | B |
| 4 | PS-VAE | "Off-manifold latents" cause unreliable decoding; discriminative encoder features lack compact regularization, causing structural artifacts. Quantifies rFID/PSNR/SSIM gaps. Explicitly frames this as a VAE latent space problem for vision-language generation. | B/C |

---

## Key Quantitative Evidence

### ≥5% Degradation (Target A threshold met)

- **BAT-CLIP**: Absolute accuracy drop from 49% → 10.79% = **38.2 percentage points** under Gaussian noise severity 5 on CIFAR-100.
- **BAT-CLIP mean improvements needed**: +9.7% (CIFAR-10C), +5.94% (CIFAR-100C), +5.12% (ImageNet-C) to close the corruption gap.
- **VLM Corruption paper**: Text recognition accuracy drops to near-random on ImageNet-C blur/noise at severity 5.

### VAE Encode-Decode Degradation (Target B/C threshold met)

- **REED-VAE**: Visual artifact accumulation after each VAE encode-decode iteration. "Essentially destroyed" at ~5 iterations without REED training. High-frequency information loss quantified in frequency domain analysis.
- **PS-VAE**: Off-manifold latent drift quantified via rFID (0.534→0.203), PSNR (26.18→28.79), SSIM (0.715→0.817). Explicitly identifies representation-to-latent mapping failure as structural obstacle.

---

## Refined Keywords for Next Search

If additional papers needed:
- `"VAE posterior collapse vision encoder"` — focuses on VAE KL regularization forcing posterior to prior
- `"diffusion model latent space drift CLIP representation"` — connects VAE latent drift to CLIP-level semantic degradation
- `"image autoencoder semantic drift reconstruction error"` — more general framing

---

## Limitations / Notes

- **No paper explicitly titles "VAE induces CLIP degradation"** — the structurally identical findings are in adjacent domains (VLM corruption robustness, latent diffusion, representation learning). The CNLSA framing (VAE → CLIP semantic drift) is a novel synthesis.
- **BAT-CLIP is the strongest Target A candidate** — gives precise accuracy numbers across corruption types and backbones.
- **REED-VAE is the strongest Target B candidate** — directly quantifies encode-decode cycle damage.
- **PS-VAE bridges Target B and C** — addresses off-manifold latent drift with quantitative metrics.

---

**next_search_kw**: `"VAE posterior collapse vision foundation model CLIP semantic degradation"
---

## Additional Papers (Parallel Scout run — 0415-PM)

### Topic 1 (VAE/CLIP — CNLSA adjacent)

**SVG — ICLR 2026** | arXiv 2510.15301 | GitHub: shiml20/SVG
Directly replaces VAE with DINOv2 self-supervised features for latent diffusion. Explicitly documents VAE latent spaces as "weakly discriminable." Code verified. **Most directly relevant to CNLSA problem.**

**CLIP is All You Need** | arXiv 2511.08075 | No code | 2025
Proves semantic representation in Stable Diffusion comes from CLIP, not the diffusion process. Key empirical grounding for CNLSA reframing: CLIP survives VAE round-trip but diffusion decoder is lossy.

**Latent-CLIP** | arXiv 2503.08455 | No official code | 2025
Trains CLIP directly in VAE latent space — enabling reward optimization without VAE decode. Matches pixel-space CLIP zero-shot classification.

### Topic 2 (TrACE-RM Redesign)

**DiNa-LRM** | arXiv 2602.11146 | GitHub: HKUST-C4G/diffusion-rm | 2026
Diffusion-native step-level latent reward model. **Most directly relevant to TrACE-RM redesign.** Code verified.

**LPO** | arXiv 2502.01051 | GitHub: casiatao/LPO + Kwai-Kolors/LPO | NeurIPS 2025
Diffusion model as step-level reward model in noisy latent space. 2.5-28× training speedup. Code verified (two repos).

**DAS** | arXiv 2501.05803 | GitHub: krafton-ai/DAS | ICLR 2025 Spotlight
SMC-based test-time reward alignment — prevents over-optimization via tempered sampling. Code verified.

**ReNO** | arXiv 2406.04312 | GitHub: ExplainableML/ReNO | NeurIPS 2024
Optimizes initial noise for one-step T2I models. Foundation for latent reward work.

**Null-TTA** | arXiv 2511.20889 | GitHub: kthone/null-tta | 2025
Optimizes null-text embedding in CFG space for reward alignment. Code verified.
