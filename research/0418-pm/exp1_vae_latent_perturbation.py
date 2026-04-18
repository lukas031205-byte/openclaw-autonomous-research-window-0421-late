#!/usr/bin/env python3
"""
Exp 1: VAE Latent Perturbation - Core Validation
- Dataset: COCO val2017 (n=50, already cached)
- Model: stabilityai/sd-vae-ft-mse (already cached)
- Perturbation: Gaussian noise on VAE latent space
- σ_latent ∈ {0.1, 0.2, 0.5, 1.0, 2.0}
- Primary metric: r(DINOv2_L2, 1 - CLIP_sim)
- BATCHED CLIP processing for speed.
- CPU budget: < 25 min
"""

import sys, os, time, json
import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

WORK_DIR = '/home/kas/.openclaw/workspace-domain/research/0418-pm'
os.makedirs(WORK_DIR, exist_ok=True)

print("=" * 70)
print("EXP 1: VAE Latent Perturbation (COCO val2017)")
print("=" * 70)

# ── Load COCO val2017 images ──────────────────────────────────────────────────
print("\n[1/6] Loading COCO val2017 (cached)...")
from torchvision import transforms
from PIL import Image

coco_root = os.path.expanduser('~/.cache/huggingface/hub/datasets--merve--coco/snapshots/9e50abcdc1361852f34841af4939cbcd2d37c92f/val2017')
image_files = sorted([f for f in os.listdir(coco_root) if f.endswith('.jpg') or f.endswith('.png')])
print(f"  Total COCO val images: {len(image_files)}")

np.random.seed(42)
n = 50
selected_files = np.random.choice(image_files, size=n, replace=False).tolist()

def load_and_preprocess(path):
    img = Image.open(path).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((512, 512)),
        transforms.ToTensor(),
    ])
    return transform(img)

images = torch.stack([load_and_preprocess(os.path.join(coco_root, f)) for f in selected_files])
print(f"  Loaded {len(images)} images, shape={images.shape}")

# ── Load VAE ─────────────────────────────────────────────────────────────────
print("\n[2/6] Loading SD-VAE-FT-MSE (CPU)...")
from diffusers import AutoencoderKL

vae_name = 'stabilityai/sd-vae-ft-mse'
vae = AutoencoderKL.from_pretrained(vae_name, torch_dtype=torch.float32)
vae.eval()
# spatial compression ratio varies by model; just show what we have
latent_ch = vae.config.get('in_channels', '?')
print(f"  VAE config: latent_ch={latent_ch}")

# Encode all images to latent space
print("\n[3/6] Encoding images to VAE latent space...")
with torch.no_grad():
    latents_mean = []
    for i in range(0, n, 5):
        batch = images[i:i+5].float()
        latent = vae.encode(batch).latent_dist.mean
        latents_mean.append(latent)
    latents_mean = torch.cat(latents_mean, dim=0)

print(f"  Latent shape per image: {latents_mean.shape[1:]}")
print(f"  Latent stats: mean={latents_mean.mean():.4f}, std={latents_mean.std():.4f}")

# Decode originals (no perturbation)
print("  Decoding original latents...")
with torch.no_grad():
    originals_decoded = []
    for i in range(0, n, 5):
        decoded = vae.decode(latents_mean[i:i+5]).sample
        originals_decoded.append(decoded)
    originals_decoded = torch.cat(originals_decoded, dim=0)
    originals_decoded = torch.clamp(originals_decoded, 0.0, 1.0)
print(f"  Original decoded shape: {originals_decoded.shape}")

# ── Load DINOv2 ───────────────────────────────────────────────────────────────
print("\n[4/6] Loading DINOv2-small...")
from transformers import AutoImageProcessor, AutoModel

dinov2_name = 'facebook/dinov2-small'
dino_processor = AutoImageProcessor.from_pretrained(dinov2_name, torch_dtype=torch.float32)
dino_model = AutoModel.from_pretrained(dinov2_name, torch_dtype=torch.float32)
dino_model.eval()

def batch_dinov2_features(imgs):
    """[B,C,H,W] -> [B, 384] CLS features"""
    with torch.no_grad():
        inputs = dino_processor(images=imgs, return_tensors='pt')
        outputs = dino_model(**inputs)
        return outputs.last_hidden_state[:, 0]

# Pre-compute original DINOv2 features
print("  Computing original DINOv2 features (batched)...")
with torch.no_grad():
    dino_feats_original = batch_dinov2_features(originals_decoded)
print(f"  Original DINOv2 features: {dino_feats_original.shape}")

# ── Load CLIP ─────────────────────────────────────────────────────────────────
print("\n[5/6] Loading CLIP (batched)...")
from transformers import CLIPModel, CLIPProcessor

clip_name = 'openai/clip-vit-base-patch32'
clip_processor = CLIPProcessor.from_pretrained(clip_name, torch_dtype=torch.float32)
clip_model = CLIPModel.from_pretrained(clip_name, torch_dtype=torch.float32)
clip_model.eval()

def batch_clip_features(imgs):
    """[B,C,H,W] -> [B, 512]"""
    with torch.no_grad():
        inputs = clip_processor(images=imgs, return_tensors='pt')
        return clip_model.get_image_features(**inputs).pooler_output

def batch_clip_cosine(imgs1, imgs2):
    """Pairwise cosine similarity for two batches [B,C,H,W] -> [B]"""
    feat1 = batch_clip_features(imgs1)
    feat2 = batch_clip_features(imgs2)
    feat1 = feat1 / feat1.norm(dim=-1, keepdim=True)
    feat2 = feat2 / feat2.norm(dim=-1, keepdim=True)
    return (feat1 * feat2).sum(dim=-1)  # [B]

# ── Main perturbation loop ────────────────────────────────────────────────────
print("\n[6/6] Running VAE latent perturbation experiment...")
sigma_levels = [0.1, 0.2, 0.5, 1.0, 2.0]
BATCH = 25

# Storage
all_dino_l2 = []
all_clip_sim = []
all_sigma = []

t_start = time.time()

for sigma in sigma_levels:
    print(f"\n  --- σ_latent = {sigma} ---")
    t_sig = time.time()
    
    # Generate and decode perturbed latents
    with torch.no_grad():
        noise = torch.randn_like(latents_mean) * sigma
        perturbed_latents = latents_mean + noise
        perturbed_decoded = []
        for i in range(0, n, 5):
            dec = vae.decode(perturbed_latents[i:i+5]).sample
            perturbed_decoded.append(dec)
        perturbed_decoded = torch.cat(perturbed_decoded, dim=0)
        perturbed_decoded = torch.clamp(perturbed_decoded, 0.0, 1.0)
    
    # DINOv2 L2 (batched)
    with torch.no_grad():
        feat_pert = batch_dinov2_features(perturbed_decoded)
        l2 = torch.norm(dino_feats_original - feat_pert, p=2, dim=1).numpy()
    
    # CLIP similarity (batched pairwise)
    clip_sims = []
    for i in range(0, n, BATCH):
        sim = batch_clip_cosine(originals_decoded[i:i+BATCH], perturbed_decoded[i:i+BATCH])
        clip_sims.append(sim.cpu().numpy())
    clip_sim = np.concatenate(clip_sims)
    
    all_dino_l2.extend(l2.tolist())
    all_clip_sim.extend(clip_sim.tolist())
    all_sigma.extend([sigma] * n)
    
    elapsed = time.time() - t_sig
    print(f"    DINOv2 L2:  {l2.mean():.4f} ± {l2.std():.4f}")
    print(f"    CLIP sim:   {clip_sim.mean():.4f} ± {clip_sim.std():.4f}")
    print(f"    1-CLIP sim: {(1-clip_sim).mean():.4f}")
    print(f"    Time: {elapsed:.1f}s")

total_time = time.time() - t_start
print(f"\n  Total experiment time: {total_time:.1f}s ({total_time/60:.1f} min)")

# ── Statistical Analysis ──────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

all_dino_l2 = np.array(all_dino_l2)
all_clip_sim = np.array(all_clip_sim)
all_sigma = np.array(all_sigma)
all_1_minus_clip = 1 - all_clip_sim
n_pts = len(all_dino_l2)

# Primary: r(DINOv2_L2, 1 - CLIP_sim)
r_primary, p_primary = stats.pearsonr(all_dino_l2, all_1_minus_clip)
ci_width_p = 1.96 * np.sqrt((1 - r_primary**2) / (n_pts - 2))
ci_primary = (r_primary - ci_width_p, r_primary + ci_width_p)

# Secondary: r(DINOv2_L2, sigma)
r_dino_sigma, p_dino_sigma = stats.pearsonr(all_dino_l2, all_sigma)

# Secondary: r(1-CLIP_sim, sigma)
r_semantic_sigma, p_semantic_sigma = stats.pearsonr(all_1_minus_clip, all_sigma)

print(f"\nn = {n} images × {len(sigma_levels)} σ levels = {n_pts} observations")
print(f"VAE: {vae_name}")
print(f"DINOv2: {dinov2_name}")
print(f"CLIP: {clip_name}")

print(f"\n--- PRIMARY: r(DINOv2_L2, 1 - CLIP_sim) ---")
print(f"  Pearson r = {r_primary:.6f}")
print(f"  p-value    = {p_primary:.2e}")
print(f"  95% CI     = [{ci_primary[0]:.4f}, {ci_primary[1]:.4f}]")
print(f"  r²         = {r_primary**2:.4f}")

print(f"\n--- SECONDARY: r(DINOv2_L2, σ_latent) ---")
print(f"  Pearson r = {r_dino_sigma:.6f}, p = {p_dino_sigma:.2e}")

print(f"\n--- SECONDARY: r(1 - CLIP_sim, σ_latent) ---")
print(f"  Pearson r = {r_semantic_sigma:.6f}, p = {p_semantic_sigma:.2e}")

print(f"\n--- Per-σ summary ---")
print(f"{'σ_latent':>10} | {'DINOv2 L2':>10} | {'CLIP sim':>10} | {'1-CLIP':>10}")
print("-" * 50)
for sigma in sigma_levels:
    mask = all_sigma == sigma
    dl2 = all_dino_l2[mask]
    cs = all_clip_sim[mask]
    print(f"{sigma:>10.1f} | {dl2.mean():>10.4f} | {cs.mean():>10.4f} | {(1-cs).mean():>10.4f}")

print("\n--- Failure Check (Exp 1) ---")
print(f"  r(DINOv2_L2, 1-CLIP_sim) = {r_primary:.4f}")
FAILURE_THRESHOLD = 0.3
if r_primary < FAILURE_THRESHOLD:
    verdict = "ABANDON_DIRECTION"
    print(f"  *** FAILURE: r = {r_primary:.4f} < {FAILURE_THRESHOLD} ***")
    print(f"  → ABANDON_DIRECTION")
    print(f"  VAE-induced semantic drift is NOT predictable by DINOv2 L2.")
else:
    if r_primary >= 0.5 and p_primary < 0.01:
        verdict = "CONFIRMED"
        print(f"  ✓ PASS: r = {r_primary:.4f} >= 0.5, p < 0.01")
        print(f"  → CONFIRMED: DINOv2 L2 predicts VAE-induced semantic drift.")
    else:
        verdict = "PARTIAL_CONFIRM"
        print(f"  △ PARTIAL: r = {r_primary:.4f} in [0.3, 0.5)")
        print(f"  → PARTIAL_CONFIRM: Use as hypothesis generation tool.")

print("\n" + "=" * 70)
print(f"EXP 1 COMPLETE — Verdict: {verdict}")
print("=" * 70)

results = {
    'verdict': verdict,
    'r_primary': float(r_primary),
    'p_primary': float(p_primary),
    'ci_primary': [float(ci_primary[0]), float(ci_primary[1])],
    'r_sq': float(r_primary**2),
    'r_dino_sigma': float(r_dino_sigma),
    'r_semantic_sigma': float(r_semantic_sigma),
    'n_images': n,
    'n_sigmas': len(sigma_levels),
    'total_time_s': float(total_time),
}

import json
with open(os.path.join(WORK_DIR, 'exp1_results.json'), 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {WORK_DIR}/exp1_results.json")
