#!/usr/bin/env python3
"""
exp_nova7_latent_contraction.py — Exp-Nova-7: VAE Latent Contraction Asymmetry
=============================================================================
Measures whether VAE latents contract differently for natural vs synthetic images.

Hypothesis: Natural images are OOD for the VAE decoder → latent mean gets pulled
toward decoder's mode attractor → larger |μ| contraction relative to synthetic.

Procedure:
  1. Sample 50 natural images (CIFAR-10, diverse semantic content)
     + 50 synthetic procedural images (random noise, checkerboards, gradients)
  2. Encode each to VAE latent → extract μ (mean of latent distribution)
  3. Compute mean L2 norm: |μ|_natural and |μ|_synthetic
  4. contraction_ratio = |μ|_natural / |μ|_synthetic

Failure condition: contraction_ratio < 1.1 → VAE decoder mode collapse
  is NOT the mechanism; revisit DINOv2 structural preservation hypothesis.

CPU-only, ~15 min.
"""

import torch
import torchvision
import torchvision.transforms as T
import numpy as np
from PIL import Image
import time
import os
import gc
import math

# ── Config ────────────────────────────────────────────────────────────────────
DEVICE = "cpu"
DTYPE = torch.float32
N_PER_CLASS = 50          # 50 natural + 50 synthetic = 100 total
BATCH_SIZE = 10            # small batch to keep RAM happy
SEED = 42
SYNTHETIC_SEED = 999
SYNTH_RESOLUTION = 32      # CIFAR-10 native resolution, will resize to 224 for VAE

torch.manual_seed(SEED)
np.random.seed(SEED)

# ── Load VAE ─────────────────────────────────────────────────────────────────
print("Loading SD-VAE-ft-mse...")
from diffusers.models import AutoencoderKL
vae = AutoencoderKL.from_pretrained(
    "stabilityai/sd-vae-ft-mse",
    cache_dir=os.path.expanduser("~/.cache/huggingface/hub/"),
    torch_dtype=DTYPE,
)
vae = vae.to(DEVICE)
vae.eval()
print(f"  VAE loaded. Latent channels={vae.config.latent_channels}, spatial factor={vae.config.scaling_factor}")

# ── Natural images: CIFAR-10 train set ───────────────────────────────────────
print("\n[1] Preparing natural images (CIFAR-10)...")
transform_224 = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
])
natural_set = torchvision.datasets.CIFAR10(
    root="./data", train=True, download=True, transform=transform_224
)
# sample randomly from entire training set
all_indices = list(range(len(natural_set)))
np.random.shuffle(all_indices)
natural_indices = all_indices[:N_PER_CLASS]
natural_tensors = torch.stack([natural_set[i][0] for i in natural_indices])
print(f"  Sampled {len(natural_tensors)} natural images, shape={natural_tensors.shape}")

# ── Synthetic images: procedural patterns ───────────────────────────────────
print("\n[2] Preparing synthetic images (procedural)...")

def make_synthetic_image(resolution=224, pattern_type="random", seed=None):
    """Generate a single synthetic procedural image."""
    if seed is not None:
        rng = np.random.RandomState(seed)
    else:
        rng = np.random.RandomState(None)

    img_np = np.zeros((resolution, resolution, 3), dtype=np.float32)

    if pattern_type == "random_noise":
        img_np = rng.randn(resolution, resolution, 3).astype(np.float32)

    elif pattern_type == "checkerboard":
        sq = resolution // 8
        for y in range(resolution):
            for x in range(resolution):
                img_np[y, x] = ((y // sq) + (x // sq)) % 2

    elif pattern_type == "gradient":
        for y in range(resolution):
            for x in range(resolution):
                img_np[y, x] = [x/resolution, y/resolution, (x+y)/(2*resolution)]

    elif pattern_type == "sine_wave":
        for y in range(resolution):
            for x in range(resolution):
                v = math.sin(x/10) * math.sin(y/10)
                img_np[y, x] = [v*0.5+0.5] * 3

    elif pattern_type == "random_blocks":
        block_size = resolution // 4
        for by in range(4):
            for bx in range(4):
                color = rng.rand(3)
                for dy in range(block_size):
                    for dx in range(block_size):
                        py = by * block_size + dy
                        px = bx * block_size + dx
                        if py < resolution and px < resolution:
                            img_np[py, px] = color

    # Clip to [0,1] and convert to tensor CHW
    img_np = np.clip(img_np, 0, 1)
    img_tensor = torch.from_numpy(img_np).permute(2, 0, 1)
    return img_tensor

# Generate diverse synthetic patterns
pattern_types = ["random_noise", "checkerboard", "gradient", "sine_wave", "random_blocks"]
synthetic_tensors = []
for i in range(N_PER_CLASS):
    pattern = pattern_types[i % len(pattern_types)]
    seed = SYNTHETIC_SEED + i
    tensor = make_synthetic_image(resolution=224, pattern_type=pattern, seed=seed)
    synthetic_tensors.append(tensor)

synthetic_tensors = torch.stack(synthetic_tensors)
print(f"  Generated {len(synthetic_tensors)} synthetic images, shape={synthetic_tensors.shape}")

# ── Encode to VAE latent space ────────────────────────────────────────────────
print("\n[3] Encoding natural images to VAE latent space...")
start_time = time.time()

natural_means = []
with torch.no_grad():
    for i in range(0, len(natural_tensors), BATCH_SIZE):
        batch = natural_tensors[i:i+BATCH_SIZE].to(DEVICE).float()
        dist = vae.encode(batch).latent_dist
        mu = dist.mean  # [B, 4, H, W] for SD-VAE
        # Flatten spatial dimensions and compute L2 norm per image
        for j in range(mu.shape[0]):
            mu_j = mu[j]           # [4, H, W]
            l2 = mu_j.flatten().norm().item()
            natural_means.append(l2)
        if (i // BATCH_SIZE + 1) % 5 == 0:
            print(f"  natural [{i+len(batch)}/{len(natural_tensors)}]")

print(f"  natural_means collected: {len(natural_means)}")

print("\n[4] Encoding synthetic images to VAE latent space...")
synthetic_means = []
with torch.no_grad():
    for i in range(0, len(synthetic_tensors), BATCH_SIZE):
        batch = synthetic_tensors[i:i+BATCH_SIZE].to(DEVICE).float()
        dist = vae.encode(batch).latent_dist
        mu = dist.mean
        for j in range(mu.shape[0]):
            mu_j = mu[j]
            l2 = mu_j.flatten().norm().item()
            synthetic_means.append(l2)
        if (i // BATCH_SIZE + 1) % 5 == 0:
            print(f"  synthetic [{i+len(batch)}/{len(synthetic_tensors)}]")

print(f"  synthetic_means collected: {len(synthetic_means)}")

total_time = time.time() - start_time

# ── Compute metrics ────────────────────────────────────────────────────────────
natural_means_arr = np.array(natural_means)
synthetic_means_arr = np.array(synthetic_means)

mu_natural = natural_means_arr.mean()
mu_synthetic = synthetic_means_arr.mean()
std_natural = natural_means_arr.std()
std_synthetic = synthetic_means_arr.std()

contraction_ratio = mu_natural / mu_synthetic if mu_synthetic > 0 else float('nan')

# Additional: log-variance statistics
print("\n[5] Computing latent log-variance stats...")
natural_lvar = []
synthetic_lvar = []

with torch.no_grad():
    for i in range(0, len(natural_tensors), BATCH_SIZE):
        batch = natural_tensors[i:i+BATCH_SIZE].to(DEVICE).float()
        dist = vae.encode(batch).latent_dist
        logvar = dist.logvar  # [B, 4, H, W]
        for j in range(logvar.shape[0]):
            lv = logvar[j].flatten().mean().item()
            natural_lvar.append(lv)

    for i in range(0, len(synthetic_tensors), BATCH_SIZE):
        batch = synthetic_tensors[i:i+BATCH_SIZE].to(DEVICE).float()
        dist = vae.encode(batch).latent_dist
        logvar = dist.logvar
        for j in range(logvar.shape[0]):
            lv = logvar[j].flatten().mean().item()
            synthetic_lvar.append(lv)

natural_lvar_arr = np.array(natural_lvar)
synthetic_lvar_arr = np.array(synthetic_lvar)

# ── Print Results ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Exp-Nova-7 RESULTS: VAE Latent Contraction Asymmetry")
print("=" * 60)
print(f"  |μ|_natural   = {mu_natural:.6f} (std={std_natural:.6f})")
print(f"  |μ|_synthetic = {mu_synthetic:.6f} (std={std_synthetic:.6f})")
print(f"  contraction_ratio = |μ|_natural / |μ|_synthetic = {contraction_ratio:.6f}")
print(f"  natural logvar mean: {natural_lvar_arr.mean():.4f} (std={natural_lvar_arr.std():.4f})")
print(f"  synthetic logvar mean: {synthetic_lvar_arr.mean():.4f} (std={synthetic_lvar_arr.std():.4f})")

# T-test for significance
from scipy import stats
t_stat, p_val = stats.ttest_ind(natural_means_arr, synthetic_means_arr)
print(f"  t-test: t={t_stat:.4f}, p={p_val:.6f}")

# Verdict
FAILURE_THRESHOLD = 1.1
if contraction_ratio < FAILURE_THRESHOLD:
    verdict = "fail"
    verdict_msg = (
        f"contraction_ratio={contraction_ratio:.4f} < {FAILURE_THRESHOLD}."
        " VAE decoder mode collapse is NOT the mechanism."
        " Revisit DINOv2 structural preservation hypothesis."
    )
else:
    verdict = "pass"
    verdict_msg = (
        f"contraction_ratio={contraction_ratio:.4f} >= {FAILURE_THRESHOLD}."
        " Natural images show asymmetric contraction → decoder mode collapse"
        " is consistent with observed semantic drift."
    )

print(f"\n  VERDICT: {verdict.upper()}")
print(f"  {verdict_msg}")
print(f"\n  Runtime: {total_time:.0f}s ({total_time/60:.2f} min)")
print("=" * 60)

# Save structured results
import json
results = {
    "|μ|_natural": float(mu_natural),
    "|μ|_synthetic": float(mu_synthetic),
    "contraction_ratio": float(contraction_ratio),
    "verdict": verdict,
    "runtime_minutes": round(total_time / 60, 2),
    "t_statistic": float(t_stat),
    "p_value": float(p_val),
    "natural_mean_l2_std": float(std_natural),
    "synthetic_mean_l2_std": float(std_synthetic),
    "natural_logvar_mean": float(natural_lvar_arr.mean()),
    "synthetic_logvar_mean": float(synthetic_lvar_arr.mean()),
}
results_path = os.path.join(os.getcwd(), "exp_nova7_results.json")
with open(results_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {results_path}")
print(json.dumps(results, indent=2))