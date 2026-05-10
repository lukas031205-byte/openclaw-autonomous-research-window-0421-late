# Kernel Code Verify — 2026-05-10

## Paper 1: 2605.06388
**Title:** Reconstruction or Semantics? What Makes a Latent Space Useful for Robotic World Models

| Field | Value |
|-------|-------|
| paper_id | 2605.06388 |
| arXiv | https://arxiv.org/abs/2605.06388 |
| project_page_url | https://hskalin.github.io/semantic-wm/ |
| code_url | null |
| verified | false |

**Verification notes:**
- Project page found and live: https://hskalin.github.io/semantic-wm/
- Hugging Face model page found: https://huggingface.co/Nilaksh404/semantic-wm (contains PyTorch checkpoints for world models)
- No GitHub repository found for this paper
- Author GitHub (hskalin / Nilaksh) has 23 repos but none explicitly named "semantic-wm" — the project page does not link to a code repository
- arXiv page shows no code link

---

## Paper 2: 2603.17825
**Title:** Steering Video Diffusion Transformers with Massive Activations (STAS)

| Field | Value |
|-------|-------|
| paper_id | 2603.17825 |
| arXiv | https://arxiv.org/abs/2603.17825 |
| project_page_url | https://xianhang.github.io/webpage-STAS/ |
| code_url | https://github.com/Xianhang/STAS |
| verified | true |

**Verification notes:**
- GitHub repo confirmed: https://github.com/Xianhang/STAS
  - Description: "Code for paper 'Steering Video Diffusion Transformers with Massive Activations'"
  - Author: Xianhang (https://github.com/Xianhang)
- Project page found and live: https://xianhang.github.io/webpage-STAS/
- arXiv page does not link to code directly, but GitHub search and author page confirm the repo

---

## Summary JSON

```json
[
  {
    "paper_id": "2605.06388",
    "code_url": null,
    "project_page_url": "https://hskalin.github.io/semantic-wm/",
    "verified": false
  },
  {
    "paper_id": "2603.17825",
    "code_url": "https://github.com/Xianhang/STAS",
    "project_page_url": "https://xianhang.github.io/webpage-STAS/",
    "verified": true
  }
]
```