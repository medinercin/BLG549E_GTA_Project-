import json
import os
import csv
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    precision_recall_curve, roc_curve,
)
import numpy as np

REPOS = [
    ("psf", "requests"),
    ("pallets", "flask"),
    ("scikit-learn", "scikit-learn"),
]

BASELINES = ["pagerank", "betweenness", "cochange_degree", "semantic_degree", "bug_keyword_density"]


def evaluate_signal(y_true, y_score, label, k=10):
    y_true_arr = np.array(y_true)
    y_score_arr = np.array(y_score)

    if len(set(y_true_arr)) < 2:
        return None

    auc_roc = roc_auc_score(y_true_arr, y_score_arr)
    auc_pr = average_precision_score(y_true_arr, y_score_arr)

    top_k_idx = np.argsort(y_score_arr)[::-1][:k]
    y_pred_k = np.zeros(len(y_true_arr), dtype=int)
    y_pred_k[top_k_idx] = 1

    prec_k = precision_score(y_true_arr, y_pred_k, zero_division=0)
    rec_k = recall_score(y_true_arr, y_pred_k, zero_division=0)
    f1_k = f1_score(y_true_arr, y_pred_k, zero_division=0)

    fpr, tpr, _ = roc_curve(y_true_arr, y_score_arr)
    pr_prec, pr_rec, _ = precision_recall_curve(y_true_arr, y_score_arr)

    return {
        "label": label,
        "auc_roc": round(float(auc_roc), 4),
        "auc_pr": round(float(auc_pr), 4),
        f"precision@{k}": round(float(prec_k), 4),
        f"recall@{k}": round(float(rec_k), 4),
        f"f1@{k}": round(float(f1_k), 4),
        "roc_curve": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
        "pr_curve": {"precision": pr_prec.tolist(), "recall": pr_rec.tolist()},
    }


def evaluate_repo(owner, repo, k=10):
    print(f"\n{owner}/{repo} - degerlendirme (TEST seti uzerinde)...")

    risk_file = f"analysis/results/{owner}_{repo}_risk_scores.json"
    with open(risk_file, "r", encoding="utf-8") as f:
        risk_scores = json.load(f)

    # Sadece test setinde olan dosyalari degerlendir
    test_nodes = [n for n, v in risk_scores.items() if v.get("in_test_set", False)]

    if len(test_nodes) < 5:
        print(f"  Test setinde yeterli dosya yok ({len(test_nodes)})")
        return []

    y_true = [int(risk_scores[n]["is_buggy_test"]) for n in test_nodes]

    if len(set(y_true)) < 2:
        print(f"  Test setinde tek sinif var, degerlendirme yapilamaz")
        return []

    print(f"  Test: {len(test_nodes)} dosya, {sum(y_true)} buggy, {len(test_nodes) - sum(y_true)} clean")

    results = []

    # Composite model
    y_composite = [risk_scores[n]["risk_score"] for n in test_nodes]
    res = evaluate_signal(y_true, y_composite, "composite", k=k)
    if res:
        results.append(res)

    # Baselines
    for sig in BASELINES:
        y_sig = [risk_scores[n].get(sig, 0.0) for n in test_nodes]
        res = evaluate_signal(y_true, y_sig, sig, k=k)
        if res:
            results.append(res)

    os.makedirs("analysis/results", exist_ok=True)
    out_file = f"analysis/results/{owner}_{repo}_evaluation.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"  {'Model':<22} {'AUC-ROC':>8} {'AUC-PR':>8} {'P@10':>8} {'R@10':>8} {'F1@10':>8}")
    print(f"  {'-'*64}")
    for r in results:
        print(f"  {r['label']:<22} {r['auc_roc']:>8.4f} {r['auc_pr']:>8.4f} "
              f"{r[f'precision@{k}']:>8.4f} {r[f'recall@{k}']:>8.4f} {r[f'f1@{k}']:>8.4f}")

    print(f"  Kaydedildi -> {out_file}")
    return results


def save_summary_csv(all_results):
    os.makedirs("analysis/results", exist_ok=True)
    out = "analysis/results/evaluation_summary.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["repo", "model", "auc_roc", "auc_pr", "precision@10", "recall@10", "f1@10"])
        for repo_name, results in all_results.items():
            for r in results:
                writer.writerow([
                    repo_name, r["label"], r["auc_roc"], r["auc_pr"],
                    r["precision@10"], r["recall@10"], r["f1@10"],
                ])
    print(f"\nOzet tablo kaydedildi -> {out}")


if __name__ == "__main__":
    all_results = {}
    for owner, repo in REPOS:
        results = evaluate_repo(owner, repo, k=10)
        all_results[f"{owner}/{repo}"] = results
    save_summary_csv(all_results)
    print("\nDegerlendirme tamamlandi!")
