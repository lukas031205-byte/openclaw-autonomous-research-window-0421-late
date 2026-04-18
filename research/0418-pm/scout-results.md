# Scout 0418-PM 文献调研结果

窗口：2026年2月–4月（60天）
要求：CVPR/ICLR/NeurIPS/ICCV 2025-2026，必须有代码/项目页

---

## 方向1：TrACE-Video（帧间隐空间一致性 / 视频生成质量评估）

### 1. Frame Guidance
- **arXiv:** 2506.07177 | **年份:** 2026 | **会议:** ICLR 2026（已接收）
- **代码:** https://github.com/agwmon/frame-guidance
- **核心贡献:** 提出无需训练的帧级控制框架，通过优化关键帧/深度/草图的隐空间表征实现细粒度时序一致性控制，无需任何模型微调。

### 2. StableWorld
- **arXiv:** 2601.15281 | **年份:** 2026（1月） | **会议:** –
- **代码:** https://github.com/xbyym/StableWorld
- **核心贡献:** 指出长视频空间漂移的根因是帧间VAE/隐空间不一致，提出动态帧淘汰机制（Dynamic Frame Eviction）主动移除不一致帧以维持场景稳定性。

### 3. Video-T1
- **arXiv:** 2503.18942 | **年份:** 2025 | **会议:** ICCV 2025
- **代码:** https://github.com/THU-SI/Video-T1
- **核心贡献:** 将测试时Scaling重新定义为噪声→视频轨迹上的搜索问题，提出Tree-of-Frames（ToF）搜索，用更多测试时计算换取视频质量和时序一致性。

### 4. EvoSearch
- **arXiv:** 2505.17618 | **年份:** 2025 | **会议:** ICLR 2026（under review）
- **代码:** https://github.com/tinnerhrhe/EvoSearch-codes
- **核心贡献:** 将去噪轨迹视为进化路径，初始噪声和中间状态均向更高质量方向进化，使SD2.1超越GPT4o，Wan 1.3B超越Wan 14B。

### 5. LatSearch
- **arXiv:** 2603.14526 | **年份:** 2026（3月） | **会议:** ICLR 2026（under review）
- **代码:** https://github.com/zengqunzhao/LatSearch
- **核心贡献:** 提出隐空间奖励模型在任意去噪时间步评估部分去噪隐变量（视觉质量/运动/文本对齐），实现79%推理时间削减同时保持VBench-2.0质量。

---

## 方向2：CNLSA（VAE语义漂移 / 扩散模型隐空间分析）

### 1. SVG
- **arXiv:** 2510.15301 | **年份:** 2026 | **会议:** ICLR 2026
- **代码:** https://github.com/shiml20/SVG | **项目页:** https://howlin-wang.github.io/svg/
- **核心贡献:** 用自监督DINOv2完全替代VAE，从根源上消除VAE语义gap，在语义结构化特征空间直接训练扩散模型，实现更高效的小步数采样。

### 2. SFD — Semantic-First Diffusion
- **arXiv:** 2512.04926 | **年份:** 2026 | **会议:** CVPR 2026
- **代码:** https://github.com/yuemingPAN/SFD | **项目页:** https://yuemingpan.github.io/SFD.github.io/
- **核心贡献:** 提出双隐空间异步去噪范式，语义（SemVAE/DINOv2）主导、纹理（SD-VAE）跟随，ImageNet 256²达FID 1.04，收敛速度提升100×。

### 3. Send-VAE
- **arXiv:** 2601.05823 | **年份:** 2026 | **会议:** arXiv（1月）
- **代码:** https://github.com/KlingAIResearch/Send-VAE
- **核心贡献:** 提出语义解耦VAE（Send-VAE），用ViT非线性映射器桥接VAE局部结构与VFM密集语义，FID 1.21 on ImageNet 256²，从根本上修复CNLSA定位的VAE语义gap。

### 4. REPA-G
- **arXiv:** 2602.03753 | **年份:** 2026 | **会议:** arXiv（2月）
- **代码:** https://github.com/valeoai/REPA-G
- **核心贡献:** 通过预训练VFM提取的表征对齐特征实现扩散模型测试时调控，在推理时优化相似度势能从纹理贴片级到全局语义多尺度控制生成方向。

### 5. RAE-DiT — Scaling Diffusion with Representation Autoencoders
- **arXiv:** 2601.16208 | **年份:** 2026 | **会议:** arXiv（1月）
- **项目页:** https://rae-dit.github.io/scale-rae/
- **核心贡献:** 用SigLIP-2语义隐空间替代VAE隐空间，RAE-based DiT在0.5B–9.8B参数规模一致超越VAE-based DiT，收敛更快且生成质量更高，从系统层面实证了CNLSA假设。

---

## 值得关注的 honorable mentions

- **ODC — Orthogonal Drift Correction**（ICLR 2026 under review，暂无公开代码）
- **PS-VAE**（arXiv 2512.17909，jshilong.github.io/PS-VAE-PAGE/，处理表示自编码器的off-manifold漂移）
- **DLFR-Gen**（ICCV 2025，无公开代码，已排除）
