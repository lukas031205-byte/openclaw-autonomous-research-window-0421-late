# 0427-AM Window — VAE Asymmetry Test Suite

**Created:** 2026-04-27 00:05 CST
**Status:** GPU BLOCKED — CPU toy design only

## Active Thread
VAE Decoder Mode Collapse Asymmetry Test

## Hypothesis
- Natural images are OOD for VAE decoder → mode-seeking reconstruction destroys CLIP-semantic attributes while preserving DINOv2 structural attributes
- Test: ΔCLIP/ΔDINO_L2 ratio on semantically-complex vs simple CIFAR-10 subsets
- SUPPORTED if: ratio >2x
- FAIL if: proportional degradation OR DINOv2 degrades more than CLIP

## Prior Evidence
- CNLSA: synthetic r=+0.57, natural COCO r=-0.43 (sign flip)
- CIFAR-10 ratio=2.24 (TinyCNNVAE 1-epoch — decoder undertrained, NOT mode collapse)
- DINOv2 L2 = low-level structural proxy; CLIP = semantic attribute measurer

## GPU Status
- nvidia-smi not found (5+ days)
- VM RAM ~600MB free
- Kernel experiments (Exp-Nova-7, VAE mode collapse) running since ~20:15 CST

## Artifact Status
- SUITE.md: this file ✅
- run_asymmetry_test.sh: created (needs GPU)
- WINDOW_SUMMARY.md: pending subagent results

## Next Action
GPU restore → run asymmetry test on CIFAR-10 vs COCO
