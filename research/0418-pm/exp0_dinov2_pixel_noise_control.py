#!/usr/bin/env python3
"""
Exp 0: DINOv2 Pixel Noise Control
- Dataset: CIFAR-10 test (n=200)
- Pixel Gaussian noise σ ∈ {0, 10, 20, 40, 80}
- Measure: r(DINOv2_L2, pixel_noise_sigma) and r(CLIP_sim, pixel_noise_sigma)
- CPU budget: < 5 min

OPTIMIZED: batch CLIP processing for speed.
"""

import sys, os, time
import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

WORK_DIR = '/home/kas/.openclaw/workspace-domain/research/0418-pm'
os.makedirs(WORK_DIR, exist_ok=True)

print("=" * 70)
print("EXP 0: DINOv2 Pixel Noise Control (CIFAR-10)")
print("=" * 70)

# ── Load CIFAR-10 ─────────────────────────────────────────────────────────────
print("\n[1/5] Loading CIFAR-10 test set...")
from torchvision.datasets import CIFAR10
from torchvision import transforms

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

cifar_root = os.path.expanduser('~/.cache/torchvision/datasets/cifar10')
cifar10 = CIFAR10(root=cifar_root, train=False, download=True, transform=transform)

np.random.seed(42)
n = 200
indices = []
for cls in range(10):
    cls_idx = [i for i, (_, l) in enumerate(cifar10) if l == cls]
    indices.extend(np.random.choice(cls_idx, size=n//10, replace=False).tolist())
indices = indices[:n]

images = torch.stack([cifar10[i][0] for i in indices])
labels = [cifar10[i][1] for i in indices]
print(f"  Loaded {len(images)} images, shape={images.shape}")

# ── Load DINOv2 ───────────────────────────────────────────────────────────────
print("\n[2/5] Loading DINOv2-small (CPU)...")
from transformers import AutoImageProcessor, AutoModel

dinov2_name = 'facebook/dinov2-small'
dino_processor = AutoImageProcessor.from_pretrained(dinov2_name, torch_dtype=torch.float32)
dino_model = AutoModel.from_pretrained(dinov2_name, torch_dtype=torch.float32)
dino_model.eval()
print(f"  DINOv2 feature dim: 384")

def batch_dinov2_features(imgs):
    """Compute DINOv2 CLS features for a batch of images [B,C,H,W]."""
    with torch.no_grad():
        inputs = dino_processor(images=imgs, return_tensors='pt')
        outputs = dino_model(**inputs)
        return outputs.last_hidden_state[:, 0]  # [B, 384]

# ── Load CLIP ─────────────────────────────────────────────────────────────────
print("\n[3/5] Loading CLIP (openai/clip-vit-base-patch32)...")
from transformers import CLIPModel, CLIPProcessor

clip_name = 'openai/clip-vit-base-patch32'
clip_processor = CLIPProcessor.from_pretrained(clip_name, torch_dtype=torch.float32)
clip_model = CLIPModel.from_pretrained(clip_name, torch_dtype=torch.float32)
clip_model.eval()

def batch_clip_features(imgs):
    """Compute CLIP image features for a batch [B,C,H,W] -> [B, 512]."""
    with torch.no_grad():
        inputs = clip_processor(images=imgs, return_tensors='pt')
        feat = clip_model.get_image_features(**inputs).pooler_output
        return feat

def batch_clip_similarity(imgs1, imgs2):
    """CLIP cosine similarity for two batches [B,C,H,W] -> [B]."""
    feat1 = batch_clip_features(imgs1)
    feat2 = batch_clip_features(imgs2)
    feat1 = feat1 / feat1.norm(dim=-1, keepdim=True)
    feat2 = feat2 / feat2.norm(dim=-1, keepdim=True)
    return (feat1 * feat2).sum(dim=-1)  # [B]

# Test batch CLIP
test_sim = batch_clip_similarity(images[:2], images[:2])
print(f"  Batch CLIP self-similarity (expected ~1.0): {test_sim.mean():.4f}")

# ── Noise Levels & Loop ────────────────────────────────────────────────────────
print("\n[4/5] Running pixel noise experiment (BATCHED)...")
sigma_levels = [0, 10, 20, 40, 80]
NOISE_SCALE = 255.0

BATCH = 50  # batch size for CLIP

results = {sigma: {'dinov2_l2': np.zeros(n), 'clip_sim': np.zeros(n)} for sigma in sigma_levels}

t_start = time.time()

for sigma in sigma_levels:
    print(f"\n  --- σ = {sigma} ---")
    t_sigma = time.time()
    
    # Generate noisy images
    if sigma == 0:
        noisy_images = images
    else:
        noise = torch.randn_like(images) * (sigma / NOISE_SCALE)
        noisy_images = torch.clamp(images + noise, 0.0, 1.0)
    
    # DINOv2 L2 distance (batched)
    with torch.no_grad():
        dino_l2_all = []
        for i in range(0, n, 25):
            feat_orig = batch_dinov2_features(images[i:i+25])
            feat_noisy = batch_dinov2_features(noisy_images[i:i+25])
            l2 = torch.norm(feat_orig - feat_noisy, p=2, dim=1)
            dino_l2_all.append(l2)
        dino_l2 = torch.cat(dino_l2_all).numpy()
    
    # CLIP cosine similarity (batched)
    clip_sims = []
    for i in range(0, n, BATCH):
        sim = batch_clip_similarity(noisy_images[i:i+BATCH], images[i:i+BATCH])
        clip_sims.append(sim.cpu().numpy())
    clip_sim = np.concatenate(clip_sims)
    
    results[sigma]['dinov2_l2'] = dino_l2
    results[sigma]['clip_sim'] = clip_sim
    
    elapsed = time.time() - t_sigma
    print(f"    DINOv2 L2: {dino_l2.mean():.4f} ± {dino_l2.std():.4f}")
    print(f"    CLIP sim:  {clip_sim.mean():.4f} ± {clip_sim.std():.4f}")
    print(f"    Time: {elapsed:.1f}s")

total_time = time.time() - t_start
print(f"\n  Total time: {total_time:.1f}s ({total_time/60:.1f} min)")

# ── Statistical Analysis ───────────────────────────────────────────────────────
print("\n[5/5] Computing correlations...")
print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

sigma_array = []
dinov2_l2_array = []
clip_sim_array = []

for sigma in sigma_levels:
    sigma_array.extend([sigma] * n)
    dinov2_l2_array.extend(results[sigma]['dinov2_l2'].tolist())
    clip_sim_array.extend(results[sigma]['clip_sim'].tolist())

sigma_array = np.array(sigma_array)
dinov2_l2_array = np.array(dinov2_l2_array)
clip_sim_array = np.array(clip_sim_array)
n_pts = len(sigma_array)

# r(DINOv2_L2, sigma)
r_dino, p_dino = stats.pearsonr(dinov2_l2_array, sigma_array)
ci_width_d = 1.96 * np.sqrt((1 - r_dino**2) / (n_pts - 2))
ci_dino = (r_dino - ci_width_d, r_dino + ci_width_d)

# r(CLIP_sim, sigma)
r_clip, p_clip = stats.pearsonr(clip_sim_array, sigma_array)
ci_width_c = 1.96 * np.sqrt((1 - r_clip**2) / (n_pts - 2))
ci_clip = (r_clip - ci_width_c, r_clip + ci_width_c)

print(f"\nn = {n} images × {len(sigma_levels)} σ levels = {n_pts} observations")

print(f"\n--- r(DINOv2_L2, pixel_noise_σ) ---")
print(f"  Pearson r = {r_dino:.6f}")
print(f"  p-value   = {p_dino:.2e}")
print(f"  95% CI   = [{ci_dino[0]:.4f}, {ci_dino[1]:.4f}]")

print(f"\n--- r(CLIP_sim, pixel_noise_σ) ---")
print(f"  Pearson r = {r_clip:.6f}")
print(f"  p-value   = {p_clip:.2e}")
print(f"  95% CI   = [{ci_clip[0]:.4f}, {ci_clip[1]:.4f}]")

print(f"\n--- Per-σ summary (mean ± std) ---")
print(f"{'σ':>6} | {'DINOv2 L2':>12} | {'CLIP sim':>10}")
print("-" * 35)
for sigma in sigma_levels:
    dl2 = results[sigma]['dinov2_l2']
    cs = results[sigma]['clip_sim']
    print(f"{sigma:>6} | {dl2.mean():>12.4f} ± {dl2.std():.4f} | {cs.mean():>10.4f} ± {cs.std():.4f}")

print("\n--- Interpretation ---")
if r_dino > 0.5:
    print(f"  ✓ DINOv2 L2 is SENSITIVE to pixel noise (r={r_dino:.3f} > 0.5)")
else:
    print(f"  ? DINOv2 L2 sensitivity moderate (r={r_dino:.3f})")

if abs(r_clip) < 0.3:
    print(f"  ✓ CLIP is ROBUST to pixel noise (|r|={abs(r_clip):.3f} < 0.3)")
    print(f"    Semantic features are invariant to pixel-level noise — ")
    print(f"    r=-0.8973 in prior work was NOT from pixel noise per se.")
else:
    print(f"  △ CLIP shows {'increasing' if r_clip > 0 else 'decreasing'} sensitivity to pixel noise (r={r_clip:.3f})")

print(f"\n--- Failure Check (Exp 0) ---")
print(f"  r(DINOv2_L2, σ) = {r_dino:.4f}")
if r_dino < 0.3:
    verdict = "ABANDON_DIRECTION"
    print(f"  FAILURE: r = {r_dino:.4f} < 0.3 → ABANDON_DIRECTION")
else:
    verdict = "PASS"
    print(f"  PASS: DINOv2 L2 is a sensitive proxy for pixel perturbation magnitude.")

print("\n" + "=" * 70)
print(f"EXP 0 COMPLETE — Verdict: {verdict}")
print("=" * 70)
