#!/usr/bin/env python3
"""
Exp 1: DINOv2 Vulnerability Test (CPU) — RETRY
VAE roundtrip cosine similarity on DINOv2 features.
Threshold: mean CS > 0.97 → CLIP-specificity survives.

Approach: 
- Build AutoencoderKL from local config.json
- Remap old-diffusers attention keys (query/key/value/proj_attn) → new (to_q/to_k/to_v/to_out.0)
- Load remapped state dict from cached safetensors
"""

import json
import numpy as np
import torch
from PIL import Image
from pathlib import Path
from safetensors.torch import load_file
from diffusers import AutoencoderKL, ConfigMixin

# Paths
COCO_VAL2017 = Path("/home/kas/.cache/huggingface/hub/datasets--merve--coco/snapshots/9e50abcdc1361852f34841af4939cbcd2d37c92f/val2017")
VAE_CACHE = Path("/home/kas/.cache/huggingface/hub/models--stabilityai--sd-vae-ft-mse/snapshots/31f26fdeee1355a5c34592e401dd41e45d25a493")
ARTIFACT_DIR = Path("/home/kas/.openclaw/workspace-domain/research/0415-pm-cnlsa-cpu")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

N_IMAGES = 20
DEVICE = "cpu"
BATCH_SIZE = 4
TARGET_SIZE = 224

IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
IMAGENET_STD  = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)

def remap_vae_state_dict(state_dict):
    """Remap old-diffusers attention keys to new diffusers format."""
    key_map = {
        '.attentions.0.query.': '.attentions.0.to_q.',
        '.attentions.0.key.': '.attentions.0.to_k.',
        '.attentions.0.value.': '.attentions.0.to_v.',
        '.attentions.0.proj_attn.': '.attentions.0.to_out.0.',
    }
    new_state_dict = {}
    for k, v in state_dict.items():
        new_k = k
        for old, new in key_map.items():
            if old in k:
                new_k = k.replace(old, new)
                break
        new_state_dict[new_k] = v
    return new_state_dict

def build_vae_from_config(config_path):
    """Build AutoencoderKL directly from local config.json."""
    import json
    with open(config_path) as f:
        cfg = json.load(f)
    # Use ConfigMixin to load architecture
    vae = AutoencoderKL.from_config(cfg)
    return vae

def load_image_batch(paths, size=224):
    tensors = []
    for p in paths:
        img = Image.open(p).convert("RGB").resize((size, size), Image.BICUBIC)
        arr = np.array(img, dtype=np.float32) / 255.0
        tensors.append(arr.transpose(2, 0, 1))
    batch = torch.tensor(np.stack(tensors), dtype=torch.float32)
    batch = (batch - IMAGENET_MEAN) / IMAGENET_STD
    return batch

def main():
    print(f"=== Exp 1: DINOv2 Vulnerability Test (CPU) ===")
    print(f"N={N_IMAGES}, batch_size={BATCH_SIZE}, device={DEVICE}")

    img_paths = sorted(COCO_VAL2017.glob("*.jpg"))[:N_IMAGES]
    print(f"Found {len(img_paths)} images")

    # --- Load DINOv2-small ---
    print("Loading DINOv2-small...")
    from transformers import AutoModel
    dinov2 = AutoModel.from_pretrained("facebook/dinov2-small")
    dinov2 = dinov2.to(DEVICE).eval()
    print("DINOv2-small ready.")

    # --- Build AutoencoderKL from local config and load remapped state dict ---
    print("Building VAE from local config...")
    vae = build_vae_from_config(VAE_CACHE / "config.json")
    vae = vae.to(DEVICE).eval()
    print("VAE model built.")

    print("Loading & remapping VAE state dict...")
    raw_state = load_file(str(VAE_CACHE / "diffusion_pytorch_model.safetensors"))
    remapped = remap_vae_state_dict(raw_state)
    print(f"  Remapped {len(raw_state)} → {len(remapped)} keys")

    missing, unexpected = vae.load_state_dict(remapped, strict=False)
    print(f"  Missing keys: {len(missing)}, Unexpected: {len(unexpected)}")
    if missing:
        print(f"  Missing sample: {missing[:5]}")
    if unexpected:
        print(f"  Unexpected sample: {unexpected[:5]}")
    print("VAE loaded successfully.")

    # --- Original DINOv2 features ---
    print("Extracting DINOv2 features from originals...")
    all_orig = []
    for i in range(0, N_IMAGES, BATCH_SIZE):
        batch = load_image_batch(img_paths[i:i+BATCH_SIZE], TARGET_SIZE).to(DEVICE)
        with torch.no_grad():
            out = dinov2(batch)
            cls = out.last_hidden_state[:, 0, :]
        all_orig.append(cls.cpu())
        print(f"  orig batch {i//BATCH_SIZE+1}/{(N_IMAGES+BATCH_SIZE-1)//BATCH_SIZE}")
    orig_features = torch.cat(all_orig, dim=0)
    print(f"  Shape: {orig_features.shape}")

    # --- VAE roundtrip ---
    print("VAE encode→decode roundtrip...")
    all_recon = []
    for i in range(0, N_IMAGES, BATCH_SIZE):
        batch = load_image_batch(img_paths[i:i+BATCH_SIZE], TARGET_SIZE).to(DEVICE)
        with torch.no_grad():
            latents = vae.encode(batch).latent_dist.sample()
            recon = vae.decode(latents).sample
        all_recon.append(recon.cpu())
        print(f"  VAE batch {i//BATCH_SIZE+1}/{(N_IMAGES+BATCH_SIZE-1)//BATCH_SIZE}")
    recon_tensor = torch.cat(all_recon, dim=0)
    print(f"  Shape: {recon_tensor.shape}")

    # --- Reconstructed DINOv2 features ---
    print("Extracting DINOv2 features from reconstructions...")
    all_recon_feats = []
    for i in range(0, N_IMAGES, BATCH_SIZE):
        batch = recon_tensor[i:i+BATCH_SIZE].to(DEVICE)
        with torch.no_grad():
            out = dinov2(batch)
            cls = out.last_hidden_state[:, 0, :]
        all_recon_feats.append(cls.cpu())
        print(f"  recon batch {i//BATCH_SIZE+1}/{(N_IMAGES+BATCH_SIZE-1)//BATCH_SIZE}")
    recon_features = torch.cat(all_recon_feats, dim=0)
    print(f"  Shape: {recon_features.shape}")

    # --- Cosine similarity ---
    orig_norm = orig_features / orig_features.norm(dim=1, keepdim=True).clamp(min=1e-8)
    recon_norm = recon_features / recon_features.norm(dim=1, keepdim=True).clamp(min=1e-8)
    cs_per_img = (orig_norm * recon_norm).sum(dim=1).numpy()

    print(f"\nPer-image CS: {[round(x,4) for x in cs_per_img]}")
    mean_cs = float(np.mean(cs_per_img))
    std_cs = float(np.std(cs_per_img))
    cohens_d = mean_cs / std_cs if std_cs > 0 else 0.0
    threshold_check = "pass" if mean_cs > 0.97 else "fail"

    print(f"\n=== RESULTS ===")
    print(f"Mean CS:  {mean_cs:.4f} ± {std_cs:.4f}")
    print(f"Cohen's d: {cohens_d:.4f}")
    print(f"Threshold (>0.97): {threshold_check}")

    results = {
        "mean_cs": round(mean_cs, 4),
        "std_cs": round(std_cs, 4),
        "cohens_d": round(cohens_d, 4),
        "threshold_check": threshold_check,
        "n_images": N_IMAGES,
        "per_image_cs": [round(x, 4) for x in cs_per_img.tolist()],
        "architectural_note": "ViT-S/14 vs ViT-B/32 confound acknowledged; SD VAE key remapping (query→to_q etc.) required for cached model compatibility"
    }

    out_path = ARTIFACT_DIR / "exp1_dinov2_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_path}")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
