#!/usr/bin/env python3
"""
Exp 1: DINOv2 Vulnerability Test (CPU)
======================================
VAE encode-decode roundtrip (σ=0) on n=50 COCO val2017 images.
Extract DINOv2-small (ViT-S/14) patch tokens for original and reconstructed.
Compute per-image cosine similarity of patch token sets.
Pre-registered threshold: mean CS > 0.97 → CLIP-specificity survives.

Prior result: DINOv2 ViT-B/14: CS=0.343, d=-3.296

All CPU, torch.no_grad(), n=50, seed=42
"""

import os
import sys
import json
import math
import torch
import numpy as np
from PIL import Image
from diffusers import AutoencoderKL
from transformers import AutoModel

torch.manual_seed(42)
np.random.seed(42)

OUT_DIR = "/home/kas/.openclaw/workspace-domain/research/0415-pm-cnlsa-cpu"
OUT_JSON = os.path.join(OUT_DIR, "exp1_dinov2_results.json")
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Paths ────────────────────────────────────────────────────────────────────
COCO_PATH = "/home/kas/.cache/huggingface/hub/datasets--merve--coco/snapshots/9e50abcdc1361852f34841af4939cbcd2d37c92f/val2017/"

N = 50
THRESHOLD = 0.97
DEVICE = "cpu"
DINOV2_MODEL = "facebook/dinov2-small"

# ─── Device ───────────────────────────────────────────────────────────────────
print(f"Device: {DEVICE}")

# ─── Models ──────────────────────────────────────────────────────────────────
print("Loading models...")

# DINOv2-small (ViT-S/14, ~22M params, CPU-feasible)
dinov2 = AutoModel.from_pretrained(DINOV2_MODEL)
dinov2 = dinov2.to(DEVICE).eval()
print(f"DINOv2-small loaded.")

# SDXL VAE (same as all prior CNLSA experiments)
vae = AutoencoderKL.from_pretrained('stabilityai/sd-vae-ft-mse')
vae = vae.to(DEVICE).eval()
print("SDXL VAE loaded.")

# ─── Image collection (same seed=42 as prior CNLSA runs) ─────────────────────
all_files = [
    f for f in os.listdir(COCO_PATH)
    if f.lower().endswith(('.jpg', '.jpeg', '.png'))
]
print(f"COCO val2017: {len(all_files)} images available")

selected = np.random.RandomState(42).choice(
    all_files, size=min(N, len(all_files)), replace=False
).tolist()
n_actual = len(selected)
print(f"Selected n={n_actual} images (seed=42, same as prior CNLSA)")

# ─── DINOv2 preprocessing ────────────────────────────────────────────────────
# DINOv2 uses ImageNet-normalized input, 224x224
from torchvision import transforms
dinov2_transform = transforms.Compose([
    transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.BICUBIC),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def get_dinov2_patch_tokens(model, pil_img):
    """
    Return patch tokens from DINOv2 (before the CLS token / global head).
    For ViT-S/14: num_patches = (224/14)^2 = 256 patch tokens.
    Shape: [num_patches, hidden_dim]  e.g. [256, 384]
    """
    img_tensor = dinov2_transform(pil_img).unsqueeze(0).to(DEVICE)  # [1, 3, 224, 224]
    with torch.no_grad():
        # transformers DINOv2 outputs: last_hidden_state (patch tokens + CLS)
        # We skip the CLS token (first token)
        outputs = model(img_tensor)
        # last_hidden_state: [1, 257, 384] for ViT-S/14 (256 patches + CLS)
        patch_tokens = outputs.last_hidden_state[0, 1:, :]  # [256, 384], skip CLS
    return patch_tokens.cpu().numpy()  # [num_patches, hidden_dim]

# ─── VAE encode-decode helpers ───────────────────────────────────────────────
def vae_roundtrip(pil_img, target_size=512):
    """
    VAE encode → decode at σ=0 (no noise).
    Returns PIL image in RGB.
    """
    w, h = pil_img.size
    img = pil_img.convert('RGB').resize((target_size, target_size), Image.LANCZOS)
    arr = np.array(img).astype(np.float32) / 255.0  # [0, 1]
    arr = arr * 2.0 - 1.0
    tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).to(DEVICE)  # [1, 3, 512, 512]

    with torch.no_grad():
        latent = vae.encode(tensor).latent_dist.sample()  # [1, 4, 64, 64]
        recon_tensor = vae.decode(latent).sample  # [1, 3, 512, 512]

    recon_tensor = recon_tensor.squeeze(0).permute(1, 2, 0).cpu().numpy()  # [512, 512, 3]
    recon_tensor = np.clip(recon_tensor, -1.0, 1.0)
    recon_arr = (recon_tensor + 1.0) / 2.0 * 255.0
    recon_arr = recon_arr.astype(np.uint8)
    return Image.fromarray(recon_arr, mode='RGB')

# ─── Cosine similarity between two sets of patch tokens ───────────────────────
def patch_token_cosine_similarity(tokens_a, tokens_b):
    """
    Compute cosine similarity between two sets of patch tokens.
    tokens_a, tokens_b: [num_patches, hidden_dim]
    Returns scalar cosine similarity (flattened dot product of flattened vectors).
    """
    # Flatten each set of tokens
    vec_a = tokens_a.flatten()
    vec_b = tokens_b.flatten()
    # L2 normalize the flattened vectors
    vec_a = vec_a / (np.linalg.norm(vec_a) + 1e-10)
    vec_b = vec_b / (np.linalg.norm(vec_b) + 1e-10)
    return float(np.dot(vec_a, vec_b))

# ─── Main loop ────────────────────────────────────────────────────────────────
print(f"\nRunning DINOv2 vulnerability test (n={n_actual})...")
print("=" * 60)

cos_sims = []
failures = 0

for i, fname in enumerate(selected):
    try:
        orig_path = os.path.join(COCO_PATH, fname)
        orig_pil = Image.open(orig_path).convert('RGB')

        # Original DINOv2 patch tokens
        orig_tokens = get_dinov2_patch_tokens(dinov2, orig_pil)

        # VAE roundtrip (same as prior CNLSA: 512x512, σ=0)
        recon_pil = vae_roundtrip(orig_pil)

        # Reconstructed DINOv2 patch tokens
        recon_tokens = get_dinov2_patch_tokens(dinov2, recon_pil)

        # Cosine similarity between patch token sets
        cs = patch_token_cosine_similarity(orig_tokens, recon_tokens)
        cos_sims.append(cs)

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{n_actual}] running mean DINOv2 CS: {np.mean(cos_sims):.4f}")

    except Exception as e:
        failures += 1
        print(f"  [{i+1}] FAILED {fname}: {e}")
        import traceback
        traceback.print_exc()

# ─── Statistics ───────────────────────────────────────────────────────────────
cos_sims = np.array(cos_sims)
n_valid = len(cos_sims)
mean_cs = float(np.mean(cos_sims))
std_cs = float(np.std(cos_sims))

# Effect size: Cohen's d vs 0
cohens_d = float(mean_cs / std_cs) if std_cs > 0 else 0.0

# One-sample t-test against threshold
from scipy import stats as scipy_stats
t_stat, p_val = scipy_stats.ttest_1samp(cos_sims, THRESHOLD)

# Also test against 0 (baseline)
t_stat_vs_zero, p_val_vs_zero = scipy_stats.ttest_1samp(cos_sims, 0.0)

threshold_check = "PASS" if mean_cs > THRESHOLD else "FAIL"

print("\n" + "=" * 60)
print("  DINOv2 VIABILITY TEST RESULTS (Exp 1)")
print("=" * 60)
print(f"  n images:             {n_valid}")
print(f"  failures:             {failures}")
print(f"  mean DINOv2 CS:       {mean_cs:.4f}")
print(f"  std DINOv2 CS:        {std_cs:.4f}")
print(f"  min DINOv2 CS:        {cos_sims.min():.4f}")
print(f"  max DINOv2 CS:        {cos_sims.max():.4f}")
print(f"  Cohen's d:            {cohens_d:.4f}")
print(f"  t-stat vs {THRESHOLD}:  {t_stat:.4f}")
print(f"  p-value vs threshold: {p_val:.6f}")
print(f"  t-stat vs 0:          {t_stat_vs_zero:.4f}")
print(f"  DECISION:              threshold_check={threshold_check}")
print(f"  (threshold: mean CS > {THRESHOLD})")
print("=" * 60)

# Architectural note
architectural_note = (
    "Using facebook/dinov2-small (ViT-S/14, 384 dim, 22M params) vs prior ViT-B/14. "
    "Architectural confound: smaller model may have different sensitivity to VAE artifacts. "
    "Direct comparison with prior ViT-B/14 CS=0.343 is confounded by model size."
)

# Save results
results = {
    "experiment": "DINOv2 Vulnerability Test (Exp 1)",
    "model": DINOV2_MODEL,
    "architecture": "ViT-S/14",
    "n": n_valid,
    "failures": failures,
    "mean_cs": mean_cs,
    "std_cs": std_cs,
    "min_cs": float(cos_sims.min()),
    "max_cs": float(cos_sims.max()),
    "cohens_d": cohens_d,
    "threshold": THRESHOLD,
    "threshold_check": threshold_check,
    "t_stat_vs_threshold": float(t_stat),
    "p_value": float(p_val),
    "t_stat_vs_zero": float(t_stat_vs_zero),
    "p_value_vs_zero": float(p_val_vs_zero),
    "per_image_cosine_similarities": cos_sims.tolist(),
    "architectural_note": architectural_note,
    "prior_result": "DINOv2 ViT-B/14: CS=0.343, d=-3.296",
    "image_selection": "np.random.RandomState(42).choice, same as prior CNLSA runs",
    "vae": "stabilityai/sd-vae-ft-mse (same as all prior CNLSA)",
    "image_size_vae": 512,
}

with open(OUT_JSON, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {OUT_JSON}")
