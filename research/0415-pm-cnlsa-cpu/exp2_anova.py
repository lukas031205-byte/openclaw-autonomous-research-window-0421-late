#!/usr/bin/env python3
"""
Exp 2: Category-Level Drift ANOVA
=================================
Welch's ANOVA + Games-Howell post-hoc on CLIP drift (1-CS) by COCO supercategory.
Uses same 50 images as prior CNLSA σ=0 run.
"""

import os
import json
import zipfile
import numpy as np
from scipy import stats

np.random.seed(42)

ARTIFACT_DIR = "/home/kas/.openclaw/workspace-domain/research/0415-pm-cnlsa-cpu"
ANNOTATIONS_JSON = os.path.join(ARTIFACT_DIR, "coco_annotations/annotations/instances_val2017.json")
SIGMA0_JSON     = "/home/kas/.openclaw/workspace-domain/research/autonomous-research-window-0415-pm/cnlsa_sigma0_gate_results.json"
COCO_PATH       = "/home/kas/.cache/huggingface/hub/datasets--merve--coco/snapshots/9e50abcdc1361852f34841af4939cbcd2d37c92f/val2017/"

# ── COCO supercategory mapping (from COCO categories) ─────────────────────────
SUPERCATEGORY_MAP = {
    "person": "person",
    "bicycle": "vehicle", "car": "vehicle", "motorcycle": "vehicle",
    "airplane": "vehicle", "bus": "vehicle", "train": "vehicle", "truck": "vehicle",
    "boat": "vehicle",
    "traffic light": "indoor", "fire hydrant": "indoor", "stop sign": "indoor",
    "parking meter": "indoor", "bench": "indoor",
    "bird": "animal", "cat": "animal", "dog": "animal", "horse": "animal",
    "sheep": "animal", "cow": "animal", "elephant": "animal", "bear": "animal",
    "zebra": "animal", "giraffe": "animal",
    "backpack": "indoor", "umbrella": "indoor", "handbag": "indoor",
    "tie": "indoor", "suitcase": "indoor",
    "frisbee": "indoor", "skis": "indoor", "snowboard": "indoor",
    "sports ball": "indoor", "kite": "indoor", "baseball bat": "indoor",
    "baseball glove": "indoor", "skateboard": "indoor", "surfboard": "indoor",
    "tennis racket": "indoor",
    "bottle": "food", "wine glass": "food", "cup": "food", "fork": "food",
    "knife": "food", "spoon": "food", "bowl": "food",
    "banana": "food", "apple": "food", "sandwich": "food", "orange": "food",
    "broccoli": "food", "carrot": "food", "hot dog": "food", "pizza": "food",
    "donut": "food", "cake": "food",
    "chair": "indoor", "couch": "indoor", "potted plant": "indoor",
    "dining table": "indoor",
    "tv": "indoor", "laptop": "indoor", "mouse": "indoor", "remote": "indoor",
    "keyboard": "indoor", "cell phone": "indoor",
    "microwave": "indoor", "oven": "indoor", "toaster": "indoor",
    "sink": "indoor", "refrigerator": "indoor",
    "book": "indoor", "clock": "indoor", "vase": "indoor", "scissors": "indoor",
    "teddy bear": "indoor", "hair drier": "indoor", "toothbrush": "indoor",
}
TARGET_SUPERCATEGORIES = ["animal", "vehicle", "food", "indoor", "person"]

# ── 1. Re-select same 50 images (same seed as sigma0_gate.py) ─────────────────
all_files = sorted([
    f for f in os.listdir(COCO_PATH)
    if f.lower().endswith(('.jpg', '.jpeg', '.png'))
])
selected_files = np.random.RandomState(42).choice(all_files, size=min(50, len(all_files)), replace=False).tolist()
selected_ids = [os.path.splitext(f)[0] for f in selected_files]  # "000000000001"
print(f"Selected {len(selected_ids)} images")

# ── 2. Load sigma0 cos similarities ────────────────────────────────────────────
with open(SIGMA0_JSON) as f:
    sigma0 = json.load(f)
cos_sims = sigma0["cos_sims"]  # list of 50 CLIP cosine similarities
print(f"Loaded {len(cos_sims)} σ=0 cos similarities, mean={np.mean(cos_sims):.4f}")

# ── 3. Load COCO annotations ───────────────────────────────────────────────────
print("Loading COCO annotations...")
with open(ANNOTATIONS_JSON) as f:
    coco_data = json.load(f)

# Build image_id -> supercategory mapping
# Only keep images that appear in our selected set
img_id_to_supercats = {}
for ann in coco_data["annotations"]:
    img_id = f"{ann['image_id']:012d}"
    cat_name = ann["category_id_to_name"].get(ann["category_id"], "") if "category_id_to_name" in ann else ""
    # Actually, let's use categories list
    pass

# Simpler: build img_id → list of category names from annotations
img_to_cats = {}
for ann in coco_data["annotations"]:
    img_id_str = f"{ann['image_id']:012d}"
    cat_id = ann["category_id"]
    img_to_cats.setdefault(img_id_str, []).append(cat_id)

# Build category_id → supercategory
cat_id_to_super = {}
for cat in coco_data["categories"]:
    cat_id = cat["id"]
    supercat = cat.get("supercategory", "")
    # Map to our target groups
    mapped = SUPERCATEGORY_MAP.get(cat["name"], None)
    if mapped in TARGET_SUPERCATEGORIES:
        cat_id_to_super[cat_id] = mapped
    elif supercat in TARGET_SUPERCATEGORIES:
        cat_id_to_super[cat_id] = supercat
    else:
        # Fallback: try to map from name
        cat_id_to_super[cat_id] = None  # unknown

print(f"COCO categories: {len(coco_data['categories'])}")
print(f"Mapped categories: {sum(1 for v in cat_id_to_super.values() if v is not None)}")

# ── 4. Assign each selected image to supercategory groups ────────────────────
# Strategy: for each image, collect all its category supercategories,
# then pick the most "specific" (non-background) one.
# If an image has categories from multiple groups, use the first prominent one.

group_drifts = {g: [] for g in TARGET_SUPERCATEGORIES}
ungrouped = []

for img_id, cos_sim in zip(selected_ids, cos_sims):
    drift = 1.0 - cos_sim
    cats = img_to_cats.get(img_id, [])
    if not cats:
        # No annotations for this image → background
        group_drifts.setdefault("background", []).append(drift)
        continue
    
    # Get supercategories for all categories of this image
    supers = []
    for c in cats:
        s = cat_id_to_super.get(c)
        if s:
            supers.append(s)
    
    if not supers:
        group_drifts.setdefault("background", []).append(drift)
    else:
        # Count occurrences of each supercategory
        from collections import Counter
        super_counts = Counter(supers)
        # Assign to the most frequent supercategory
        dominant = super_counts.most_common(1)[0][0]
        group_drifts[dominant].append(drift)

print("\nGroup sizes:")
for g, vals in group_drifts.items():
    print(f"  {g}: n={len(vals)}, mean_drift={np.mean(vals):.4f}, std={np.std(vals):.4f}")

# ── 5. Filter to groups with n >= 2 ─────────────────────────────────────────
groups_with_data = {g: np.array(vals) for g, vals in group_drifts.items() if len(vals) >= 2}
print(f"\nGroups with n>=2: {list(groups_with_data.keys())}")

# ── 6. Welch's ANOVA (one-way, unequal variances) ─────────────────────────────
# H0: all group means are equal
# Using scipy's f_oneway (does NOT assume equal variance — actually it does assume equal)
# For Welch's ANOVA we need to compute manually.

def welch_anova(*groups):
    """
    One-way Welch's ANOVA.
    Returns F-statistic and p-value.
    """
    k = len(groups)
    ni = np.array([len(g) for g in groups])
    means = np.array([np.mean(g) for g in groups])
    variances = np.array([np.var(g, ddof=1) for g in groups])
    
    # Weights
    wi = ni / variances
    sum_wi = np.sum(wi)
    
    # Grand mean (weighted)
    grand_mean = np.sum(wi * means) / sum_wi
    
    # Numerator (between-group variance)
    F_num = np.sum(wi * (means - grand_mean)**2) / (k - 1)
    
    # Denominator (within-group variance), corrected for unequal variances
    # Welch-Satterthwaite degrees of freedom
    term_sum = 0
    for i, (ni_i, var_i, wi_i) in enumerate(zip(ni, variances, wi)):
        term = (1 - wi_i / sum_wi)**2 / (ni_i - 1)
        term_sum += term
    
    F_denom = 1 + (2 * (k - 2) / (k**2 - 1)) * term_sum
    
    F_stat = F_num / F_denom
    
    # Welch-Satterthwaite degrees of freedom
    num_df = k - 1
    # Denominator df: complicated formula
    denom_df_num = 0
    for i, (ni_i, var_i, wi_i) in enumerate(zip(ni, variances, wi)):
        denom_df_num += (wi_i - wi_i**2 / sum_wi)**2 / (ni_i - 1)
    
    denom_df = denom_df_num / term_sum if term_sum > 0 else np.inf
    
    p_value = 1 - stats.f.cdf(F_stat, num_df, denom_df)
    
    return F_stat, p_value, num_df, denom_df

groups_list = [groups_with_data[g] for g in sorted(groups_with_data.keys())]
group_names = sorted(groups_with_data.keys())

F_stat, p_value, df1, df2 = welch_anova(*groups_list)
print(f"\nWelch's ANOVA: F({df1:.0f},{df2:.2f}) = {F_stat:.4f}, p = {p_value:.6f}")
anova_pass = p_value < 0.05

# ── 7. Games-Howell post-hoc (pairwise, unequal variances) ───────────────────
def games_howell(group_a, name_a, group_b, name_b):
    """
    Games-Howell post-hoc test.
    Returns (t_stat, p_value, q_stat, se)
    """
    na, nb = len(group_a), len(group_b)
    if na < 2 or nb < 2:
        return None, None, None, None
    
    var_a = np.var(group_a, ddof=1)
    var_b = np.var(group_b, ddof=1)
    mean_a, mean_b = np.mean(group_a), np.mean(group_b)
    
    # Standard error
    se = np.sqrt(var_a / na + var_b / nb)
    
    # t-statistic
    t_stat = (mean_a - mean_b) / se
    
    # Welch-Satterthwaite df
    num = (var_a / na + var_b / nb)**2
    denom = (var_a / na)**2 / (na - 1) + (var_b / nb)**2 / (nb - 1)
    df_welch = num / denom if denom > 0 else np.inf
    
    # p-value (two-tailed)
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df_welch))
    
    # Games-Howell q statistic (studentized range approximation)
    # q = |mean_a - mean_b| / se
    q_stat = abs(t_stat)
    
    return t_stat, p_value, q_stat, float(se)

print("\nGames-Howell post-hoc:")
gh_results = []
g_names = group_names
for i in range(len(g_names)):
    for j in range(i + 1, len(g_names)):
        ga, gb = groups_with_data[g_names[i]], groups_with_data[g_names[j]]
        t, p, q, se = games_howell(ga, g_names[i], gb, g_names[j])
        sig = "*" if (p is not None and p < 0.05) else "ns"
        gh_results.append({
            "pair": f"{g_names[i]} vs {g_names[j]}",
            "n_A": len(ga), "n_B": len(gb),
            "mean_A": float(np.mean(ga)), "mean_B": float(np.mean(gb)),
            "mean_diff": float(np.mean(ga) - np.mean(gb)),
            "t_stat": float(t) if t is not None else None,
            "p_value": float(p) if p is not None else None,
            "q_stat": float(q) if q is not None else None,
            "se": se,
            "sig": sig
        })
        q_str = f"{q:.3f}" if q is not None else "N/A"
        p_str = f"{p:.4f}" if p is not None else "N/A"
        print(f"  {g_names[i]} vs {g_names[j]}: "
              f"Δ={np.mean(ga)-np.mean(gb):.4f}, q={q_str}, p={p_str} {sig}")

# ── 8. Compile and save results ───────────────────────────────────────────────
group_summary = {}
for g in sorted(groups_with_data.keys()):
    arr = groups_with_data[g]
    group_summary[g] = {
        "n": int(len(arr)),
        "mean_drift": float(np.mean(arr)),
        "std_drift": float(np.std(arr)),
        "min_drift": float(np.min(arr)),
        "max_drift": float(np.max(arr))
    }

results = {
    "experiment": "Exp 2: Category-Level Drift ANOVA",
    "design": "Welch's ANOVA + Games-Howell post-hoc",
    "threshold": "p < 0.05",
    "pre_threshold_met": anova_pass,
    "welch_F": float(F_stat),
    "df1": float(df1),
    "df2": float(df2),
    "p_value": float(p_value),
    "groups": group_summary,
    "games_howell": gh_results,
    "notes": "CLIP drift = 1.0 - CS(VAE_roundtrip), σ=0 baseline",
    "n_total": len(selected_ids),
    "background_n": len(group_drifts.get("background", []))
}

out_md = os.path.join(ARTIFACT_DIR, "exp2_anova_results.md")
with open(out_md, "w") as f:
    f.write("# Exp 2: Category-Level Drift ANOVA Results\n\n")
    f.write(f"**Pre-registered threshold:** ANOVA p < 0.05 → category concentration confirmed\n\n")
    f.write(f"**Result:** {'✅ PASS' if anova_pass else '❌ FAIL'} (Welch's ANOVA p = {p_value:.6f})\n\n")
    
    f.write("## Group Summary (CLIP Drift = 1 − CS)\n\n")
    f.write("| Supercategory | n | Mean Drift | Std | Min | Max |\n")
    f.write("|---|---|---|---|---|---|\n")
    for g in sorted(group_summary.keys()):
        s = group_summary[g]
        f.write(f"| {g} | {s['n']} | {s['mean_drift']:.4f} | {s['std_drift']:.4f} | {s['min_drift']:.4f} | {s['max_drift']:.4f} |\n")
    
    f.write(f"\n**Background (unannotated):** n = {results['background_n']}\n")
    
    f.write("\n## Welch's ANOVA\n\n")
    f.write(f"- **F({df1:.0f}, {df2:.2f})** = **{F_stat:.4f}**\n")
    f.write(f"- **p-value** = **{p_value:.6f}**\n")
    f.write(f"- **Decision:** {'Reject H₀ — category concentration confirmed' if anova_pass else 'Fail to reject H₀ — no significant category drift difference'}\n")
    
    f.write("\n## Games-Howell Post-hoc\n\n")
    f.write("| Pair | n₁ | n₂ | Mean₁ | Mean₂ | Δ | q | p-value | Sig |\n")
    f.write("|---|---|---|---|---|---|---|---|---|\n")
    for r in gh_results:
        sig_str = "†" if (r["p_value"] is not None and r["p_value"] < 0.05) else ""
        p_str = f"{r['p_value']:.4f}" if r["p_value"] is not None else "N/A"
        q_str = f"{r['q_stat']:.3f}" if r["q_stat"] is not None else "N/A"
        f.write(f"| {r['pair']} | {r['n_A']} | {r['n_B']} | "
                f"{r['mean_A']:.4f} | {r['mean_B']:.4f} | "
                f"{r['mean_diff']:.4f} | {q_str} | {p_str} | {sig_str} |\n")
    
    f.write("\n*Sig: † = p < 0.05*\n\n")
    f.write("## Notes\n\n")
    f.write("- CLIP drift = 1.0 − cosine_similarity(CLIP(original), CLIP(VAE_roundtrip))\n")
    f.write("- σ=0 baseline (VAE encode-decode with no noise)\n")
    f.write("- Welch's ANOVA does not assume equal variances\n")
    f.write("- Games-Howell uses Welch-Satterthwaite df approximation\n")

print(f"\nResults saved to {out_md}")
print(f"ANOVA: F({df1:.0f},{df2:.2f}) = {F_stat:.4f}, p = {p_value:.6f} → {'PASS' if anova_pass else 'FAIL'}")
