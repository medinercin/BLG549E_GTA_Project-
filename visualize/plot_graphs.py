import json
import pickle
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

REPOS = [
    ("psf", "requests"),
    ("pallets", "flask"),
    ("scikit-learn", "scikit-learn"),
]

os.makedirs("visualize/figures", exist_ok=True)
STYLE = {
    "buggy_color":    "#e05c5c",
    "clean_color":    "#5b8dd9",
    "accent":         "#f0a500",
    "bg":             "#f9f9f9",
    "font":           "DejaVu Sans",
}
plt.rcParams.update({
    "font.family": STYLE["font"],
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": STYLE["bg"],
    "axes.facecolor": STYLE["bg"],
})


# ── Figure 1: Risk score distribution (bar chart, top-N files per repo)
def plot_risk_distributions():
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Top-20 Highest-Risk Files per Repository", fontsize=14, fontweight="bold", y=1.02)

    for ax, (owner, repo) in zip(axes, REPOS):
        with open(f"analysis/results/{owner}_{repo}_risk_scores.json") as f:
            scores = json.load(f)

        items = sorted(scores.items(), key=lambda x: x[1]["risk_score"], reverse=True)[:20]
        labels = [os.path.basename(k) for k, _ in items]
        values = [v["risk_score"] for _, v in items]
        colors = [STYLE["buggy_color"] if v.get("is_buggy_train", v.get("is_buggy", False)) else STYLE["clean_color"] for _, v in items]

        bars = ax.barh(range(len(labels)), values[::-1], color=colors[::-1], edgecolor="white", linewidth=0.4)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels[::-1], fontsize=7)
        ax.set_xlabel("Composite Risk Score", fontsize=9)
        ax.set_title(f"{owner}/{repo}", fontsize=11, fontweight="bold")
        ax.tick_params(axis="x", labelsize=8)

    buggy_patch = mpatches.Patch(color=STYLE["buggy_color"], label="Buggy")
    clean_patch = mpatches.Patch(color=STYLE["clean_color"], label="Clean")
    fig.legend(handles=[buggy_patch, clean_patch], loc="lower center",
               ncol=2, fontsize=9, frameon=False, bbox_to_anchor=(0.5, -0.04))

    fig.tight_layout()
    fig.savefig("visualize/figures/fig1_risk_distribution.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("  fig1_risk_distribution.png")


# ── Figure 2: ROC curves — composite vs baselines (one panel per repo)
def plot_roc_curves():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    fig.suptitle("ROC Curves: Composite Model vs Single-Signal Baselines", fontsize=13, fontweight="bold")

    line_styles = {
        "composite":          ("-",  2.0, STYLE["accent"]),
        "pagerank":           ("--", 1.2, "#7e7e7e"),
        "betweenness":        ("-.", 1.2, "#7e7e7e"),
        "cochange_degree":    (":",  1.2, "#aaaaaa"),
        "semantic_degree":    ("--", 1.0, "#bbbbbb"),
        "bug_keyword_density":("-.", 1.2, "#cc6666"),
    }

    for ax, (owner, repo) in zip(axes, REPOS):
        with open(f"analysis/results/{owner}_{repo}_evaluation.json") as f:
            evals = json.load(f)

        for ev in evals:
            ls, lw, col = line_styles.get(ev["label"], ("-", 1.0, "gray"))
            fpr = ev["roc_curve"]["fpr"]
            tpr = ev["roc_curve"]["tpr"]
            auc = ev["auc_roc"]
            ax.plot(fpr, tpr, ls=ls, lw=lw, color=col,
                    label=f"{ev['label']} ({auc:.2f})")

        ax.plot([0, 1], [0, 1], "k--", lw=0.7, alpha=0.4)
        ax.set_xlabel("False Positive Rate", fontsize=9)
        ax.set_ylabel("True Positive Rate", fontsize=9)
        ax.set_title(f"{owner}/{repo}", fontsize=10, fontweight="bold")
        ax.legend(fontsize=7, frameon=False)
        ax.tick_params(labelsize=8)

    fig.tight_layout()
    fig.savefig("visualize/figures/fig2_roc_curves.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("  fig2_roc_curves.png")


# ── Figure 3: Precision-Recall curves
def plot_pr_curves():
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    fig.suptitle("Precision–Recall Curves: Composite Model vs Single-Signal Baselines",
                 fontsize=13, fontweight="bold")

    line_styles = {
        "composite":       ("-",  2.0, STYLE["accent"]),
        "pagerank":        ("--", 1.2, "#7e7e7e"),
        "betweenness":     ("-.", 1.2, "#7e7e7e"),
        "cochange_degree": (":",  1.2, "#aaaaaa"),
        "semantic_degree": ("--", 1.0, "#bbbbbb"),
    }

    for ax, (owner, repo) in zip(axes, REPOS):
        with open(f"analysis/results/{owner}_{repo}_evaluation.json") as f:
            evals = json.load(f)

        for ev in evals:
            ls, lw, col = line_styles.get(ev["label"], ("-", 1.0, "gray"))
            prec = ev["pr_curve"]["precision"]
            rec  = ev["pr_curve"]["recall"]
            ap   = ev["auc_pr"]
            ax.plot(rec, prec, ls=ls, lw=lw, color=col,
                    label=f"{ev['label']} (AP={ap:.2f})")

        ax.set_xlabel("Recall", fontsize=9)
        ax.set_ylabel("Precision", fontsize=9)
        ax.set_title(f"{owner}/{repo}", fontsize=10, fontweight="bold")
        ax.legend(fontsize=7, frameon=False)
        ax.tick_params(labelsize=8)

    fig.tight_layout()
    fig.savefig("visualize/figures/fig3_pr_curves.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("  fig3_pr_curves.png")


# ── Figure 4: Metric comparison bar chart (AUC-ROC across models & repos)
def plot_metric_comparison():
    import csv
    rows = []
    with open("analysis/results/evaluation_summary.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    models = ["composite", "pagerank", "betweenness", "cochange_degree", "semantic_degree", "bug_keyword_density"]
    repo_labels = ["requests", "flask", "scikit-learn"]
    x = np.arange(len(repo_labels))
    width = 0.15
    colors = [STYLE["accent"], "#5b8dd9", "#aabbdd", "#88ccbb", "#ddaaaa", "#cc6666"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, metric, title in zip(axes,
                                  ["auc_roc", "f1@10"],
                                  ["AUC-ROC by Model and Repository",
                                   "F1@10 by Model and Repository"]):
        for i, model in enumerate(models):
            vals = []
            for repo_lbl in repo_labels:
                matched = [r for r in rows if r["model"] == model and repo_lbl in r["repo"]]
                vals.append(float(matched[0][metric]) if matched else 0.0)
            offset = (i - len(models) / 2 + 0.5) * width
            bars = ax.bar(x + offset, vals, width * 0.92, label=model,
                          color=colors[i], edgecolor="white", linewidth=0.4)

        ax.set_xticks(x)
        ax.set_xticklabels(repo_labels, fontsize=10)
        ax.set_ylabel(metric.upper(), fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.legend(fontsize=8, frameon=False)
        ax.tick_params(labelsize=9)
        ax.set_ylim(0, 1.05)

    fig.tight_layout()
    fig.savefig("visualize/figures/fig4_metric_comparison.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("  fig4_metric_comparison.png")


# ── Figure 5: Co-change graph visualization (spring layout, colored by buggy)
def plot_cochange_graph(owner, repo, max_nodes=80):
    with open(f"graphs/{owner}_{repo}_cochange.pkl", "rb") as f:
        G = pickle.load(f)
    with open(f"data/processed/{owner}_{repo}_file_stats.json") as f:
        file_stats = json.load(f)

    # Yönetilebilir boyut için en bağlantılı düğümleri al
    if G.number_of_nodes() > max_nodes:
        top_nodes = sorted(G.degree(weight="weight"), key=lambda x: x[1], reverse=True)[:max_nodes]
        G = G.subgraph([n for n, _ in top_nodes]).copy()

    node_colors = [
        STYLE["buggy_color"] if file_stats.get(n, {}).get("is_buggy", file_stats.get(n, {}).get("is_buggy_train", False)) else STYLE["clean_color"]
        for n in G.nodes()
    ]
    weights = [G[u][v].get("weight", 1) for u, v in G.edges()]
    max_w = max(weights) if weights else 1
    edge_widths = [0.3 + 1.5 * (w / max_w) for w in weights]
    edge_alphas = [0.2 + 0.5 * (w / max_w) for w in weights]

    fig, ax = plt.subplots(figsize=(10, 8))
    pos = nx.spring_layout(G, weight="weight", seed=42, k=1.2)

    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.25,
                           edge_color="#999999", ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=60,
                           alpha=0.92, ax=ax)

    # Sadece yüksek dereceli düğümlere etiket
    top10 = sorted(G.degree(weight="weight"), key=lambda x: x[1], reverse=True)[:10]
    labels = {n: os.path.basename(n) for n, _ in top10}
    nx.draw_networkx_labels(G, pos, labels, font_size=6, ax=ax)

    buggy_patch = mpatches.Patch(color=STYLE["buggy_color"], label="Buggy")
    clean_patch  = mpatches.Patch(color=STYLE["clean_color"],  label="Clean")
    ax.legend(handles=[buggy_patch, clean_patch], fontsize=9, frameon=False)
    ax.set_title(f"Co-change Graph — {owner}/{repo}\n(top {G.number_of_nodes()} nodes by weighted degree)",
                 fontsize=11, fontweight="bold")
    ax.axis("off")

    fig.tight_layout()
    fname = f"visualize/figures/fig5_{owner}_{repo}_cochange_graph.png"
    fig.savefig(fname, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"  {os.path.basename(fname)}")


# ── Figure 6: Louvain community visualization (co-change graph)
def plot_community_graph(owner, repo, max_nodes=80):
    with open(f"graphs/{owner}_{repo}_cochange.pkl", "rb") as f:
        G = pickle.load(f)
    with open(f"analysis/results/{owner}_{repo}_centrality.json") as f:
        centrality = json.load(f)

    if G.number_of_nodes() > max_nodes:
        top_nodes = sorted(G.degree(weight="weight"), key=lambda x: x[1], reverse=True)[:max_nodes]
        G = G.subgraph([n for n, _ in top_nodes]).copy()

    community_ids = [centrality.get(n, {}).get("community_id", 0) for n in G.nodes()]
    unique_cids = list(set(community_ids))
    cmap = plt.cm.get_cmap("tab20", len(unique_cids))
    cid_to_color = {cid: cmap(i) for i, cid in enumerate(unique_cids)}
    node_colors = [cid_to_color[c] for c in community_ids]

    fig, ax = plt.subplots(figsize=(10, 8))
    pos = nx.spring_layout(G, weight="weight", seed=42, k=1.2)
    nx.draw_networkx_edges(G, pos, alpha=0.15, edge_color="#aaaaaa", ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=60, alpha=0.9, ax=ax)

    top10 = sorted(G.degree(weight="weight"), key=lambda x: x[1], reverse=True)[:8]
    labels = {n: os.path.basename(n) for n, _ in top10}
    nx.draw_networkx_labels(G, pos, labels, font_size=6, ax=ax)

    ax.set_title(f"Louvain Communities — {owner}/{repo}\n({len(unique_cids)} communities detected)",
                 fontsize=11, fontweight="bold")
    ax.axis("off")
    fig.tight_layout()
    fname = f"visualize/figures/fig6_{owner}_{repo}_communities.png"
    fig.savefig(fname, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"  {os.path.basename(fname)}")


# ── Figure 7: Signal correlation heatmap (per repo)
def plot_signal_heatmap(owner, repo):
    with open(f"analysis/results/{owner}_{repo}_risk_scores.json") as f:
        scores = json.load(f)

    signals = ["pagerank", "betweenness", "cochange_degree", "semantic_degree", "bug_keyword_density", "risk_score"]
    data = np.array([[v.get(s, 0.0) for s in signals] for v in scores.values()])

    corr = np.corrcoef(data.T)

    fig, ax = plt.subplots(figsize=(7, 5.5))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(signals)))
    ax.set_yticks(range(len(signals)))
    labels_clean = ["PageRank", "Betweenness", "Co-change\nDegree", "Semantic\nDegree", "Bug KW\nDensity", "Composite"]
    ax.set_xticklabels(labels_clean, rotation=35, ha="right", fontsize=8)
    ax.set_yticklabels(labels_clean, fontsize=8)

    for i in range(len(signals)):
        for j in range(len(signals)):
            ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center",
                    fontsize=7, color="black" if abs(corr[i, j]) < 0.7 else "white")

    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title(f"Signal Correlation — {owner}/{repo}", fontsize=11, fontweight="bold")
    fig.tight_layout()
    fname = f"visualize/figures/fig7_{owner}_{repo}_signal_corr.png"
    fig.savefig(fname, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"  {os.path.basename(fname)}")


if __name__ == "__main__":
    print("Figürler oluşturuluyor...")

    plot_risk_distributions()
    plot_roc_curves()
    plot_pr_curves()
    plot_metric_comparison()

    for owner, repo in REPOS:
        plot_cochange_graph(owner, repo)
        plot_community_graph(owner, repo)
        plot_signal_heatmap(owner, repo)

    print(f"\nTüm figürler → visualize/figures/")
