# Arxiv Daily - March 10, 2026

## Topic 1: LLM (Large Language Models)

### 论文1: Steering Large Language Models via In-Context One-step Learning Dynamics
- **作者:** Kartik Sharma et al.
- **摘要:** Activation steering methods enable inference-time control of large language model (LLM) behavior without retraining, but current approaches face a fundamental trade-off: sample-efficient methods suboptimally capture steering signals from labeled examples, while methods that better extract these signals require hundreds to thousands of examples. We introduce COLD-Steer, a training-free framework that steers LLM activations by approximating the representational changes that would result from gradient descent on in-context examples. Our key insight is that the effect of fine-tuning on a small set of examples can be efficiently approximated at inference time without actual parameter updates. We formalize this through two complementary approaches: (i) a unit kernel approximation method that updates the activations directly using gradients with respect to them, normalized across examples, and (ii) a finite-difference approximation requiring only two forward passes regardless of example count. Experiments across a variety of steering tasks and benchmarks demonstrate that COLD-Steer achieves upto 95% steering effectiveness while using 50 times fewer samples compared to the best baseline.
- **链接:** https://arxiv.org/abs/2603.06495
- **备注:** ICLR 2026

### 论文2: Multimodal Large Language Models as Image Classifiers
- **作者:** Nikita Kisel et al.
- **摘要:** Multimodal Large Language Models (MLLM) classification performance depends critically on evaluation protocol and ground truth quality. Studies comparing MLLMs with supervised and vision-language models report conflicting conclusions, and we show these conflicts stem from protocols that either inflate or underestimate performance. Across the most common evaluation protocols, we identify and fix key issues: model outputs that fall outside the provided class list and are discarded, inflated results from weak multiple-choice distractors, and an open-world setting that underperforms only due to poor output mapping. We additionally quantify the impact of commonly overlooked design choices - batch size, image ordering, and text encoder selection - showing they substantially affect accuracy. Evaluating on ReGT, our multilabel reannotation of 625 ImageNet-1k classes, reveals that MLLMs benefit most from corrected labels (up to +10.8%), substantially narrowing the perceived gap with supervised models.
- **链接:** https://arxiv.org/abs/2603.06578

---

## Topic 2: 3D Reconstruction & Autonomous Driving

### 论文1: Next-step Open-Vocabulary Autoregression for 3D Multi-Object Tracking in Autonomous Driving (NOVA)
- **作者:** Kailun Yang et al.
- **摘要:** Generalizing across unknown targets is critical for open-world perception, yet existing 3D Multi-Object Tracking (3D MOT) pipelines remain limited by closed-set assumptions and "semantic-blind" heuristics. To address this, we propose Next-step Open-Vocabulary Autoregression (NOVA), an innovative paradigm that shifts 3D tracking from traditional fragmented distance-based matching toward generative spatio-temporal semantic modeling. NOVA reformulates 3D trajectories as structured spatio-temporal semantic sequences, enabling the simultaneous encoding of physical motion continuity and deep linguistic priors. By leveraging the autoregressive capabilities of Large Language Models (LLMs), we transform the tracking task into a principled process of next-step sequence completion. This mechanism allows the model to explicitly utilize the hierarchical structure of language space to resolve fine-grained semantic ambiguities and maintain identity consistency across complex long-range sequences through high-level commonsense reasoning.
- **链接:** https://arxiv.org/abs/2603.06254

### 论文2: DeepSight - Bridging Depth Maps and Language with a Depth-Driven Multimodal Model
- **作者:** Hao Yang et al.
- **摘要:** Multimodal large language models (MLLMs) have achieved impressive performance across various tasks such as image captioning and visual question answer(VQA); however, they often struggle to accurately interpret depth information inherent in visual data. In this work, we introduce DeepSight, the first dedicated depth MLLM designed to enhance three-dimensional scene understanding. Unlike conventional methods that align RGB image encodings with text, our approach takes advantage of the unique characteristics of depth images: single-channel grayscale images where the pixel values directly reflect depth cues to improve spatial reasoning. To address challenges associated with limited depth data and the inadequacy of simple channel replication, we construct a novel depth image-text pair dataset and a depth instruction dataset.
- **链接:** https://arxiv.org/abs/2603.06090

---

## Topic 3: Vision Foundation Models

### 论文1: Knowledge-Anchored Manifold Transport for Cross-Modal Prompt Learning in Medical Imaging (K-MaT)
- **作者:** Jiajun Zeng et al.
- **摘要:** Large-scale biomedical vision-language models (VLMs) adapted on high-end imaging (e.g., CT) often fail to transfer to frontline low-end modalities (e.g., radiography), collapsing into modality-specific shortcuts. We propose K-MaT (Knowledge-Anchored Manifold Transport), a prompt-learning framework that transfers decision structures to low-end modalities without requiring low-end training images. K-MaT factorizes prompts, anchors them to clinical text descriptions, and aligns the low-end prompt manifold to the visually-grounded high-end space using Fused Gromov-Wasserstein optimal transport. We evaluate K-MaT on four cross-modal benchmarks, including dermoscopy, mammography to ultrasound, and CT to chest X-ray. K-MaT achieves state-of-the-art results, improving the average harmonic mean of accuracy to 44.1% (from BiomedCoOp's 42.0%) and macro-F1 to 36.2%.
- **链接:** https://arxiv.org/abs/2603.06340
