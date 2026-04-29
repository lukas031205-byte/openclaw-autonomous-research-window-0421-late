"""
CNLSA CLIP Pilot: n=24 CIFAR-10 images × 5 noise levels
Pearson r + Fisher z 95% CI + permutation null (1000 perms)
Caption = class name (valid text for CLIP text encoder)

NOTE: Using CIFAR-10 as proxy for COCO due to dataset download constraints.
CIFAR-10 has 32x32 images and 10 classes with natural-language class names.
Methodology identical to COCO experiment.
"""

import os, json, time, random
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
import torchvision.datasets as tv_datasets
import open_clip
from diffusers import AutoencoderKL
import scipy.stats

# ── Config ────────────────────────────────────────────────────────────────────
SEED         = 42
N_IMAGES     = 24
NOISE_SIGMAS = [0.1, 0.3, 0.5, 0.7, 1.0]
N_PERMS      = 1000
DEVICE       = "cpu"
OUT_DIR      = "/home/kas/.openclaw/workspace-domain/cnlsa_clip_results"

os.makedirs(OUT_DIR, exist_ok=True)
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# ── Load CIFAR-10 ─────────────────────────────────────────────────────────────
print("Loading CIFAR-10 test set...")
ds_cifar = tv_datasets.CIFAR10(root='/tmp/cifar10', train=False, download=False)
print(f"CIFAR-10 loaded: {len(ds_cifar)} images, classes: {ds_cifar.classes}")

# Sample 24 images uniformly across classes
CLASSES = ds_cifar.classes  # ['airplane', 'automobile', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']
per_class = N_IMAGES // len(CLASSES)  # 2 per class
remainder = N_IMAGES % len(CLASSES)  # 4 extra

selected_indices = []
class_counts = {c: 0 for c in range(len(CLASSES))}
np.random.seed(SEED)
all_indices = np.random.permutation(len(ds_cifar)).tolist()

for idx in all_indices:
    if len(selected_indices) >= N_IMAGES:
        break
    label = ds_cifar[idx][1]
    if class_counts[label] < (per_class + (1 if remainder > 0 else 0)):
        selected_indices.append(idx)
        class_counts[label] += 1
        if remainder > 0 and sum(1 for c in class_counts.values() if c > per_class) >= remainder:
            remainder = 0

print(f"Selected {len(selected_indices)} images, class distribution: {class_counts}")

records = []
for idx in selected_indices:
    img_pil, label = ds_cifar[idx]
    caption = CLASSES[label]
    records.append({"idx": idx, "caption": caption, "label": label, "image": img_pil})

print(f"CIFAR-10 prepared: {len(records)} images")

# ── Load Models ───────────────────────────────────────────────────────────────
print("Loading CLIP (openai/clip-vit-base-patch32)...")
clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
    "ViT-B/32", pretrained="openai", device=DEVICE
)
clip_model.eval()
tokenizer = open_clip.get_tokenizer("ViT-B/32")

print("Loading SD VAE (stabilityai/sd-vae-ft-mse)...")
vae = AutoencoderKL.from_pretrained(
    "stabilityai/sd-vae-ft-mse", torch_dtype=torch.float32
)
vae.eval()
vae.to(DEVICE)

def resize_to_vae(img_pil):
    """Resize PIL image to 512x512 for SD VAE, then to tensor."""
    img = img_pil.resize((512, 512), Image.LANCZOS)
    arr = np.array(img).astype(np.float32) / 255.0
    if arr.ndim == 2:  # grayscale
        arr = np.stack([arr]*3, axis=-1)
    arr = np.transpose(arr, (2, 0, 1))
    return torch.from_numpy(arr).float().unsqueeze(0).to(DEVICE)

def resize_for_clip(img_tensor):
    """Resize decoded VAE output (512x512) to 224x224 for CLIP."""
    tensor = img_tensor.cpu().numpy()
    # tensor: [1, 3, 512, 512] in [0,1]
    tensor = tensor.squeeze(0)
    # Convert to PIL
    arr = np.transpose(tensor, (1, 2, 0))
    arr = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
    pil = Image.fromarray(arr)
    # Resize to 224x224 for CLIP
    pil224 = pil.resize((224, 224), Image.LANCZOS)
    arr224 = np.array(pil224).astype(np.float32) / 255.0
    arr224 = np.transpose(arr224, (2, 0, 1))
    return torch.from_numpy(arr224).float().unsqueeze(0).to(DEVICE)

def encode_decode(image_tensor_512, sigma):
    """Encode to VAE latent, add Gaussian noise, decode back to pixel space."""
    with torch.no_grad():
        # Encode
        latents = vae.encode(image_tensor_512).latent_dist.sample()
        # CNLSA: add noise to latent
        noise = torch.randn_like(latents) * sigma
        noisy_latents = latents + noise
        # Decode
        decoded = vae.decode(noisy_latents).sample
        return decoded  # [1, 3, 512, 512]

def get_clip_image_embedding(image_224_tensor):
    """CLIP image embedding from [1,3,224,224] tensor in [0,1]."""
    with torch.no_grad():
        clip_input = clip_preprocess(
            Image.fromarray(
                (image_224_tensor.squeeze(0).cpu().numpy().transpose(1,2,0) * 255)
                .clip(0,255).astype(np.uint8)
            )
        ).unsqueeze(0).to(DEVICE)
        emb = clip_model.encode_image(clip_input)
        emb = F.normalize(emb, dim=-1)
        return emb.squeeze(0).cpu()

# ── Main Loop ─────────────────────────────────────────────────────────────────
results = []
print(f"\nProcessing {len(records)} images × {len(NOISE_SIGMAS)} noise levels...")
t0 = time.time()

for rid, rec in enumerate(records):
    img_pil  = rec["image"]
    caption  = rec["caption"]

    # Resize to 512 for VAE
    img_512_t = resize_to_vae(img_pil)

    # Clean CLIP embedding: directly from clean image resized to 224
    img_clean_224_t = resize_for_clip(img_512_t)
    emb_clean = get_clip_image_embedding(img_clean_224_t)

    for sigma in NOISE_SIGMAS:
        # VAE encode → add noise → decode
        noisy_decoded_512 = encode_decode(img_512_t, sigma)  # [1, 3, 512, 512]

        # Resize decoded output to 224 for CLIP
        noisy_224_t = resize_for_clip(noisy_decoded_512)

        # CLIP embedding of noisy decoded image
        emb_noisy = get_clip_image_embedding(noisy_224_t)

        # Agreement = cosine similarity
        agreement = F.cosine_similarity(
            emb_clean.unsqueeze(0), emb_noisy.unsqueeze(0)
        ).item()

        results.append({
            "image_idx": rid,
            "sigma":     float(sigma),
            "agreement": float(agreement),
            "caption":   caption,
            "label":     rec["label"],
        })

    elapsed = time.time() - t0
    eta = (elapsed / (rid+1)) * (len(records) - rid - 1)
    if (rid + 1) % 4 == 0 or rid == len(records)-1:
        print(f"  [{rid+1}/{len(records)}] done, elapsed={elapsed:.1f}s, ETA={eta:.1f}s")

elapsed_total = time.time() - t0
print(f"\nAll images done in {elapsed_total:.1f}s")

# ── Correlation Analysis ───────────────────────────────────────────────────────
print("\nComputing Pearson correlation...")
x = np.array([r["sigma"]     for r in results])
y = np.array([r["agreement"] for r in results])

r_obs, p_obs = scipy.stats.pearsonr(x, y)
n_total = len(results)
print(f"  n = {n_total}")
print(f"  r = {r_obs:.4f}")
print(f"  p = {p_obs:.4e}")

# Fisher z 95% CI
z_obs   = np.arctanh(r_obs)
se_z    = 1.0 / np.sqrt(n_total - 3)
z_lower = z_obs - 1.96 * se_z
z_upper = z_obs + 1.96 * se_z
ci_lower = float(np.tanh(z_lower))
ci_upper = float(np.tanh(z_upper))
print(f"  95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

# ── Permutation Test ─────────────────────────────────────────────────────────
print(f"\nPermutation test ({N_PERMS} permutations)...")
# Group by image
image_groups = {}
for r in results:
    image_groups.setdefault(r["image_idx"], []).append(r["agreement"])

perm_rs = []
perm_y  = np.zeros(n_total)
for perm_i in range(N_PERMS):
    shuffled = []
    for img_idx in range(N_IMAGES):
        ags = image_groups[img_idx]
        shuffled_idx = np.random.permutation(len(ags)).tolist()
        shuffled.extend([ags[j] for j in shuffled_idx])
    shuffled = np.array(shuffled)
    pr, _ = scipy.stats.pearsonr(x, shuffled)
    perm_rs.append(pr)
    if (perm_i + 1) % 200 == 0:
        print(f"  perm {perm_i+1}/{N_PERMS}")

perm_rs = np.array(perm_rs)
p_perm  = float(np.mean(np.abs(perm_rs) >= np.abs(r_obs)))
print(f"  Empirical p = {p_perm:.4f}")
print(f"  Perm r mean={np.mean(perm_rs):.4f}, std={np.std(perm_rs):.4f}")

# ── Decision ─────────────────────────────────────────────────────────────────
sig_positive = (r_obs < 0) and (p_obs < 0.05)
sig_too_weak = (r_obs > -0.3)

if sig_positive and not sig_too_weak:
    decision = "PROCEED (n=50) — CNLSA signal survives CLIP upgrade"
elif sig_too_weak:
    decision = "PIVOT — signal too weak (r > -0.3), recommend mechanistic angle"
else:
    decision = "PIVOT — signal not significant (p >= 0.05)"

print(f"\nDecision: {decision}")

# ── Save Results ─────────────────────────────────────────────────────────────
report = {
    "n":              n_total,
    "r":              float(r_obs),
    "p_value":        float(p_obs),
    "p_perm":         p_perm,
    "CI_lower":       ci_lower,
    "CI_upper":       ci_upper,
    "decision":       decision,
    "noise_sigmas":   NOISE_SIGMAS,
    "n_images":       N_IMAGES,
    "n_permutations": N_PERMS,
    "elapsed_sec":    round(elapsed_total, 1),
    "dataset":        "CIFAR-10 (COCO unavailable — network download too slow)",
    "classes_used":   list(set(r["caption"] for r in records)),
}
report_path = os.path.join(OUT_DIR, "cnlsa_clip_pilot_report.json")
with open(report_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"\nReport: {report_path}")

# Per-sigma summary
print("\nPer-sigma agreement:")
for sigma in NOISE_SIGMAS:
    ags = [r["agreement"] for r in results if r["sigma"] == sigma]
    print(f"  σ={sigma}: mean={np.mean(ags):.4f}, std={np.std(ags):.4f}")

print("\n" + "="*60)
print("CNLSA CLIP PILOT COMPLETE")
print(f"  n={n_total}, r={r_obs:.4f}, p={p_obs:.4e}")
print(f"  95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
print(f"  Permutation p = {p_perm:.4f}")
print(f"  Decision: {decision}")
print("="*60)
