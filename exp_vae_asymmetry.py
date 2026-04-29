#!/usr/bin/env python3
"""
exp_vae_asymmetry.py — VAE CIFAR-10 Semantic Asymmetry Experiment
================================================================
Measures whether VAE encode→decode destroys semantic attributes more on
"complex" (animals) vs "simple" (planes, cars) CIFAR-10 images.

CPU-only, <2GB RAM, <15 min expected runtime.

pip install: torch torchvision dinov2 open_clip_torch torchmetrics pillow

Hypothesis: ΔDINO_L2 and ΔCLIP should be larger for semantically complex images.
"""

import torch
import torchvision
import torchvision.transforms as T
import open_clip
from dinov2.eval.utils import model_utils as dinov2_utils
import numpy as np
from PIL import Image
import time
import os
import gc

# ── Config ────────────────────────────────────────────────────────────────────
DEVICE = "cpu"
BATCH_SIZE = 32          # keep small for RAM
N_SAMPLES = 500          # total (250 simple + 250 complex), adjust if OOM
SEED = 42
SIMPLE_CLASSES = [0, 1]   # airplane, automobile
COMPLEX_CLASSES = [3, 4, 5, 6, 7]  # cat, deer, dog, frog, horse

torch.manual_seed(SEED)
np.random.seed(SEED)

print("=" * 60)
print("exp_vae_asymmetry.py — VAE CIFAR-10 Semantic Asymmetry")
print("=" * 60)

# ── 1. Load CIFAR-10 ──────────────────────────────────────────────────────────
print("\n[1] Loading CIFAR-10 train set...")
transform = T.Compose([
    T.Resize((224, 224)),      # DINOv2/CLIP expect 224
    T.ToTensor(),
])
dataset = torchvision.datasets.CIFAR10(
    root="./data", train=True, download=True, transform=transform
)

# Stratified sample
simple_idx = [i for i, (_, label) in enumerate(dataset) if label in SIMPLE_CLASSES]
complex_idx = [i for i, (_, label) in enumerate(dataset) if label in COMPLEX_CLASSES]
np.random.shuffle(simple_idx)
np.random.shuffle(complex_idx)
n_per = N_SAMPLES // 2
indices = simple_idx[:n_per] + complex_idx[:n_per]
np.random.shuffle(indices)

print(f"  Samples: {len(indices)} total ({n_per} simple, {n_per} complex)")

# ── 2. Load Models ────────────────────────────────────────────────────────────
print("\n[2] Loading models (CPU)...")

# 2a. VAE — use cached stabilityai/sd-vae-ft-mse
from diffusers.models import AutoencoderKL
print("  Loading SD-VAE (ft-mse)...")
vae = AutoencoderKL.from_pretrained(
    "stabilityai/sd-vae-ft-mse",
    cache_dir=os.path.expanduser("~/.cache/huggingface/hub/"),
    torch_dtype=torch.float32,
)
vae = vae.to(DEVICE)
vae.eval()
print("  VAE loaded OK")

# 2b. DINOv2 — use ViT-B/14 (smallest variant)
print("  Loading DINOv2 ViT-B/14...")
dinov2_model = torch.hub.load("facebookresearch/dinov2", "dinov2_vitb14")
dinov2_model = dinov2_model.to(DEVICE)
dinov2_model.eval()
print("  DINOv2 loaded OK")

# 2c. CLIP — use open_clip ViT-B/14
print("  Loading Open CLIP ViT-B/14...")
clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
    "ViT-B/14", pretrained="openai"
)
clip_model = clip_model.to(DEVICE)
clip_model.eval()
print("  CLIP loaded OK")

print("\n  Memory after model load:")
import psutil
mem = psutil.virtual_memory()
print(f"  Used: {mem.used/1024**3:.1f}GB | Free: {mem.free/1024**3:.1f}GB | Avail: {mem.available/1024**3:.1f}GB")

# ── 3. Helper Functions ───────────────────────────────────────────────────────
def get_dino_features(img_tensor):
    """Extract DINOv2 features (register tokens if available)."""
    with torch.no_grad():
        x = img_tensor.unsqueeze(0).to(DEVICE)
        # DINOv2 with registers has a specific forward
        try:
            feat = dinov2_model.forward_features(x)
            # Use cls token or mean
            if 'x_norm_clstoken' in feat:
                return feat['x_norm_clstoken'].squeeze()
            elif 'x_norm_patchtokens' in feat:
                return feat['x_norm_patchtokens'].mean(1)
            else:
                return feat['x_norm_token']
        except Exception:
            # fallback: use intermediate feature
            return None

def get_clip_features(img_tensor):
    """Extract CLIP image features."""
    with torch.no_grad():
        x = clip_preprocess(img_tensor).unsqueeze(0).to(DEVICE)
        return clip_model.encode_image(x).squeeze()

def encode_decode(img_tensor):
    """Encode to VAE latent, decode back to pixel space."""
    with torch.no_grad():
        x = img_tensor.unsqueeze(0).to(DEVICE).float()
        # VAE expects input in [-1, 1] approximately
        latent = vae.encode(x).latent_dist.sample()
        recon = vae.decode(latent).sample
        return recon.squeeze().cpu()

# ── 4. Main Evaluation Loop ──────────────────────────────────────────────────
print(f"\n[3] Processing {len(indices)} images in batches of {BATCH_SIZE}...")

results = {"simple": [], "complex": []}
start_time = time.time()

for batch_start in range(0, len(indices), BATCH_SIZE):
    batch_idx = indices[batch_start:batch_start + BATCH_SIZE]
    batch_imgs = [dataset[i][0] for i in batch_idx]
    batch_labels = [dataset[i][1] for i in batch_idx]

    # Collect originals
    orig_tensors = torch.stack(batch_imgs)  # [B, 3, 224, 224]
    is_simple = [l in SIMPLE_CLASSES for l in batch_labels]

    # Encode-decode
    recon_tensors = []
    for img in batch_imgs:
        recon = encode_decode(img)
        recon_tensors.append(recon)
    recon_tensors = torch.stack(recon_tensors)

    # Compute features
    dino_orig_list, dino_recon_list = [], []
    clip_orig_list, clip_recon_list = [], []

    for i in range(len(batch_imgs)):
        o = orig_tensors[i]
        r = recon_tensors[i]

        # DINOv2 features — resize back to 224 if needed
        d_o = get_dino_features(o)
        d_r = get_dino_features(r)
        if d_o is not None and d_r is not None:
            dino_orig_list.append(d_o.float())
            dino_recon_list.append(d_r.float())

        # CLIP features
        # Need to convert back to PIL for clip_preprocess
        def tens_to_pil(t):
            t = t.cpu().clamp(0, 1)
            arr = (t.permute(1, 2, 0).numpy() * 255).astype(np.uint8)
            return Image.fromarray(arr)

        c_o = get_clip_features(tens_to_pil(o))
        c_r = get_clip_features(tens_to_pil(r))
        clip_orig_list.append(c_o.float())
        clip_recon_list.append(c_r.float())

    # Compute metrics per image
    for i, (is_s, label) in enumerate(zip(is_simple, batch_labels)):
        key = "simple" if is_s else "complex"
        dino_l2 = torch.nn.functional.pairwise_distance(
            dino_orig_list[i].unsqueeze(0), dino_recon_list[i].unsqueeze(0)
        ).item()
        clip_cos = torch.nn.functional.cosine_similarity(
            clip_orig_list[i].unsqueeze(0), clip_recon_list[i].unsqueeze(0)
        ).item()
        results[key].append((dino_l2, 1 - clip_cos))  # store ΔCLIP as drop

    # Progress
    done = min(batch_start + BATCH_SIZE, len(indices))
    elapsed = time.time() - start_time
    rate = done / elapsed if elapsed > 0 else 0
    eta = (len(indices) - done) / rate if rate > 0 else 0
    print(f"  [{done}/{len(indices)}] elapsed={elapsed:.0f}s eta={eta:.0f}s", flush=True)

    # Memory check
    gc.collect()
    mem = psutil.virtual_memory()
    if mem.available / 1024**3 < 0.8:
        print(f"  WARNING: Low memory! available={mem.available/1024**3:.1f}GB, stopping early")
        break

# ── 5. Report Results ─────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

for key in ["simple", "complex"]:
    if results[key]:
        dino_l2s = [r[0] for r in results[key]]
        clip_drops = [r[1] for r in results[key]]
        print(f"\n{key.upper()} (n={len(results[key])}):")
        print(f"  ΔDINO_L2 : mean={np.mean(dino_l2s):.4f} std={np.std(dino_l2s):.4f} "
              f"min={np.min(dino_l2s):.4f} max={np.max(dino_l2s):.4f}")
        print(f"  ΔCLIP_drop: mean={np.mean(clip_drops):.4f} std={np.std(clip_drops):.4f} "
              f"min={np.min(clip_drops):.4f} max={np.max(clip_drops):.4f}")

# Summary comparison
if results["simple"] and results["complex"]:
    s_dino = np.mean([r[0] for r in results["simple"]])
    c_dino = np.mean([r[0] for r in results["complex"]])
    s_clip = np.mean([r[1] for r in results["simple"]])
    c_clip = np.mean([r[1] for r in results["complex"]])
    print(f"\nSUMMARY:")
    print(f"  ΔDINO_L2: complex - simple = {c_dino - s_dino:+.4f} "
          f"({'LARGER for complex (supports hypothesis)' if c_dino > s_dino else 'NOT larger'})")
    print(f"  ΔCLIP_drop: complex - simple = {c_clip - s_clip:+.4f} "
          f"({'LARGER for complex (supports hypothesis)' if c_clip > s_clip else 'NOT larger'})")

total_time = time.time() - start_time
print(f"\nTotal runtime: {total_time:.0f}s ({total_time/60:.1f} min)")
print(f"Final memory: used={mem.used/1024**3:.1f}GB free={mem.free/1024**3:.1f}GB avail={mem.available/1024**3:.1f}GB")
