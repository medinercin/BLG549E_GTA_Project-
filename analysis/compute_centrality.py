import pickle
import json
import os
import re
import networkx as nx
from networkx.algorithms.community import louvain_communities

REPOS = [
    ("psf", "requests"),
    ("pallets", "flask"),
    ("scikit-learn", "scikit-learn"),
]

BUG_KEYWORDS = [
    r'\bfix\b', r'\bbug\b', r'\bdefect\b', r'\berror\b',
    r'\bcrash\b', r'\bfault\b', r'\bpatch\b',
    r'\bhotfix\b', r'\bresolve\b', r'\bcorrect\b', r'\bregression\b',
    r'\bbroken\b', r'\bfail\b', r'\bwrong\b', r'\binvalid\b',
]


def weighted_degree(G, node):
    return sum(d.get("weight", 1) for _, _, d in G.edges(node, data=True))


def compute_bug_keyword_density(file_stats):
    densities = {}
    for fname, stats in file_stats.items():
        messages = stats.get("commit_messages", [])
        if not messages:
            densities[fname] = 0.0
            continue
        combined = " ".join(messages).lower()
        words = combined.split()
        if len(words) == 0:
            densities[fname] = 0.0
            continue
        hit_count = sum(
            len(re.findall(kw, combined)) for kw in BUG_KEYWORDS
        )
        densities[fname] = hit_count / len(words)
    return densities


def compute_metrics(owner, repo):
    print(f"\n{owner}/{repo} - metrikler hesaplaniyor...")

    prefix = f"graphs/{owner}_{repo}"
    with open(f"{prefix}_cochange.pkl", "rb") as f:
        G_co = pickle.load(f)
    with open(f"{prefix}_semantic.pkl", "rb") as f:
        G_sem = pickle.load(f)
    with open(f"{prefix}_dependency.pkl", "rb") as f:
        G_dep = pickle.load(f)

    stats_file = f"data/processed/{owner}_{repo}_file_stats.json"
    with open(stats_file, "r", encoding="utf-8") as f:
        file_stats = json.load(f)

    all_nodes = set(G_co.nodes()) | set(G_sem.nodes()) | set(G_dep.nodes())
    metrics = {n: {} for n in all_nodes}

    # ── Dependency graph: betweenness centrality & PageRank
    print("  Betweenness centrality (dependency)...")
    bc = nx.betweenness_centrality(G_dep, weight="weight", normalized=True)
    pr = nx.pagerank(G_dep, weight="weight", alpha=0.85)
    for n in all_nodes:
        metrics[n]["betweenness"] = bc.get(n, 0.0)
        metrics[n]["pagerank"] = pr.get(n, 0.0)

    # ── Co-change graph: weighted degree centrality & Louvain community
    print("  Weighted degree (co-change)...")
    total_weight_co = sum(d.get("weight", 1) for _, _, d in G_co.edges(data=True)) or 1
    for n in all_nodes:
        if G_co.has_node(n):
            metrics[n]["cochange_degree"] = weighted_degree(G_co, n) / total_weight_co
        else:
            metrics[n]["cochange_degree"] = 0.0

    print("  Louvain community detection (co-change)...")
    if G_co.number_of_edges() > 0:
        communities = louvain_communities(G_co, weight="weight", seed=42)
        node_community = {}
        for cid, members in enumerate(communities):
            for m in members:
                node_community[m] = cid
        community_sizes = {cid: len(members) for cid, members in enumerate(communities)}
    else:
        node_community = {}
        community_sizes = {}

    for n in all_nodes:
        cid = node_community.get(n, -1)
        metrics[n]["community_id"] = cid
        metrics[n]["community_size"] = community_sizes.get(cid, 0)

    # ── Semantic graph: weighted degree centrality
    print("  Weighted degree (semantic)...")
    total_weight_sem = sum(d.get("weight", 1) for _, _, d in G_sem.edges(data=True)) or 1
    for n in all_nodes:
        if G_sem.has_node(n):
            metrics[n]["semantic_degree"] = weighted_degree(G_sem, n) / total_weight_sem
        else:
            metrics[n]["semantic_degree"] = 0.0

    # ── NLP: bug keyword density from commit messages
    print("  Bug keyword density (NLP)...")
    bkd = compute_bug_keyword_density(file_stats)
    for n in all_nodes:
        metrics[n]["bug_keyword_density"] = bkd.get(n, 0.0)

    # ── Save
    os.makedirs("analysis/results", exist_ok=True)
    out_file = f"analysis/results/{owner}_{repo}_centrality.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    n_communities = len(set(v for v in node_community.values()))
    print(f"  {len(metrics)} dugum, {n_communities} Louvain toplulugu")
    print(f"  Kaydedildi -> {out_file}")
    return metrics


if __name__ == "__main__":
    for owner, repo in REPOS:
        compute_metrics(owner, repo)
    print("\nTüm metrikler hesaplandı!")
