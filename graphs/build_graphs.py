import json
import os
import networkx as nx
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

REPOS = [
    ("psf", "requests"),
    ("pallets", "flask"),
    ("scikit-learn", "scikit-learn")
]


def build_cochange_graph(commits):
    G = nx.Graph()
    from itertools import combinations

    for commit in commits:
        files = [f["filename"] for f in commit["files"]]
        if len(files) < 2:
            continue
        for f1, f2 in combinations(files, 2):
            if G.has_edge(f1, f2):
                G[f1][f2]["weight"] += 1
            else:
                G.add_edge(f1, f2, weight=1)

    return G


def build_semantic_graph(file_stats, threshold=0.25):
    G = nx.Graph()

    modules = []
    texts = []
    for fname, stats in file_stats.items():
        messages = stats.get("commit_messages", [])
        if len(messages) < 2:
            continue
        combined_text = " ".join(messages)
        modules.append(fname)
        texts.append(combined_text)

    if len(modules) < 2:
        print("    Semantic graph icin yeterli veri yok.")
        return G

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=300,
        ngram_range=(1, 2),
        min_df=2
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError as e:
        print(f"    TF-IDF hatasi: {e}")
        return G

    sim_matrix = cosine_similarity(tfidf_matrix)

    for m in modules:
        G.add_node(m)

    edge_count = 0
    for i in range(len(modules)):
        for j in range(i + 1, len(modules)):
            sim = float(sim_matrix[i][j])
            if sim > threshold:
                G.add_edge(modules[i], modules[j], weight=sim)
                edge_count += 1

    print(f"    Semantic graph: {len(modules)} dugum, {edge_count} kenar (threshold={threshold})")
    return G


def build_all_graphs(owner, repo):
    print(f"\n{owner}/{repo} - graflar insa ediliyor (train verisi)...")

    # Train verisini kullan (temporal split)
    train_commits_file = f"data/processed/{owner}_{repo}_train_commits.json"
    stats_file = f"data/processed/{owner}_{repo}_file_stats.json"

    with open(train_commits_file, "r", encoding="utf-8") as f:
        commits = json.load(f)
    with open(stats_file, "r", encoding="utf-8") as f:
        file_stats = json.load(f)

    # Co-change graph (train commits)
    G_cochange = build_cochange_graph(commits)
    print(f"  Co-change graph:   {G_cochange.number_of_nodes()} dugum, "
          f"{G_cochange.number_of_edges()} kenar")

    # Semantic graph (train commit messages)
    print("  Semantic graph hesaplaniyor...")
    G_semantic = build_semantic_graph(file_stats)

    # Dependency graph: AST-based (build_dependency.py ile ayri olusturuldu)
    dep_file = f"graphs/{owner}_{repo}_dependency.pkl"
    with open(dep_file, "rb") as f:
        G_dependency = pickle.load(f)
    print(f"  Dependency graph (AST): {G_dependency.number_of_nodes()} dugum, "
          f"{G_dependency.number_of_edges()} kenar")

    # Co-change ve semantic graflari kaydet
    os.makedirs("graphs", exist_ok=True)
    prefix = f"graphs/{owner}_{repo}"

    with open(f"{prefix}_cochange.pkl", "wb") as f:
        pickle.dump(G_cochange, f)
    with open(f"{prefix}_semantic.pkl", "wb") as f:
        pickle.dump(G_semantic, f)

    print(f"  Graflar kaydedildi")


if __name__ == "__main__":
    for owner, repo in REPOS:
        build_all_graphs(owner, repo)
    print("\nTum graflar olusturuldu!")
