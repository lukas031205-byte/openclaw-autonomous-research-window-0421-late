# LCS Compute Gate — 实验设计文档
**Author:** Kernel  
**Date:** 2026-04-21  
**Status:** GPU-unavailable; CPUfeasible subset defined below

---

## 1. 核心假设

> **Hypothesis:** LCS (Latent Consistency Score) threshold 可以作为 adaptive compute gate 的触发器——当 DINOv2 L2 distance 在像素空间proxy测量中超过阈值时，触发全量 semantic consistency 检查或 early-exit。

换言之：DINOv2 frame-level L2 distance（计算代价低）能够预测 CLIP cosine similarity（语义一致性金标准）是否崩溃。如果二者相关性足够强（Pearson r > 0.3 初步门槛），则可以用 L2 distance 作为轻量哨兵，节省 CLIP forward pass 的计算。

**Strategic alignment:** Nova Idea A (LCS compute gate), priority 0.92.  
**Falsification condition:** 如果 DINOv2 L2 distance 不能预测 CLIP semantic inconsistency（r < 0.3），则 compute gate 想法证伪，放弃此方向。

---

## 2. 最小 CPU 实验设计（GPU恢复前可执行）

### 2.1 数据集
- **CIFAR-10** (60k images, 32×32) — 用于快速迭代
- 额外：合成高斯噪声序列（5个 noise level: σ ∈ {0.05, 0.1, 0.2, 0.4, 0.6}），生成模拟 "frame drift" 轨迹
- 使用预训练模型（无需GPU）：DINOv2 ViT-S/14，CLIP ViT-B/32

### 2.2 指标定义

| 指标 | 模型 | 说明 |
|------|------|------|
| L2 proxy | DINOv2 ViT-S/14 (frozen) | 提取 [CLS] token，帧间 L2 distance |
| Semantic gold | CLIP ViT-B/32 (frozen) | 帧间 cosine similarity |
| LCS proxy | 1 - normalized_L2 | 归一化后的 L2 → 一致性分数 |

### 2.3 实验流程

```
For each noise_level in [0.05, 0.1, 0.2, 0.4, 0.6]:
    1. 从CIFAR-10随机选取500个样本对 (anchor, positive)
    2. 对anchor添加noise_level σ的高斯噪声生成noisy version
    3. 计算DINOv2 L2 distance: d_dino = ||f_dino(anchor) - f_dino(noisy)||
    4. 计算CLIP cosine similarity: cs_clip = cosine(f_clip(anchor), f_clip(noisy))
    5. 记录 (noise_level, d_dino, cs_clip) 三元组
    6. 输出: Pearson r(d_dino, cs_clip) across all noise levels
```

### 2.4 CPU 计算量估算
- DINOv2 ViT-S/14 forward: ~0.3s/image on CPU (batched, 32 batch)
- CLIP ViT-B/32 forward: ~0.5s/image on CPU (batched, 32 batch)
- 总样本: 500 pairs × 5 noise levels = 2500 对
- 总时间: ~2500/32 × (0.3+0.5) / 2 ≈ 20-30 min (CPU)
- **GPU不可用不影响此实验**

### 2.5 失败条件

| 条件 | 阈值 | 结论 |
|------|------|------|
| Pearson r(DINO L2, CLIP CS) | < 0.3 | **FALSIFIED** — L2不能预测语义一致性，放弃compute gate |
| Pearson r | 0.3–0.5 | Weak signal — 需要更大数据集或更好的proxy |
| Pearson r | > 0.5 | Promising — 继续完整实验 |

### 2.6 Compute Saving 估算（基于threshold）

如果相关性验证通过，用以下方法估算 saving：

```
gate_threshold ∈ [0.1, 0.2, 0.3, 0.4, 0.5]:
    early_exit_rate = fraction of samples where L2_distance < threshold
    avg_LCS_at_exit = mean(CLIP_CS for exited samples)
    false_negative_rate = fraction of exited samples where CLIP_CS < 0.5
```

Saved compute = early_exit_rate × CLIP forward pass cost

---

## 3. GPU 恢复后的完整实验（完整验证）

### 3.1 数据集升级
- **CIFAR-10 → CIFAR-100** (更大语义多样性)
- **Real trajectory 数据**: 使用 Consistency-Preserving (2602.15287) 发布的评估轨迹，或使用 SDXL-Turbo 端到端生成轨迹

### 3.2 完整指标栈

| 指标 | 用途 | 计算代价 |
|------|------|---------|
| DINOv2 L2 distance | LCS proxy (gate trigger) | Low (仅 encoder) |
| CLIP cosine similarity | Semantic gold standard | Medium |
| TrACE-Video metric (LCS) | Main evaluation metric | High (需要 diffusion) |

### 3.3 ROC-AUC 评估

将 DINOv2 L2 distance 作为二分类器：
- **Positive class**: CLIP CS < 0.5（语义不一致）
- **Negative class**: CLIP CS ≥ 0.5（语义一致）
- **Metric**: ROC-AUC for DINO L2 distinguishing consistent vs inconsistent

```
GPU实验失败条件: AUC ≤ 0.55 → 放弃compute gate方向
(AUC 0.55 = 仅比random好一点)
```

### 3.4 端到端生成轨迹实验

```
1. 使用 SDXL-Turbo 生成 200 个视频轨迹 (step 0 → step 50)
2. 每个轨迹记录:
   - frame-level DINOv2 L2 distance (低代价)
   - CLIP cosine similarity (中代价)
   - TrACE-Video LCS (高代价, ground truth)
3. 评估: DINO L2 的 ROC-AUC 预测 CLIP semantic inconsistency
4. 评估: CLIP CS 的 ROC-AUC 预测 TrACE-Video LCS 崩溃
5. 结论: 是否形成有效的三明治计算架构
```

### 3.5 资源需求
- **15-25 min on single A100 (40GB)** for SDXL-Turbo trajectories
- DINOv2 + CLIP evaluation: ~5 min on CPU

---

## 4. 与 Consistency-Preserving (2602.15287) 的关系

Consistency-Preserving 是最接近 TrACE-Video 的已有工作，核心区别：

| 维度 | Consistency-Preserving | TrACE-Video + LCS Gate |
|------|------------------------|------------------------|
| Metric | CFG-free consistency | Latent semantic consistency |
| Compute gate | 无 | DINO L2 threshold |
| Video domain | 主要video | Image + video |
| 评估协议 | FVD, Fed | ROC-AUC, compute saving |

**补充价值:** 如果 LCS compute gate 在 SDXL-Turbo 轨迹上验证通过，可以显著加速 Consistency-Preserving 的推理（early exit），同时保持 semantic fidelity。

---

## 5. 下一步行动

1. **立即执行（CPU）**: 运行 `lcs_toy.py`，得到 r(DINO L2, CLIP CS) 的初步结果
2. **如果 r < 0.3**: 放弃 LCS compute gate 方向，更新 Nova Idea A 状态为 falsified
3. **如果 r ≥ 0.3**: 准备 GPU 完整实验，联系 CMU/Princtox 合作者获取 compute
4. **Monitor GPU status**: 每4小时检查一次 GPU queue 状态

---

## 6. 参考文献

- Consistency-Preserving: arXiv 2602.15287
- DINOv2: Facebookresearch/dinov2
- CLIP: openai/CLIP
- Re2Pix: Sta8is/Re2Pix (arxiv 2604.11707, code not released yet)
