# Kernel: LCS Compute Gate — VAE Latent Perturbation Result

**Date:** 2026-04-21 12:00 CST  
**Scale:** 20 CIFAR-10 test images × 3 σ levels = 60 data points  
**Models:** SD-VAE-FT-MSE, DINOv2-Small, CLIP-ViT-B/32  

## Global Correlation

Pearson r = -0.3532 (p = 5.637e-03)

## Per-σ Breakdown

| σ | r | p |
|---|-----|-----|
| 0.0 | -0.6229 | 3.349e-03 |
| 0.1 | 0.2185 | 3.548e-01 |
| 0.4 | -0.5236 | 1.781e-02 |

## Verdict

**FALSIFIED (r<0.3)**

## Runtime

11.7 minutes

## Raw Statistics

- DINO L2: mean=14.7906, std=4.6443
- CLIP CS: mean=0.9026, std=0.0312
- N = 60 data points
