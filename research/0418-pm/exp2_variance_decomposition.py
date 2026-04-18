#!/usr/bin/env python3
"""
Exp 2: Variance Decomposition
- Dataset: COCO val2017 (n=50, same as exp1)
- Re-use exp1's decoded images and perturbations
- Predictors: DINOv2_L2 + edge_density + pixel_variance
- Target: 1 - CLIP cosine similarity (semantic inconsistency)
- Output: R²_single (DINOv2_L2 only) vs R²_full (all 3)
- BATCHED CLIP for speed.
- CPU budget: < 10 min
"""

import sys, os, time, json
import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

WORK_DIR = '/home/kas/.openclaw/workspace-domain/research/0418-pm'
os.makedirs(WORK_DIR, exist_ok=True)

print("=" * 70)
print("EXP 2: Variance Decomposition (COCO val2017, n=50)")
print("=" * 70)

# ── Load COCO val2017 images (same as exp1) ───────────────────────────────────
print("\n[1/5] Loading COCO val2017 (same 50 images as exp1)...")
from torchvision import transforms
from torchvision.transforms import functional as TF
from PIL import Image

coco_root = os.path.expanduser('~/.cache/huggingface/hub/datasets--merve--coco/snapshots/9e50abcdc1361852f34841af4939cbcd2d37c92f/val2017')
image_files = sorted([f for f in os.listdir(coco_root) if f.endswith('.jpg') or f.endswith('.png')])

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

# ── Compute edge density and pixel variance ──────────────────────────────────
print("\n[2/5] Computing edge density and pixel variance...")
edge_densities = []
pixel_variances = images.var(dim=(1, 2, 3)).numpy()
for i in range(n):
    gray = images[i].mean(dim=0)  # [H, W]
    edges = TF.canny(gray.unsqueeze(0).float())[0]
    edge_densities.append(edges.float().mean().item())
edge_densities = np.array(edge_densities)
print(f"  Edge density: {edge_densities.mean():.4f} ± {edge_densities.std():.4f}")
print(f"  Pixel variance: {pixel_variances.mean():.4f} ± {pixel_variances.std():.4f}")

# ── Load VAE and regenerate perturbations ────────────────────────────────────
print("\n[3/5] Loading VAE and regenerating perturbations...")
from diffusers import AutoencoderKL

vae_name = 'stabilityai/sd-vae-ft-mse'
vae = AutoencoderKL.from_pretrained(vae_name, torch_dtype=torch.float32)
vae.eval()

with torch.no_grad():
    latents_mean = []
    for i in range(0, n, 5):
        latent = vae.encode(images[i:i+5].float()).latent_dist.mean
        latents_mean.append(latent)
    latents_mean = torch.cat(latents_mean, dim=0)

    originals_decoded = []
    for i in range(0, n, 5):
        decoded = vae.decode(latents_mean[i:i+5]).sample
        originals_decoded.append(decoded)
    originals_decoded = torch.cat(originals_decoded, dim=0)
    originals_decoded = torch.clamp(originals_decoded, 0.0, 1.0)

# ── Load DINOv2 and CLIP ───────────────────────────────────────────────────────
from transformers import AutoImageProcessor, AutoModel, CLIPModel, CLIPProcessor

dinov2_name = 'facebook/dinov2-small'
dino_processor = AutoImageProcessor.from_pretrained(dinov2_name, torch_dtype=torch.float32)
dino_model = AutoModel.from_pretrained(dinov2_name, torch_dtype=torch.float32)
dino_model.eval()

clip_name = 'openai/clip-vit-base-patch32'
clip_processor = CLIPProcessor.from_pretrained(clip_name, torch_dtype=torch.float32)
clip_model = CLIPModel.from_pretrained(clip_name, torch_dtype=torch.float32)
clip_model.eval()

def batch_dinov2_features(imgs):
    with torch.no_grad():
        inputs = dino_processor(images=imgs, return_tensors='pt')
        return dino_model(**inputs).last_hidden_state[:, 0]

def batch_clip_features(imgs):
    with torch.no_grad():
        inputs = clip_processor(images=imgs, return_tensors='pt')
        return clip_model.get_image_features(**inputs).pooler_output

def batch_clip_cosine(imgs1, imgs2):
    feat1 = batch_clip_features(imgs1)
    feat2 = batch_clip_features(imgs2)
    feat1 = feat1 / feat1.norm(dim=-1, keepdim=True)
    feat2 = feat2 / feat2.norm(dim=-1, keepdim=True)
    return (feat1 * feat2).sum(dim=-1)

# Pre-compute original DINOv2 features
print("  Computing original DINOv2 features...")
with torch.no_grad():
    dino_feats_original = batch_dinov2_features(originals_decoded)

# ── Collect all observations ─────────────────────────────────────────────────
print("\n[4/5] Collecting observations across perturbation levels...")
sigma_levels = [0.1, 0.2, 0.5, 1.0, 2.0]
BATCH = 25

Y_all = []   # 1 - CLIP_sim
X1_all = []  # DINOv2_L2
X2_all = []  # edge_density
X3_all = []  # pixel_variance

t_start = time.time()

for sigma in sigma_levels:
    print(f"\n  --- σ_latent = {sigma} ---")
    t_sig = time.time()
    
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
        dino_l2 = torch.norm(dino_feats_original - feat_pert, p=2, dim=1).numpy()
    
    # CLIP similarity (batched pairwise)
    clip_sims = []
    for i in range(0, n, BATCH):
        sim = batch_clip_cosine(originals_decoded[i:i+BATCH], perturbed_decoded[i:i+BATCH])
        clip_sims.append(sim.cpu().numpy())
    clip_sim = np.concatenate(clip_sims)
    Y_batch = 1 - clip_sim
    
    Y_all.extend(Y_batch.tolist())
    X1_all.extend(dino_l2.tolist())
    X2_all.extend(edge_densities.tolist())
    X3_all.extend(pixel_variances.tolist())
    
    elapsed = time.time() - t_sig
    print(f"    DINOv2 L2: {dino_l2.mean():.4f}, 1-CLIP: {Y_batch.mean():.4f}, Time: {elapsed:.1f}s")

total_time = time.time() - t_start
print(f"\n  Total time: {total_time:.1f}s")

Y_all = np.array(Y_all)
X1_all = np.array(X1_all)
X2_all = np.array(X2_all)
X3_all = np.array(X3_all)
n_obs = len(Y_all)

# ── Regression Analysis ────────────────────────────────────────────────────────
print("\n[5/5] Regression analysis...")
print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

X_single = X1_all.reshape(-1, 1)
X_full = np.column_stack([X1_all, X2_all, X3_all])

# R²_single
reg_single = LinearRegression()
reg_single.fit(X_single, Y_all)
Y_pred_single = reg_single.predict(X_single)
R2_single = r2_score(Y_all, Y_pred_single)

# R²_full
reg_full = LinearRegression()
reg_full.fit(X_full, Y_all)
Y_pred_full = reg_full.predict(X_full)
R2_full = r2_score(Y_all, Y_pred_full)

# Bootstrap CI
print("  Computing bootstrap CI (1000 iterations)...")
np.random.seed(42)
n_boot = 1000
R2_single_boot = np.array([
    r2_score(Y_all[np.random.choice(n_obs, n_obs, replace=True)],
             LinearRegression().fit(X_single[np.random.choice(n_obs, n_obs, replace=True)],
                                     Y_all[np.random.choice(n_obs, n_obs, replace=True)]).predict(
                 X_single[np.random.choice(n_obs, n_obs, replace=True)]))
    for _ in range(n_boot)
])
R2_full_boot = np.array([
    r2_score(Y_all[np.random.choice(n_obs, n_obs, replace=True)],
             LinearRegression().fit(X_full[np.random.choice(n_obs, n_obs, replace=True)],
                                     Y_all[np.random.choice(n_obs, n_obs, replace=True)]).predict(
                 X_full[np.random.choice(n_obs, n_obs, replace=True)]))
    for _ in range(n_boot)
])
R2_single_ci = (np.percentile(R2_single_boot, 2.5), np.percentile(R2_single_boot, 97.5))
R2_full_ci = (np.percentile(R2_full_boot, 2.5), np.percentile(R2_full_boot, 97.5))

# F-test
RSS_full = np.sum((Y_all - Y_pred_full)**2)
RSS_single = np.sum((Y_all - Y_pred_single)**2)
k_full, k_single = 3, 1
MSE_full = RSS_full / (n_obs - k_full - 1)
F_stat = ((RSS_single - RSS_full) / (k_full - k_single)) / MSE_full
p_F = 1 - stats.f.cdf(F_stat, k_full - k_single, n_obs - k_full - 1)

# t-tests on coefficients
X_i = np.column_stack([np.ones(n_obs), X_full])
coeffs = np.linalg.lstsq(X_i, Y_all, rcond=None)[0]
residuals = Y_all - X_i @ coeffs
s2 = np.sum(residuals**2) / (n_obs - k_full - 1)
var_covar = s2 * np.linalg.inv(X_i.T @ X_i)
se = np.sqrt(np.diag(var_covar))
t_vals = coeffs / se
p_vals = 2 * (1 - stats.t.cdf(np.abs(t_vals), n_obs - k_full - 1))

print(f"\nn = {n} images × {len(sigma_levels)} σ levels = {n_obs} observations")
print(f"Target Y: 1 - CLIP cosine similarity (semantic inconsistency)")

print(f"\n--- R²_single: Y ~ DINOv2_L2 ---")
print(f"  R²         = {R2_single:.4f}")
print(f"  95% CI     = [{R2_single_ci[0]:.4f}, {R2_single_ci[1]:.4f}] (bootstrap)")
print(f"  Coef (β1)  = {reg_single.coef_[0]:.6f}")
print(f"  Intercept  = {reg_single.intercept_:.6f}")

print(f"\n--- R²_full: Y ~ DINOv2_L2 + edge_density + pixel_variance ---")
print(f"  R²         = {R2_full:.4f}")
print(f"  95% CI     = [{R2_full_ci[0]:.4f}, {R2_full_ci[1]:.4f}] (bootstrap)")
print(f"  ΔR²        = {R2_full - R2_single:.4f}")

print(f"\n--- Full model coefficients ---")
print(f"  {'Predictor':>15} | {'Coef':>10} | {'SE':>10} | {'t':>8} | {'p':>10}")
print(f"  {'-'*60}")
pred_names = ['Intercept', 'DINOv2_L2', 'edge_density', 'pixel_variance']
for name, c, s, t, p in zip(pred_names, coeffs, se, t_vals, p_vals):
    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
    print(f"  {name:>15} | {c:>10.6f} | {s:>10.6f} | {t:>8.3f} | {p:>9.2e} {sig}")

print(f"\n--- F-test: edge_density + pixel_variance add explanatory power? ---")
print(f"  F({k_full - k_single}, {n_obs - k_full - 1}) = {F_stat:.4f}")
print(f"  p-value = {p_F:.4e}")
if p_F < 0.05:
    print(f"  ✓ Significant: edge_density + pixel_variance ADD explanatory power")
else:
    print(f"  ✗ Not significant: edge_density + pixel_variance do NOT add explanatory power")

print(f"\n--- Summary ---")
print(f"  R²_single (DINOv2 L2 only) = {R2_single:.4f}")
print(f"  R²_full (all 3 predictors) = {R2_full:.4f}")
print(f"  Unexplained variance = {1 - R2_full:.4f}")

print(f"\n--- Failure Check (Exp 2) ---")
FAILURE_THRESHOLD = 0.4
if R2_full < FAILURE_THRESHOLD:
    verdict = "LOW_EXPLAINED_VARIANCE"
    print(f"  *** FAILURE: R²_full = {R2_full:.4f} < {FAILURE_THRESHOLD} ***")
    print(f"  → LOW_EXPLAINED_VARIANCE")
    print(f"  Most variance is unexplained even with all measurable confounders.")
else:
    verdict = "EXPLAINED_VARIANCE_OK"
    print(f"  ✓ PASS: R²_full = {R2_full:.4f} >= {FAILURE_THRESHOLD}")
    print(f"  → EXPLAINED_VARIANCE_OK")

print("\n" + "=" * 70)
print(f"EXP 2 COMPLETE — Verdict: {verdict}")
print("=" * 70)

results = {
    'verdict': verdict,
    'R2_single': float(R2_single),
    'R2_full': float(R2_full),
    'R2_single_ci': [float(R2_single_ci[0]), float(R2_single_ci[1])],
    'R2_full_ci': [float(R2_full_ci[0]), float(R2_full_ci[1])],
    'delta_R2': float(R2_full - R2_single),
    'F_stat': float(F_stat),
    'p_F': float(p_F),
    'coeffs': {n: float(c) for n, c in zip(pred_names, coeffs)},
    'p_values': {n: float(p) for n, p in zip(pred_names, p_vals)},
    'n_images': n,
    'n_obs': int(n_obs),
    'total_time_s': float(total_time),
}

import json
with open(os.path.join(WORK_DIR, 'exp2_results.json'), 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {WORK_DIR}/exp2_results.json")
