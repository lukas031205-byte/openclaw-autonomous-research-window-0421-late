# Scout Results — 0426-PM (Apr 26, 2026)

## Apr 26 arXiv cs.CV (100篇扫描)

### 直接相关（VAE/diffusion/video latent）
无新发现。今日列表无直接涉及 VAE latent space 或 video diffusion semantic drift 的论文。

### 间接相关 / 值得记录

**1. Seeing Fast and Slow: Learning the Flow of Time in Videos**
- arXiv: 2604.21931
- Authors: (待补充)
- 摘要: 研究视频中时间流感知与控制，自监督学习速度变化检测和播放速度估计；提出最大慢动作视频数据集；速度条件视频生成和时间超分辨率。
- 相关性: 时间推理与视频生成控制，与 TrACE-Video 的 frame-level semantic consistency 方向不同但相邻
- 代码: 未知

**2. Vista4D: Video Reshooting with 4D Point Clouds**
- arXiv: 2604.21915
- Authors: Kuan Heng Lin, Zhizheng Liu, et al.
- 摘要: 基于 4D 点云的视频重拍框架，对输入视频和目标相机进行对齐
- 相关性: 视频生成+3D，与我们的 video latent research 正交
- 代码: 未知

**3. Grounding Video Reasoning in Physical Signals**
- arXiv: 2604.21873
- 摘要: V-STaR 扩展到 4 个视频源、6 个物理领域，物理视频理解 benchmark
- 相关性: 视频推理，与 TrACE-Video 的 semantic drift 正交
- 代码: 未知

**4. Context Unrolling in Omni Models**
- arXiv: 2604.21921
- Authors: Ceyuan Yang, Zhijie Lin, et al. (大量作者)
- 相关性: omni model，可能涉及 video+text+image 多模态
- 代码: 未知

### 已知论文状态确认（60天窗口）

| 论文 | arXiv | 状态 | 代码 |
|------|-------|------|------|
| Re2Pix | 2604.11707 | 代码 NOT released (确认 Apr 26) | 无 |
| LumiVid | 2604.11788 | 项目页 HDR-LumiVid.github.io | 无代码 |
| DOCO | 2604.21772 | CVPR 2026, code released | github.com/xxx |
| DualSplat | 2604.21631 | CVPR 2026 | 未知 |
| Reshoot-Anything | 2604.21776 | 视频时间一致性 | 未知 |
| Hybrid Forcing | 2604.10103 | streaming SVG, 29.5 FPS | leeuibin/hybrid-forcing |
| StructMem | 2604.21748 | ACL 2026, 代码 released | 已知 |

## 结论
Apr 26 无直接相关新论文。60天窗口内最重要的仍然是：
- DOCO (CVPR 2026) — TTA + structural preservation
- LumiVid — LogC3 VAE latent fix（治疗路径）
- Hybrid Forcing — streaming SVG baseline
