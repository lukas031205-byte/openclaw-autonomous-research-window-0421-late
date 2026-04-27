#!/bin/bash
# VAE Asymmetry Test — run_asymmetry_test.sh
# GPU REQUIRED — this is a placeholder until GPU is restored
# Target: CIFAR-10 semantically-complex vs simple subsets
# Measure: ΔCLIP / ΔDINO_L2 ratio

echo "ERROR: GPU required to run this experiment"
echo "Expected command once GPU is available:"
echo "  python vae_asymmetry_test.py --dataset cifar10 --subset complex"
echo "  python vae_asymmetry_test.py --dataset coco --subset all"
echo ""
echo "Hypothesis: ΔCLIP/ΔDINO_L2 ratio >2x on complex vs simple = SUPPORTED"
echo "FAIL condition: proportional degradation OR DINOv2 degrades more than CLIP"

exit 1
