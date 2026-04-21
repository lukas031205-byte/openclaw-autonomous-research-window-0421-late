#!/usr/bin/env python3
"""LCS Compute Gate Toy — Minimal CPU experiment"""
import numpy as np
import torch
import torch.nn.functional as F
from torchvision.datasets import CIFAR10
import torchvision.transforms as T
import timm
from scipy.stats import pearsonr

torch.manual_seed(42)
np.random.seed(42)

print("Loading models...")
dino = timm.create_model('vit_small_patch14_dinov2.lvd142m', pretrained=True)
dino.eval()
clip_model = timm.create_model('vit_base_patch32_clip_224.openai', pretrained=True)
clip_model.eval()

print("Loading CIFAR-10...")
ds = CIFAR10(root='/tmp/cifar10', train=False, download=True, transform=T.ToTensor())
anchors = torch.stack([ds[i][0] for i in range(30)])

def get_dino_features(model, images):
    """Get DINOv2 features. Output is (B, N, D) or (B, D)."""
    with torch.no_grad():
        out = model(images)
        if out.dim() == 3:
            # (B, N, D) → mean pool over N
            feat = out.mean(dim=1)
        elif out.dim() == 2:
            feat = out
        else:
            feat = out.flatten(1).mean(dim=-1)
        return F.normalize(feat, dim=-1)

def get_clip_features(model, images):
    """Get CLIP image features. Output is (B, D) or (B, N, D)."""
    with torch.no_grad():
        out = model(images)
        if out.dim() == 3:
            feat = out.mean(dim=1)
        elif out.dim() == 2:
            feat = out
        else:
            feat = out.flatten(1).mean(dim=-1)
        return F.normalize(feat, dim=-1)

dino_t = T.Compose([T.Resize((518, 518))])
clip_t = T.Compose([T.Resize((224, 224))])

noise_levels = [0.1, 0.2, 0.4]
all_l2, all_cs = [], []

for nl in noise_levels:
    noisy = torch.clamp(anchors + torch.randn_like(anchors) * nl, 0, 1)
    
    with torch.no_grad():
        a_dino = get_dino_features(dino, dino_t(anchors))
        n_dino = get_dino_features(dino, dino_t(noisy))
        l2 = torch.norm(a_dino - n_dino, dim=-1).numpy()
        
        a_clip = get_clip_features(clip_model, clip_t(anchors))
        n_clip = get_clip_features(clip_model, clip_t(noisy))
        cs = F.cosine_similarity(a_clip, n_clip, dim=-1).numpy()
    
    r, p = pearsonr(l2, cs)
    print(f"σ={nl} | DINO-L2={l2.mean():.4f}±{l2.std():.4f} | CLIP-CS={cs.mean():.4f}±{cs.std():.4f} | r={r:.4f} (p={p:.2e})")
    all_l2.extend(l2.tolist())
    all_cs.extend(cs.tolist())

r_all, p_all = pearsonr(np.array(all_l2), np.array(all_cs))
print(f"\nOVERALL r = {r_all:.4f} (p={p_all:.2e})")
verdict = "LCS_PROXY_VIABLE" if r_all > 0.3 else "LCS_PROXY_FALSIFIED"
print(f"VERDICT: {verdict}")
print(f"\nCONCLUSION: DINOv2 L2 {'DOES' if r_all > 0.3 else 'DOES NOT'} predict CLIP semantic inconsistency")
