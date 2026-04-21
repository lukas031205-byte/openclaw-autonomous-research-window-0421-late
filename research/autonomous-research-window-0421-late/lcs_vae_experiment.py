#!/usr/bin/env python3
"""
LCS Compute Gate VAE Latent Perturbation Experiment
=====================================================
H0: DINOv2 L2 does NOT predict CLIP semantic inconsistency on VAE-latent-perturbed images.
H1: DINOv2 L2 (probe) correlates with CLIP cosine similarity (ground truth) across VAE latent perturbations.

Dataset: 60 CIFAR-10 test images (12 per class × 5 classes), resized to 224×224
VAE:     stabilityai/sd-vae-ft-mse
Encoders: DINOv2 ViT-S/14 (probe) + CLIP ViT-B/32 (ground truth)
σ levels: {0, 0.05, 0.1, 0.2, 0.4}
Output:  Pearson r(DINO_L2, CLIP_CS) with 95% CI, per-σ breakdown, PASS/FAIL/WEAK verdict
"""

import torch
import numpy as np
import pandas as pd
from PIL import Image
import torchvision.transforms as T
import torchvision.datasets as datasets
from scipy import stats
import time
import warnings
import os
import json

warnings.filterwarnings("ignore")

# ── Config ────────────────────────────────────────────────────────────────────
DEVICE   = "cpu"
SEED     = 42
SIGMAS   = [0.0, 0.05, 0.1, 0.2, 0.4]
N_PER_CLASS, N_CLASSES = 12, 5
IMAGENET_CLASSES = [0, 1, 2, 3, 4]   # airplane, automobile, bird, cat, deer (CIFAR-10 mapping)
IMG_SIZE = 224

np.random.seed(SEED)
torch.manual_seed(SEED)

WORKDIR  = "/home/kas/.openclaw/workspace-domain/research/autonomous-research-window-0421-late"
OUT_PATH = os.path.join(WORKDIR, "kernel-lcs-result.md")

# ── Load CIFAR-10 test set ────────────────────────────────────────────────────
print("Loading CIFAR-10 test set...")
cifar_root = os.path.expanduser("~/.cache/torchvision/datasets/cifar10")
cifar_test = datasets.CIFAR10(root=cifar_root, train=False, download=True)

# Collect indices: N_PER_CLASS per IMAGENET_CLASSES
# CIFAR-10 class labels: 0=plane,1=car,2=bird,3=cat,4=deer
selected_indices = []
counts = {c: 0 for c in IMAGENET_CLASSES}
for idx, (_, label) in enumerate(cifar_test):
    if label in IMAGENET_CLASSES and counts[label] < N_PER_CLASS:
        selected_indices.append(idx)
        counts[label] += 1
    if all(v >= N_PER_CLASS for v in counts.values()):
        break

assert len(selected_indices) == N_PER_CLASS * N_CLASSES, \
    f"Expected {N_PER_CLASS * N_CLASSES} images, got {len(selected_indices)}"
print(f"  Selected {len(selected_indices)} images (12 per class × 5 classes)")

# ── Image transforms ───────────────────────────────────────────────────────────
resize_to_imagenet = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.ToTensor(),
])
norm = T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

def pil_to_tensor(path_or_pil):
    img = path_or_pil if isinstance(path_or_pil, Image.Image) else Image.open(path_or_pil).convert("RGB")
    return resize_to_imagenet(img)

# ── Load models ────────────────────────────────────────────────────────────────
print("Loading models (CPU)...")
t0 = time.time()

from transformers import CLIPProcessor, CLIPModel
from diffusers import AutoencoderKL

# VAE
vae = AutoencoderKL.from_pretrained(
    "stabilityai/sd-vae-ft-mse",
    torch_dtype=torch.float32,
)
vae.eval()
vae.to(DEVICE)
print("  VAE loaded (stabilityai/sd-vae-ft-mse)")

# DINOv2
dinov2 = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14")
dinov2.eval()
dinov2.to(DEVICE)
DINO_DIM = dinov2.embed_dim  # 384
print(f"  DINOv2 loaded (ViT-S/14, {DINO_DIM}-dim)")

# CLIP
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
clip_model.eval()
clip_model.to(DEVICE)
print("  CLIP loaded (ViT-B/32)")

print(f"  Model load time: {time.time()-t0:.1f}s")

# ── Helper functions ───────────────────────────────────────────────────────────
def encode_vae(img_tensor):
    """Convert normalized ImageNet tensor to VAE latent."""
    # VAE expects unnormalized [0,1] input in [-1,1] range
    x = img_tensor.unsqueeze(0).to(DEVICE)  # 1×3×224×224
    x = x * 2 - 1  # [0,1] → [-1,1]
    with torch.no_grad():
        latents = vae.encode(x).latent_dist.sample()
    # VAE latent: 4×64×64 (spatial 1/32 reduction)
    return latents.squeeze(0)  # 4×64×64

def decode_vae(latent):
    with torch.no_grad():
        decoded = vae.decode(latent.unsqueeze(0)).sample
    # Output: 4×64×64 → 3×224×224 (after decode)
    # Map back to [0,1] then ImageNet norm
    decoded = decoded.squeeze(0).cpu()
    decoded = (decoded + 1) / 2  # [-1,1] → [0,1]
    return decoded.clamp(0, 1)

def extract_dino(img_tensor):
    """Extract DINOv2-S features from an ImageNet-normalized tensor."""
    x = img_tensor.to(DEVICE)
    with torch.no_grad():
        feat = dinov2(x.unsqueeze(0))
    return feat.squeeze(0).cpu()

def extract_clip(img_tensor_norm):
    """Extract CLIP ViT-B/32 features from ImageNet-normalized tensor."""
    # Convert normalized tensor → PIL for CLIP processor
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3,1,1)
    std  = torch.tensor([0.229, 0.224, 0.225]).view(3,1,1)
    x = img_tensor_norm.cpu() * std + mean  # denormalize
    x = x.clamp(0, 1)
    pil_img = T.ToPILImage()(x)
    inputs = clip_processor(images=pil_img, return_tensors="pt")
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    with torch.no_grad():
        out = clip_model.get_image_features(**inputs)
    # out is BaseModelOutputWithPooling; pooler_output is [1, 512]
    feat = out.pooler_output.squeeze(0).cpu()  # [512]
    return feat

def cosine_sim(a, b):
    a, b = a.float(), b.float()
    return torch.nn.functional.cosine_similarity(a.unsqueeze(0), b.unsqueeze(0)).item()

# ── Main experiment loop ──────────────────────────────────────────────────────
records = []  # {(sigma, img_idx): {dino_l2, clip_cs, ...}}
results = {s: {"dino_l2": [], "clip_cs": []} for s in SIGMAS}

print(f"\nRunning experiment: {N_PER_CLASS * N_CLASSES} images × {len(SIGMAS)} σ = {N_PER_CLASS * N_CLASSES * len(SIGMAS)} trials")
t_start = time.time()

for img_idx, cifar_idx in enumerate(selected_indices):
    img_pil, label = cifar_test[cifar_idx]

    # Resize to 224×224, convert to tensor, ImageNet-normalize
    img_t = resize_to_imagenet(img_pil)          # 3×224×224 [0,1]
    img_t_norm = norm(img_t)                      # ImageNet-normalized

    # Encode original with VAE
    z_orig = encode_vae(img_t)                     # 4×64×64 latent

    for sigma in SIGMAS:
        # ── Perturb latent ────────────────────────────────────────────────────
        if sigma > 0:
            noise = torch.randn_like(z_orig) * sigma
            z_pert = z_orig + noise
        else:
            z_pert = z_orig

        # ── Decode perturbed latent ─────────────────────────────────────────
        img_rec_t = decode_vae(z_pert)            # 3×224×224 [0,1]
        img_rec_norm = norm(img_rec_t)            # ImageNet-normalized

        # ── DINOv2 L2 ────────────────────────────────────────────────────────
        f_dino_orig = extract_dino(img_t_norm)
        f_dino_rec  = extract_dino(img_rec_norm)
        dino_l2 = torch.linalg.vector_norm(f_dino_orig - f_dino_rec).item()

        # ── CLIP cosine similarity ───────────────────────────────────────────
        f_clip_orig = extract_clip(img_t_norm)
        f_clip_rec  = extract_clip(img_rec_norm)
        clip_cs = cosine_sim(f_clip_orig, f_clip_rec)

        results[sigma]["dino_l2"].append(dino_l2)
        results[sigma]["clip_cs"].append(clip_cs)
        records.append({
            "img_idx": img_idx,
            "sigma": sigma,
            "label": label,
            "dino_l2": dino_l2,
            "clip_cs": clip_cs,
        })

    if (img_idx + 1) % 10 == 0:
        elapsed = time.time() - t_start
        print(f"  Processed {img_idx+1}/{len(selected_indices)} images ({elapsed:.1f}s)")

total_time = time.time() - t_start

# ── Correlation analysis ──────────────────────────────────────────────────────
print("\nComputing correlations...")

all_dino  = []
all_clip  = []
per_sigma = {}

for sigma in SIGMAS:
    dino_arr = np.array(results[sigma]["dino_l2"])
    clip_arr = np.array(results[sigma]["clip_cs"])
    r, p = stats.pearsonr(dino_arr, clip_arr)

    # 95% CI via Fisher z-transformation
    n = len(dino_arr)
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3)
    ci_lo = np.tanh(z - 1.96 * se)
    ci_hi = np.tanh(z + 1.96 * se)

    per_sigma[sigma] = {
        "r": r, "p": p,
        "ci_lo": ci_lo, "ci_hi": ci_hi,
        "n": n,
        "dino_l2_mean": dino_arr.mean(),
        "dino_l2_std":  dino_arr.std(),
        "clip_cs_mean": clip_arr.mean(),
        "clip_cs_std":  clip_arr.std(),
    }
    all_dino.extend(results[sigma]["dino_l2"])
    all_clip.extend(results[sigma]["clip_cs"])

# Global Pearson r across all 300 points
all_dino = np.array(all_dino)
all_clip = np.array(all_clip)
global_r, global_p = stats.pearsonr(all_dino, all_clip)
n_total = len(all_dino)
z_global = np.arctanh(global_r)
se_global = 1.0 / np.sqrt(n_total - 3)
global_ci_lo = np.tanh(z_global - 1.96 * se_global)
global_ci_hi = np.tanh(z_global + 1.96 * se_global)

# ── Verdict ───────────────────────────────────────────────────────────────────
if global_r < 0.3:
    verdict = "FALSIFIED"
elif global_r < 0.4:
    verdict = "WEAK"
else:
    verdict = "PROMISING"

# Stability check: r < 0.2 at ≥ 3/5 sigma levels
unstable_levels = sum(1 for s in SIGMAS if per_sigma[s]["r"] < 0.2)
if unstable_levels >= 3:
    verdict = "FALSIFIED (unstable)"

# ── Build result table ────────────────────────────────────────────────────────
print("\n" + "="*70)
print("LCS COMPUTE GATE — VAE LATENT PERTURBATION EXPERIMENT RESULTS")
print("="*70)
print(f"\nGlobal Pearson r: {global_r:.4f}  95% CI [{global_ci_lo:.4f}, {global_ci_hi:.4f}]  p={global_p:.2e}")
print(f"Verdict: {verdict}")
print(f"\nPer-σ Breakdown:")
print(f"{'σ':>6} {'r':>8} {'CI-lo':>8} {'CI-hi':>8} {'p':>12} {'n':>5}  {'DINO-L2 mean±std':>22}  {'CLIP-CS mean±std':>20}")
print("-"*100)
for sigma in SIGMAS:
    s = per_sigma[sigma]
    print(f"{sigma:6.2f} {s['r']:8.4f} {s['ci_lo']:8.4f} {s['ci_hi']:8.4f} {s['p']:12.2e} {s['n']:5d}  "
          f"{s['dino_l2_mean']:.4f}±{s['dino_l2_std']:.4f}  {s['clip_cs_mean']:.4f}±{s['clip_cs_std']:.4f}")

print(f"\nRuntime: {total_time/60:.1f} minutes ({total_time:.1f}s)")
print(f"Images: {len(selected_indices)}  σ levels: {len(SIGMAS)}  Total trials: {len(records)}")

# ── Write result markdown ──────────────────────────────────────────────────────
lines = [
    "# Kernel: LCS Compute Gate — VAE Latent Perturbation Result",
    "",
    "**Date:** 2026-04-21 11:40 CST",
    "**Script:** `lcs_vae_experiment.py`",
    "**Agent:** Kernel (subagent)",
    "",
    "## Experiment Summary",
    "",
    f"| Metric | Value |",
    f"|--------|-------|",
    f"| **Global Pearson r** | **{global_r:.4f}** |",
    f"| **95% CI** | [{global_ci_lo:.4f}, {global_ci_hi:.4f}] |",
    f"| **p-value** | {global_p:.2e} |",
    f"| **Total data points** | {n_total} (60 images × 5 σ) |",
    f"| **Verdict** | **{verdict}** |",
    f"| **Runtime** | {total_time/60:.1f} min |",
    "",
    "## Per-σ Breakdown Table",
    "",
    f"| σ | r | 95% CI | p-value | n | DINOv2 L2 (mean±std) | CLIP CS (mean±std) |",
    f"|---|-------|------------------|---------|---|----------------------|---------------------|",
]
for sigma in SIGMAS:
    s = per_sigma[sigma]
    lines.append(
        f"| {sigma:.2f} | {s['r']:.4f} | [{s['ci_lo']:.4f}, {s['ci_hi']:.4f}] | "
        f"{s['p']:.2e} | {s['n']} | {s['dino_l2_mean']:.4f}±{s['dino_l2_std']:.4f} | "
        f"{s['clip_cs_mean']:.4f}±{s['clip_cs_std']:.4f} |"
    )

lines += [
    "",
    "## Interpretation",
    "",
    f"- **Verdict: {verdict}**",
]
if verdict == "FALSIFIED":
    lines += [
        "- r(DINOv2 L2, CLIP CS) < 0.3 → H₀ **not rejected**, LCS Compute Gate is **falsified**.",
        "- DINOv2 structural distance does NOT reliably predict CLIP semantic drift under VAE latent perturbation.",
        "- Recommend abandoning LCS Compute Gate direction; shift to CNLSA/Send-VAE/TTC for paper.",
    ]
elif verdict == "WEAK":
    lines += [
        "- r ∈ [0.3, 0.4) → LCS Compute Gate is **weak but not falsified**.",
        "- Corroborates CNLSA-Bridge result (r=0.3681) as ceiling; VAE perturbation does not improve correlation.",
        "- Consider nonlinear transformation of DINOv2 L2 or combining with other proxy signals.",
    ]
else:  # PROMISING
    lines += [
        "- r ≥ 0.4 → LCS Compute Gate has **empirical foundation** on VAE latent perturbation.",
        "- DINOv2 L2 distance is a viable lightweight semantic consistency proxy.",
        "- Next step: build compute gate scheduler using this signal.",
    ]

lines += [
    "",
    "## Confound Mitigation",
    "",
    "| Property | This Experiment | Past (confounded) |",
    "|----------|----------------|------------------|",
    "| Noise domain | **VAE latent** | Pixel (confounded) |",
    "| Probe encoder | **DINOv2 ViT-S/14** | CLIP L2 (same-model) |",
    "| Ground truth | **CLIP ViT-B/32** | CLIP cosine (same-model) |",
    "",
    "## References",
    "",
    "- VAE: `stabilityai/sd-vae-ft-mse`",
    "- DINOv2: `facebook/dinov2-small` (ViT-S/14, 384-dim)",
    "- CLIP: `openai/clip-vit-base-patch32` (ViT-B/32)",
    "",
    "---\n*Generated by Kernel subagent — LCS Compute Gate CPU Validation*\n",
]

result_md = "\n".join(lines)
with open(OUT_PATH, "w") as f:
    f.write(result_md)

print(f"\nResult written to: {OUT_PATH}")
print(f"\nFinal verdict: {verdict}  (r={global_r:.4f}, 95% CI [{global_ci_lo:.4f}, {global_ci_hi:.4f}])")
