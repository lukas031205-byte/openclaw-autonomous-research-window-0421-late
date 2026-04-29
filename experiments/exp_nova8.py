#!/usr/bin/env python3
"""
Exp-Nova-8: VAE Mode Collapse First-Pass Validation
Kernel execution — CPU only

Key insight: COCO val2017 images are cached as blob symlinks.
Natural images: load from cached COCO val2017 blob files (5000 images).
Synthetic images: 200 CIFAR-10 test images upscaled to 64x64.
"""

import os, time, json, random
import numpy as np
import torch
from torchvision import datasets, transforms
from torchvision.transforms import functional as TF
from PIL import Image
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# ============ DEVICE ============
device = torch.device('cpu')
print(f"Device: {device}")

# ============ SET SEEDS ============
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# ============ PATHS ============
WORKSPACE = "/home/kas/.openclaw/workspace-domain"
COCO_VAL2017_DIR = "/home/kas/.cache/huggingface/hub/datasets--merve--coco/snapshots/9e50abcdc1361852f34841af4939cbcd2d37c92f/val2017"
RESULT_PATH = os.path.join(WORKSPACE, "experiments", "exp_nova8_results.json")

# ============ MODEL LOADING ============
print("\n" + "="*60)
print("Loading models...")
print("="*60)

from transformers import CLIPModel, CLIPProcessor, AutoModel, AutoImageProcessor

print("Loading CLIP (openai/clip-vit-base-patch32)...")
clip_model = CLIPModel.from_pretrained(
    "openai/clip-vit-base-patch32",
    cache_dir=os.path.expanduser("~/.cache/huggingface/hub")
)
clip_processor = CLIPProcessor.from_pretrained(
    "openai/clip-vit-base-patch32",
    cache_dir=os.path.expanduser("~/.cache/huggingface/hub")
)
clip_model.eval()
clip_model.to(device)

print("Loading DINOv2-small...")
dino_model = AutoModel.from_pretrained(
    "facebook/dinov2-small",
    cache_dir=os.path.expanduser("~/.cache/huggingface/hub")
)
dino_processor = AutoImageProcessor.from_pretrained(
    "facebook/dinov2-small",
    cache_dir=os.path.expanduser("~/.cache/huggingface/hub")
)
dino_model.eval()
dino_model.to(device)

def get_clip_features(img_pil):
    """Get normalized CLIP image features."""
    with torch.no_grad():
        inputs = clip_processor(images=[img_pil], return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        outputs = clip_model.get_image_features(**inputs)
        if hasattr(outputs, 'last_hidden_state'):
            feats = outputs.last_hidden_state[:, 0]
        else:
            feats = outputs
        return feats / feats.norm(dim=-1, keepdim=True)

def get_dino_features(img_pil):
    """Get DINOv2 CLS features."""
    with torch.no_grad():
        inputs = dino_processor(images=[img_pil], return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        outputs = dino_model(**inputs)
        return outputs.last_hidden_state[:, 0]  # CLS token

def clip_similarity(img1, img2):
    f1 = get_clip_features(img1)
    f2 = get_clip_features(img2)
    return (f1 @ f2.T).item()

def dino_distance(img1, img2):
    f1 = get_dino_features(img1)
    f2 = get_dino_features(img2)
    return (f1 - f2).norm(dim=-1).item()

# ============ PART 1: SENSITIVITY CONTROL ============
print("\n" + "="*60)
print("PART 1: Sensitivity Control (30 images)")
print("="*60)

cifar_full = datasets.CIFAR10(
    root=os.path.join(WORKSPACE, "data"), 
    download=False, 
    train=False
)

sens_indices = random.sample(range(len(cifar_full)), 30)
sens_images = [cifar_full[i][0].convert('RGB') for i in sens_indices]

s_clip_list = []
s_dino_list = []

print("Computing sensitivity on perturbed images (σ=5 pixel noise)...")
for img in sens_images:
    np_img = np.array(img).astype(np.float32)
    noise = np.random.normal(0, 5, np_img.shape).astype(np.float32)
    noisy_np = np.clip(np_img + noise, 0, 255).astype(np.uint8)
    noisy_img = Image.fromarray(noisy_np)
    
    s_clip = clip_similarity(img, noisy_img)
    s_dino = dino_distance(img, noisy_img)
    # s_CLIP is 1 - cos_sim already from our function
    s_clip_list.append(s_clip)
    s_dino_list.append(s_dino)

mean_s_clip = float(np.mean(s_clip_list))
mean_s_dino = float(np.mean(s_dino_list))
sensitivity_ratio = mean_s_clip / mean_s_dino

print(f"  mean(s_CLIP noise): {mean_s_clip:.4f}")
print(f"  mean(s_DINO noise): {mean_s_dino:.4f}")
print(f"  sensitivity_ratio = mean_s_CLIP / mean_s_DINO: {sensitivity_ratio:.4f}")

del sens_images, cifar_full
import gc; gc.collect()

# ============ PART 2: VAE SETUP ============
print("\n" + "="*60)
print("PART 2: VAE Setup")
print("="*60)

print("Loading SD-VAE-ft-mse...")
from diffusers import AutoencoderKL

vae = AutoencoderKL.from_pretrained(
    "stabilityai/sd-vae-ft-mse",
    cache_dir=os.path.expanduser("~/.cache/huggingface/hub")
)
vae.eval()
vae.to(device)

def vae_roundtrip(img_pil):
    """VAE encode-decode roundtrip, returns reconstructed PIL Image."""
    with torch.no_grad():
        img_tensor = TF.to_tensor(img_pil).float().to(device)  # [3, H, W] in [0,1]
        latent = vae.encode(img_tensor.unsqueeze(0)).latent_dist.sample()
        recon = vae.decode(latent).sample.squeeze(0).cpu()
        recon = torch.clamp(recon, 0, 1)
        recon_np = (recon.permute(1, 2, 0).numpy() * 255).astype(np.uint8)
        return Image.fromarray(recon_np)

# ============ PART 3: DATASET PREPARATION ============
print("\n" + "="*60)
print("PART 3: Dataset Preparation")
print("="*60)

transform_64 = transforms.Compose([
    transforms.Resize((64, 64), interpolation=transforms.InterpolationMode.BILINEAR),
])

# NATURAL SET: COCO val2017 first 200 cached images
print(f"Using COCO val2017 from cache ({COCO_VAL2017_DIR})")
coco_files = sorted(os.listdir(COCO_VAL2017_DIR))[:200]
print(f"Natural set: {len(coco_files)} COCO val images (first 200)")

# SYNTHETIC SET: CIFAR-10 test, 200 random
cifar_test = datasets.CIFAR10(
    root=os.path.join(WORKSPACE, "data"),
    download=False,
    train=False
)
synth_indices = random.sample(range(len(cifar_test)), 200)
synth_images_pil = []
for idx in synth_indices:
    img_pil = cifar_test[idx][0].convert('RGB')
    img_pil = transform_64(img_pil)  # 32->64 bilinear upscale
    synth_images_pil.append(img_pil)
print(f"Synthetic set: {len(synth_images_pil)} CIFAR-10 images (upscaled to 64x64)")

del cifar_test
import gc; gc.collect()

# ============ PART 4: MAIN EXPERIMENT ============
print("\n" + "="*60)
print("PART 4: Computing ΔCLIP and ΔDINOv2 for both sets")
print("="*60)

def compute_metrics_batch(file_list, is_coco, desc):
    """
    file_list: list of image file paths (for COCO) or PIL images (for CIFAR)
    is_coco: True for COCO (file paths), False for CIFAR (PIL already in list)
    """
    dclip_list = []
    ddino_list = []
    
    for i, item in enumerate(tqdm(file_list, desc=desc)):
        try:
            if is_coco:
                # item is a file path (symlink to blob)
                blob_path = os.path.join(COCO_VAL2017_DIR, item)
                img_pil = Image.open(blob_path).convert('RGB')
                img_pil = transform_64(img_pil)
            else:
                img_pil = item
            
            # Original features
            f_clip_orig = get_clip_features(img_pil)
            f_dino_orig = get_dino_features(img_pil)
            
            # Roundtrip
            recon_pil = vae_roundtrip(img_pil)
            
            # Reconstructed features
            f_clip_recon = get_clip_features(recon_pil)
            f_dino_recon = get_dino_features(recon_pil)
            
            # ΔCLIP = 1 - cos_sim
            cos_sim = (f_clip_orig @ f_clip_recon.T).item()
            dclip = 1.0 - cos_sim
            
            # ΔDINOv2 = L2 distance
            ddino = (f_dino_orig - f_dino_recon).norm(dim=-1).item()
            
            dclip_list.append(dclip)
            ddino_list.append(ddino)
            
        except Exception as e:
            print(f"  Error at {desc} index {i}: {e}")
            continue
    
    return dclip_list, ddino_list

t_start = time.time()

# Natural (COCO)
print("\n--- Natural Set (COCO val2017, first 200) ---")
dclip_nat, ddino_nat = compute_metrics_batch(coco_files, True, "Natural (COCO)")
t_nat = time.time() - t_start
print(f"Natural: {len(dclip_nat)} images done in {t_nat:.1f}s")

# Synthetic (CIFAR-10)
print("\n--- Synthetic Set (CIFAR-10, 200, upscaled) ---")
dclip_synth, ddino_synth = compute_metrics_batch(synth_images_pil, False, "Synthetic (CIFAR)")
t_synth = time.time() - t_start
print(f"Synthetic: {len(dclip_synth)} images done in {t_synth:.1f}s")

total_runtime = (time.time() - t_start) / 60.0

# ============ PART 5: STATISTICAL TESTS ============
print("\n" + "="*60)
print("PART 5: Statistical Tests")
print("="*60)

from scipy import stats

dclip_nat = np.array(dclip_nat)
dclip_synth = np.array(dclip_synth)
ddino_nat = np.array(ddino_nat)
ddino_synth = np.array(ddino_synth)

n_nat = len(dclip_nat)
n_synth = len(dclip_synth)

# Means
dclip_nat_mean = float(np.mean(dclip_nat))
dclip_synth_mean = float(np.mean(dclip_synth))
ddino_nat_mean = float(np.mean(ddino_nat))
ddino_synth_mean = float(np.mean(ddino_synth))

print(f"ΔCLIP natural mean: {dclip_nat_mean:.4f}")
print(f"ΔCLIP synthetic mean: {dclip_synth_mean:.4f}")
print(f"ΔDINOv2 natural mean: {ddino_nat_mean:.4f}")
print(f"ΔDINOv2 synthetic mean: {ddino_synth_mean:.4f}")

# Welch's t-test (one-sided, α=0.01): H1 = ΔCLIP_nat > ΔCLIP_synth
t_stat, p_value = stats.ttest_ind(dclip_nat, dclip_synth, equal_var=False, alternative='greater')
t_test_p_value = float(p_value)
print(f"\nWelch's t-test (H1: ΔCLIP_nat > ΔCLIP_synth):")
print(f"  t={t_stat:.4f}, p={p_value:.6f}")

# Pearson correlations ΔCLIP vs ΔDINOv2
r_nat = float(np.corrcoef(dclip_nat, ddino_nat)[0, 1])
r_synth = float(np.corrcoef(dclip_synth, ddino_synth)[0, 1])

# Fisher r-to-z
z_nat = 0.5 * np.log((1 + r_nat) / (1 - r_nat))
z_synth = 0.5 * np.log((1 + r_synth) / (1 - r_synth))

fisher_r_to_z_nat = float(z_nat)
fisher_r_to_z_synth = float(z_synth)

print(f"\nPearson r (ΔCLIP vs ΔDINOv2):")
print(f"  Natural: r={r_nat:.4f}, z={z_nat:.4f}")
print(f"  Synthetic: r={r_synth:.4f}, z={z_synth:.4f}")

# Signal detection
sign_nat = 1 if r_nat >= 0 else -1
sign_synth = 1 if r_synth >= 0 else -1
signal_detected = "yes" if (t_test_p_value < 0.01) and (sign_nat != sign_synth) else "no"

print(f"\nSignal detection:")
print(f"  t-test p < 0.01: {t_test_p_value < 0.01}")
print(f"  r_nat sign: {'+' if sign_nat>0 else '-'}, r_synth sign: {'+' if sign_synth>0 else '-'}")
print(f"  sign flip: {sign_nat != sign_synth}")
print(f"  SIGNAL: {signal_detected}")

# ============ SAVE RESULTS ============
results = {
    "sensitivity_control_ratio": round(sensitivity_ratio, 4),
    "dclip_nat_mean": round(dclip_nat_mean, 4),
    "dclip_synth_mean": round(dclip_synth_mean, 4),
    "ddino_nat_mean": round(ddino_nat_mean, 4),
    "ddino_synth_mean": round(ddino_synth_mean, 4),
    "t_test_t_statistic": round(float(t_stat), 4),
    "t_test_p_value": round(t_test_p_value, 6),
    "pearson_r_nat": round(r_nat, 4),
    "pearson_r_synth": round(r_synth, 4),
    "fisher_r_to_z_nat": round(fisher_r_to_z_nat, 4),
    "fisher_r_to_z_synth": round(fisher_r_to_z_synth, 4),
    "signal_detected": signal_detected,
    "n_nat": int(n_nat),
    "n_synth": int(n_synth),
    "runtime_minutes": round(total_runtime, 2),
}

print("\n" + "="*60)
print("FINAL RESULTS")
print("="*60)
for k, v in results.items():
    print(f"  {k}: {v}")

with open(RESULT_PATH, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {RESULT_PATH}")