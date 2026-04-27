"""
Exp-Nova-8 v2: CPU experiment — CLIP-only (DINO OOM on this VM)
H2: VAE roundtrip on natural images causes asymmetric CLIP semantic drift

Memory-constrained design:
  - Process 1 image at a time, aggressive GC
  - CLIP ViT-B/32 only (no DINO - OOM killed the process)
  - 25 natural (CIFAR-10) + 25 synthetic (MNIST-like generated)
  - Compare ΔCLIP distributions: natural vs synthetic
  - H2: natural ΔCLIP >> synthetic ΔCLIP → SUPPORTED
"""

import os, sys, time, json, gc
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
import torchvision
import torchvision.transforms as T
import numpy as np

device = torch.device("cpu")
print(f"Device: {device}")

OUT_DIR = "/home/kas/.openclaw/workspace-domain/research/autonomous-research-0427-am"
os.makedirs(OUT_DIR, exist_ok=True)

# ════════════════════════════════════════════════════════════════════════════
# STEP 1: TinyCNN VAE on MNIST
# ════════════════════════════════════════════════════════════════════════════
print("\n═══ STEP 1: Training TinyCNN VAE on MNIST ════")

class TinyCNNVAE(nn.Module):
    def __init__(self, latent_dim=16):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Conv2d(1, 16, 3, stride=2, padding=1),   # 14x14
            nn.ReLU(),
            nn.Conv2d(16, 32, 3, stride=2, padding=1),  # 7x7
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(32 * 7 * 7, 64),
            nn.ReLU(),
        )
        self.fc_mu = nn.Linear(64, latent_dim)
        self.fc_logvar = nn.Linear(64, latent_dim)
        self.dec_fc = nn.Linear(latent_dim, 32 * 7 * 7)
        self.dec = nn.Sequential(
            nn.ReLU(),
            nn.ConvTranspose2d(32, 16, 3, stride=2, padding=1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(16, 1, 3, stride=2, padding=1, output_padding=1),
            nn.Sigmoid(),
        )

    def encode(self, x):
        h = self.enc(x)
        return self.fc_mu(h), self.fc_logvar(h)

    def decode(self, z):
        h = self.dec_fc(z).view(-1, 32, 7, 7)
        return self.dec(h)

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        return mu + torch.randn_like(std) * std

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar

transform_mnist = T.Compose([T.ToTensor()])
mnist_train = torchvision.datasets.MNIST(root=OUT_DIR, train=True, download=True, transform=transform_mnist)
subset_idx = list(range(0, len(mnist_train), 3))  # ~20k images
train_loader = DataLoader(Subset(mnist_train, subset_idx), batch_size=64, shuffle=True, num_workers=0)

vae = TinyCNNVAE(latent_dim=16).to(device)
optimizer = optim.Adam(vae.parameters(), lr=1e-3)

EPOCHS = 5
t0 = time.time()
for epoch in range(EPOCHS):
    vae.train()
    epoch_loss = 0.0
    batches = 0
    for imgs, _ in train_loader:
        imgs = imgs.to(device)
        optimizer.zero_grad()
        recon, mu, logvar = vae(imgs)
        recon_loss = nn.functional.mse_loss(recon, imgs, reduction='sum')
        kl = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        loss = recon_loss + 0.01 * kl
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
        batches += 1
        if batches >= 150:
            break
    print(f"  Epoch {epoch+1}/{EPOCHS} - loss: {epoch_loss/batches:.4f}")

vae.eval()
train_time = time.time() - t0
print(f"VAE training time: {train_time:.1f}s")

# Free training data
del train_loader, mnist_train, subset_idx
gc.collect()

# ════════════════════════════════════════════════════════════════════════════
# STEP 2: CLIP ViT-B/32 (load once, keep resident)
# ════════════════════════════════════════════════════════════════════════════
print("\n═══ STEP 2: Loading CLIP ViT-B/32 ════")
import clip
from PIL import Image

clip_model, clip_preprocess = clip.load("ViT-B/32", device=device)
clip_model.eval()
text_input = clip.tokenize(["a photo"]).to(device)

def get_clip_sim(img_tensor):
    """img_tensor: [1, 3, 224, 224] uint8 [0,255]"""
    with torch.no_grad():
        if img_tensor.max() > 1:
            img_tensor = img_tensor.float() / 255.0
        img_tensor = torch.clamp(img_tensor, 0, 1)
        clip_t = clip_preprocess(Image.fromarray(
            (img_tensor[0].permute(1,2,0).cpu().numpy() * 255).astype(np.uint8)
        )).unsqueeze(0).to(device)
        img_feat = clip_model.encode_image(clip_t)
        img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)
        text_feat = clip_model.encode_text(text_input)
        text_feat = text_feat / text_feat.norm(dim=-1, keepdim=True)
        return (img_feat @ text_feat.T).item()

# ════════════════════════════════════════════════════════════════════════════
# STEP 3: Load CIFAR-10 (natural) — 25 images
# ════════════════════════════════════════════════════════════════════════════
print("\n═══ STEP 3: Loading CIFAR-10 natural images ════")
transform_cifar = T.Compose([T.Resize((224, 224)), T.ToTensor()])
cifar = torchvision.datasets.CIFAR10(root=OUT_DIR, train=False, download=True, transform=transform_cifar)
np.random.seed(42)
natural_indices = np.random.choice(len(cifar), 25, replace=False).tolist()
natural_loader = DataLoader(Subset(cifar, natural_indices), batch_size=1, shuffle=False)
print(f"Loaded {len(natural_indices)} CIFAR-10 natural images")

# ════════════════════════════════════════════════════════════════════════════
# STEP 4: Generate 25 synthetic images (noise-based, VAE-friendly)
# ════════════════════════════════════════════════════════════════════════════
print("\n═══ STEP 4: Generating 25 synthetic images ════")
# Synthetic = random noise patched through the VAE's learned manifold
# Generate random z, decode to get "synthetic-like" images
synthetic_imgs = []
with torch.no_grad():
    for i in range(25):
        z = torch.randn(1, 16).to(device)
        recon = vae.decode(z)  # [1,1,28,28]
        # Upsample to 224 and tile to 3-channel
        recon_up = torch.nn.functional.interpolate(recon, size=(224, 224), mode='bilinear', align_corners=False)
        recon_3ch = recon_up.repeat(1, 3, 1, 1)  # [1, 3, 224, 224]
        # Convert to uint8
        recon_np = (recon_3ch[0].permute(1,2,0).cpu().numpy() * 255).astype(np.uint8)
        synthetic_imgs.append(recon_np)
print(f"Generated {len(synthetic_imgs)} synthetic images")

# ════════════════════════════════════════════════════════════════════════════
# STEP 5: Run experiment
# ════════════════════════════════════════════════════════════════════════════
print("\n═══ STEP 5: Running Exp-Nova-8 v2 ════")
results = {
    "experiment": "Exp-Nova-8 v2 (CLIP-only, DINO OOM)",
    "hypothesis": "H2: VAE roundtrip on natural images causes asymmetric CLIP semantic drift (ΔCLIP_natural >> ΔCLIP_synthetic)",
    "vae_config": {"epochs": 5, "batch_size": 64, "lr": 1e-3, "kl_weight": 0.01, "latent_dim": 16},
    "natural_dataset": "CIFAR-10 test set, 25 images",
    "synthetic_dataset": "VAE prior sampling (random z decode), 25 images",
    "clip_model": "ViT-B/32",
    "dinov2_status": "OOM killed - not available on this VM",
    "natural_images": [],
    "synthetic_images": [],
    "summary": {},
}

natural_deltas = []
synthetic_deltas = []

t_start = time.time()

# ── Natural (CIFAR-10) images ─────────────────────────────────────────────────
print("  Processing natural images...")
for img_idx, (img, _) in enumerate(natural_loader):
    img = img.to(device)  # [1, 3, 224, 224]
    
    # CLIP before
    clip_before = get_clip_sim(img)
    
    # VAE roundtrip
    with torch.no_grad():
        vae_in = img[:1].mean(dim=1, keepdim=True)  # [1,1,224,224]
        vae_in28 = torch.nn.functional.interpolate(vae_in, size=(28,28), mode='bilinear', align_corners=False)
        mu, logvar = vae.encode(vae_in28)
        z = vae.reparameterize(mu, logvar)
        recon_gray = vae.decode(z)  # [1,1,28,28]
        recon_up = torch.nn.functional.interpolate(recon_gray, size=(224,224), mode='bilinear', align_corners=False)
        recon_3ch = recon_up.repeat(1, 3, 1, 1)
    
    # CLIP after
    clip_after = get_clip_sim(recon_3ch)
    
    delta = clip_before - clip_after
    natural_deltas.append(delta)
    
    results["natural_images"].append({
        "idx": int(img_idx),
        "clip_before": round(clip_before, 6),
        "clip_after": round(clip_after, 6),
        "delta_clip": round(delta, 6),
    })
    
    del img, recon_gray, recon_up, recon_3ch, vae_in, vae_in28
    gc.collect()
    
    if (img_idx + 1) % 5 == 0:
        print(f"    Natural: {img_idx+1}/25 done")

# ── Synthetic (VAE prior) images ───────────────────────────────────────────────
print("  Processing synthetic images...")
for syn_idx in range(25):
    syn_img_np = synthetic_imgs[syn_idx]  # [224, 224, 3] uint8
    syn_tensor = torch.from_numpy(syn_img_np).permute(2,0,1).unsqueeze(0).float() / 255.0
    syn_tensor = syn_tensor.to(device)
    
    # CLIP before
    clip_before = get_clip_sim(syn_tensor)
    
    # VAE roundtrip (synthetic is already VAE output - still meaningful test)
    with torch.no_grad():
        vae_in = syn_tensor[:1].mean(dim=1, keepdim=True)  # grayscale
        vae_in28 = torch.nn.functional.interpolate(vae_in, size=(28,28), mode='bilinear', align_corners=False)
        mu, logvar = vae.encode(vae_in28)
        z = vae.reparameterize(mu, logvar)
        recon_gray = vae.decode(z)
        recon_up = torch.nn.functional.interpolate(recon_gray, size=(224,224), mode='bilinear', align_corners=False)
        recon_3ch = recon_up.repeat(1, 3, 1, 1)
    
    # CLIP after
    clip_after = get_clip_sim(recon_3ch)
    
    delta = clip_before - clip_after
    synthetic_deltas.append(delta)
    
    results["synthetic_images"].append({
        "idx": int(syn_idx),
        "clip_before": round(clip_before, 6),
        "clip_after": round(clip_after, 6),
        "delta_clip": round(delta, 6),
    })
    
    del syn_tensor, recon_gray, recon_up, recon_3ch, vae_in, vae_in28
    gc.collect()
    
    if (syn_idx + 1) % 5 == 0:
        print(f"    Synthetic: {syn_idx+1}/25 done")

total_time = time.time() - t_start

# ════════════════════════════════════════════════════════════════════════════
# STEP 6: Summary statistics
# ════════════════════════════════════════════════════════════════════════════
nat_arr = np.array(natural_deltas)
syn_arr = np.array(synthetic_deltas)

summary = {
    "n_natural": 25,
    "n_synthetic": 25,
    "total_time_seconds": round(total_time, 1),
    "vae_training_time_seconds": round(train_time, 1),
    "natural_delta_clip_mean": round(float(np.mean(nat_arr)), 6),
    "natural_delta_clip_std":  round(float(np.std(nat_arr)), 6),
    "natural_delta_clip_median": round(float(np.median(nat_arr)), 6),
    "synthetic_delta_clip_mean": round(float(np.mean(syn_arr)), 6),
    "synthetic_delta_clip_std":  round(float(np.std(syn_arr)), 6),
    "synthetic_delta_clip_median": round(float(np.median(syn_arr)), 6),
}

# Ratio of natural vs synthetic delta magnitude
nat_mean = summary["natural_delta_clip_mean"]
syn_mean = summary["synthetic_delta_clip_mean"]
delta_ratio = abs(nat_mean) / abs(syn_mean) if abs(syn_mean) > 1e-6 else 0.0
summary["natural_vs_synthetic_ratio"] = round(delta_ratio, 4)

# H2 verdict
if delta_ratio > 2.0:
    h2_verdict = "SUPPORTED"
    h2_detail = f"natural ΔCLIP ({nat_mean:.4f}) >> synthetic ΔCLIP ({syn_mean:.4f}), ratio={delta_ratio:.2f}x → asymmetric degradation confirmed"
elif delta_ratio > 1.0:
    h2_verdict = "PARTIALLY_SUPPORTED"
    h2_detail = f"natural ΔCLIP ({nat_mean:.4f}) > synthetic ΔCLIP ({syn_mean:.4f}), ratio={delta_ratio:.2f}x → some asymmetry"
else:
    h2_verdict = "FAIL"
    h2_detail = f"natural/synthetic ΔCLIP ratio={delta_ratio:.2f} ≈ 1 → symmetric degradation → H2 falsified"

summary["h2_verdict"] = h2_verdict
summary["h2_detail"] = h2_detail

print(f"\n═══ RESULTS ════")
print(f"Natural   ΔCLIP mean={nat_mean:.6f} std={summary['natural_delta_clip_std']:.6f} median={summary['natural_delta_clip_median']:.6f}")
print(f"Synthetic ΔCLIP mean={syn_mean:.6f} std={summary['synthetic_delta_clip_std']:.6f} median={summary['synthetic_delta_clip_median']:.6f}")
print(f"Natural/Synthetic ratio: {delta_ratio:.4f}")
print(f"H2 verdict: {h2_verdict}")
print(f"Detail: {h2_detail}")
print(f"Total time: {total_time:.1f}s (VAE train: {train_time:.1f}s)")

results["summary"] = summary

results_path = os.path.join(OUT_DIR, "exp_nova_8_results.json")
with open(results_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults written to: {results_path}")