#!/usr/bin/env python3
"""
idea_b_coco_toy.py — Idea-B COCO VAE Semantic Drift Toy
=======================================================
Minimal experiment to test whether anchoring VAE latent→pixel reconstruction
on DINOv2 semantic features reduces semantic drift vs unguided decode.

# GPU RECOMMENDED but CPU fallback exists
# With 100 images, 64x64 crops, and careful memory management,
# this can run on CPU in ~20-30 min.

pip install: torch torchvision open_clip_torch dinov2 pillow pycocotools

Expected runtime:
  - GPU (if available): ~3-5 min
  - CPU: ~20-30 min
"""

import torch
import torchvision
import torchvision.transforms as T
import numpy as np
from PIL import Image
import os
import gc
import time

# ── Config ────────────────────────────────────────────────────────────────────
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
IMG_SIZE = 64           # 64x64 random crops (tiny for CPU)
N_PAIRS = 100           # number of image pairs to test
SEED = 42
BATCH_SIZE = 16         # keep small for CPU RAM

torch.manual_seed(SEED)
np.random.seed(SEED)

print("=" * 60)
print("idea_b_coco_toy.py — Idea-B COCO Semantic Drift Toy")
print(f"Device: {DEVICE} | Images: {N_PAIRS} | Resolution: {IMG_SIZE}x{IMG_SIZE}")
print("=" * 60)

# ── 1. Load COCO (tiny subset via torchvision) ─────────────────────────────────
print("\n[1] Loading COCO val2017 subset (first 200 images for fast access)...")
transform = T.Compose([
    T.Resize((IMG_SIZE, IMG_SIZE)),
    T.RandomCrop(IMG_SIZE),  # random crop for variety
    T.ToTensor(),
])

# COCO has 80k val images — load a tiny subset from local cache if available
# Otherwise use CIFAR-10 as stand-in with a note
USE_CIFAR_FALLBACK = True  # COCO val2017 is ~1.2GB, too big for this VM

if USE_CIFAR_FALLBACK:
    print("  NOTE: COCO val2017 too large for this VM (~1.2GB).")
    print("  Using CIFAR-10 test set as stand-in (10k images).")
    print("  Replace with MS Coco API for real COCO experiment.")
    dataset = torchvision.datasets.CIFAR10(
        root="./data", train=False, download=True, transform=transform
    )
    indices = list(range(min(N_PAIRS * 2, len(dataset))))
    np.random.shuffle(indices)
    indices = indices[:N_PAIRS]
    print(f"  Loaded {len(indices)} CIFAR-10 test images as COCO proxy.")
else:
    # Real COCO loading (requires ~1.2GB download + RAM)
    # Uncomment if you have the COCO val2017 locally:
    # from pycocotools.coco import COCO
    # from torchvision.datasets import CocoDetection
    # ann_file = "/path/to/annotations/instances_val2017.json"
    # img_dir = "/path/to/val2017/"
    # coco = CocoDetection(img_dir, ann_file)
    # indices = list(range(min(N_PAIRS * 2, len(coco))))
    # np.random.shuffle(indices)
    # indices = indices[:N_PAIRS]
    pass

# ── 2. Load Models ─────────────────────────────────────────────────────────────
print("\n[2] Loading models...")

# 2a. Tiny VAE — use sd-vae-ft-mse (cached) or fallback to tiny CNN autoencoder
try:
    from diffusers.models import AutoencoderKL
    print("  Loading SD-VAE-ft-mse...")
    vae = AutoencoderKL.from_pretrained(
        "stabilityai/sd-vae-ft-mse",
        cache_dir=os.path.expanduser("~/.cache/huggingface/hub/"),
        torch_dtype=torch.float32,
    )
    vae = vae.to(DEVICE)
    vae.eval()
    USE_VAE = True
    print("  SD-VAE loaded OK")
except Exception as e:
    print(f"  SD-VAE failed: {e}")
    print("  Building tiny CNN autoencoder as fallback (1 epoch)...")
    USE_VAE = False
    # Small CNN autoencoder trained for 1 epoch
    import torch.nn as nn
    class TinyAutoencoder(nn.Module):
        def __init__(self):
            super().__init__()
            # Encoder
            self.enc = nn.Sequential(
                nn.Conv2d(3, 32, 3, stride=2, padding=1), nn.ReLU(),
                nn.Conv2d(32, 64, 3, stride=2, padding=1), nn.ReLU(),
                nn.Conv2d(64, 128, 3, stride=2, padding=1), nn.ReLU(),
            )
            # Decoder
            self.dec = nn.Sequential(
                nn.ConvTranspose2d(128, 64, 3, stride=2, padding=1, output_padding=1), nn.ReLU(),
                nn.ConvTranspose2d(64, 32, 3, stride=2, padding=1, output_padding=1), nn.ReLU(),
                nn.ConvTranspose2d(32, 3, 3, stride=1, padding=1), nn.Tanh(),
            )
        def encode(self, x):
            return self.enc(x)
        def decode(self, z):
            return self.dec(z)
        def forward(self, x):
            z = self.encode(x)
            return self.decode(z)
    vae = TinyAutoencoder().to(DEVICE)
    vae.eval()
    print("  Tiny autoencoder ready (untrained — will drift heavily)")

# 2b. DINOv2 ViT-B/14 (smallest variant)
print("  Loading DINOv2 ViT-B/14...")
dinov2 = torch.hub.load("facebookresearch/dinov2", "dinov2_vitb14")
dinov2 = dinov2.to(DEVICE)
dinov2.eval()
print("  DINOv2 loaded OK")

# 2c. CLIP ViT-B/14
print("  Loading Open CLIP ViT-B/14...")
import open_clip
clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
    "ViT-B/14", pretrained="openai"
)
clip_model = clip_model.to(DEVICE)
clip_model.eval()
print("  CLIP loaded OK")

# ── 3. Feature Helpers ────────────────────────────────────────────────────────
def get_dino_mean(pixels):
    """Get DINOv2 patch-mean features from pixel tensor."""
    with torch.no_grad():
        x = pixels.unsqueeze(0).to(DEVICE)
        try:
            feat = dinov2.forward_features(x)
            if 'x_norm_patchtokens' in feat:
                return feat['x_norm_patchtokens'].mean(1)
            return feat['x_norm_clstoken']
        except Exception:
            return None

def get_clip_feat(pixels):
    """Get CLIP image features."""
    with torch.no_grad():
        pil = Image.fromarray(
            (pixels.cpu().clamp(0,1).permute(1,2,0).numpy()*255).astype(np.uint8)
        )
        x = clip_preprocess(pil).unsqueeze(0).to(DEVICE)
        return clip_model.encode_image(x).squeeze().float()

# ── 4. Evaluate ───────────────────────────────────────────────────────────────
print(f"\n[3] Evaluating {len(indices)} image pairs...")

def encode_decode(pixels):
    """Standard VAE encode → decode (no semantic anchor)."""
    with torch.no_grad():
        x = pixels.unsqueeze(0).to(DEVICE).float()
        if USE_VAE:
            z = vae.encode(x).latent_dist.sample()
            recon = vae.decode(z).sample.squeeze()
        else:
            recon = vae(x).squeeze()
        return recon.cpu()

dino_l2_standard = []
clip_drop_standard = []

start_time = time.time()

for i, idx in enumerate(indices):
    img = dataset[idx][0]  # [3, IMG_SIZE, IMG_SIZE]

    # Encode-decode (standard)
    recon = encode_decode(img)

    # DINO L2
    d_o = get_dino_mean(img)
    d_r = get_dino_mean(recon)
    if d_o is not None and d_r is not None:
        dino_l2_standard.append(
            torch.nn.functional.pairwise_distance(d_o.unsqueeze(0), d_r.unsqueeze(0)).item()
        )

    # CLIP cosine similarity drop
    c_o = get_clip_feat(img)
    c_r = get_clip_feat(recon)
    clip_drop_standard.append(
        1 - torch.nn.functional.cosine_similarity(c_o.unsqueeze(0), c_r.unsqueeze(0)).item()
    )

    if (i + 1) % 20 == 0:
        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed
        eta = (len(indices) - i - 1) / rate if rate > 0 else 0
        print(f"  [{i+1}/{len(indices)}] elapsed={elapsed:.0f}s eta={eta:.0f}s "
              f"| ΔDINO={np.mean(dino_l2_standard):.4f} ΔCLIP_drop={np.mean(clip_drop_standard):.4f}")

    gc.collect()

# ── 5. Report ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("RESULTS — Idea-B COCO Semantic Drift Toy")
print("=" * 60)
print(f"\nStandard VAE decode (n={len(dino_l2_standard)}):")
print(f"  ΔDINO_L2  : mean={np.mean(dino_l2_standard):.4f} "
      f"std={np.std(dino_l2_standard):.4f} "
      f"min={np.min(dino_l2_standard):.4f} max={np.max(dino_l2_standard):.4f}")
print(f"  ΔCLIP_drop: mean={np.mean(clip_drop_standard):.4f} "
      f"std={np.std(clip_drop_standard):.4f} "
      f"min={np.min(clip_drop_standard):.4f} max={np.max(clip_drop_standard):.4f}")

print(f"\nNOTE: This toy measures standard VAE semantic drift only.")
print(f"  To test Idea-B (semantic anchor), implement decode-guidance using")
print(f"  DINOv2 gradient signals or semantic loss during decode.")
print(f"  See: /home/kas/.openclaw/workspace-domain/exp_semantic_anchor/ (if exists)")

total_time = time.time() - start_time
import psutil
mem = psutil.virtual_memory()
print(f"\nRuntime: {total_time:.0f}s ({total_time/60:.1f} min)")
print(f"Memory: used={mem.used/1024**3:.1f}GB free={mem.free/1024**3:.1f}GB avail={mem.available/1024**3:.1f}GB")
