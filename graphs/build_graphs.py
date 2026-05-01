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

# ─────────────────────────────────────────
# GRAF 1: CO-CHANGE GRAPH
# ─────────────────────────────────────────
def build_cochange_graph(commits):
    """
    Aynı committe birlikte değişen dosyalar arasına kenar koy.
    Kenar ağırlığı = kaç kez birlikte değiştiler.
    """
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


# ─────────────────────────────────────────
# GRAF 2: SEMANTIC SIMILARITY GRAPH
# ─────────────────────────────────────────
def build_semantic_graph(file_stats, threshold=0.25):
    """
    Her dosyanın commit mesajlarını TF-IDF ile vektörleştir.
    Cosine similarity > threshold olan çiftler arasına kenar koy.
    """
    G = nx.Graph()

    # Yeterli mesajı olan dosyaları al
    modules = []
    texts = []
    for fname, stats in file_stats.items():
        messages = stats.get("commit_messages", [])
        if len(messages) < 2:  # çok az veri olan dosyaları atla
            continue
        combined_text = " ".join(messages)
        modules.append(fname)
        texts.append(combined_text)

    if len(modules) < 2:
        print("    Semantic graph için yeterli veri yok.")
        return G

    # TF-IDF vektörleştirme
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=300,
        ngram_range=(1, 2),
        min_df=2  # en az 2 dosyada geçen terimler
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError as e:
        print(f"    TF-IDF hatası: {e}")
        return G

    sim_matrix = cosine_similarity(tfidf_matrix)

    # Düğümleri ekle
    for m in modules:
        G.add_node(m)

    # Kenarları ekle
    edge_count = 0
    for i in range(len(modules)):
        for j in range(i + 1, len(modules)):
            sim = float(sim_matrix[i][j])
            if sim > threshold:
                G.add_edge(modules[i], modules[j], weight=sim)
                edge_count += 1

    print(f"    Semantic graph: {len(modules)} düğüm, {edge_count} kenar (threshold={threshold})")
    return G


# ─────────────────────────────────────────
# GRAF 3: DEPENDENCY GRAPH (import analizi)
# ─────────────────────────────────────────
def build_dependency_graph(file_stats):
    """
    Elimizdeki dosya listesinden basit bir dependency graph çıkar.
    Not: Gerçek import analizi için kaynak kodu gerekir.
    Burada co-change verisinden proxy dependency çıkarıyoruz —
    sık birlikte değişen ve aynı dizindeki dosyalar muhtemelen bağımlıdır.
    """
    G = nx.DiGraph()

    all_files = list(file_stats.keys())

    # Tüm dosyaları düğüm olarak ekle
    for f in all_files:
        G.add_node(f)

    # Dizin bazlı bağımlılık: aynı klasördeki dosyalar birbirini import ediyor olabilir
    # co_changed_with verisini directed proxy olarak kullan
    for fname, stats in file_stats.items():
        co_changed = stats.get("co_changed_with", {})
        for other_file, count in co_changed.items():
            if other_file in all_files and count >= 3:
                # En az 3 kez birlikte değişmişse directed kenar ekle
                # Daha çok değişen dosya → daha az değişene bağımlı gibi davran
                src_changes = file_stats[fname]["total_commits"]
                tgt_changes = file_stats.get(other_file, {}).get("total_commits", 0)
                if src_changes >= tgt_changes:
                    G.add_edge(fname, other_file, weight=count)
                else:
                    G.add_edge(other_file, fname, weight=count)

    return G


# ─────────────────────────────────────────
# ANA FONKSİYON
# ─────────────────────────────────────────
def build_all_graphs(owner, repo):
    print(f"\n{owner}/{repo} — graflar inşa ediliyor...")

    # Temizlenmiş veriyi yükle
    commits_file = f"data/processed/{owner}_{repo}_commits_clean.json"
    stats_file = f"data/processed/{owner}_{repo}_file_stats.json"

    with open(commits_file, "r", encoding="utf-8") as f:
        commits = json.load(f)
    with open(stats_file, "r", encoding="utf-8") as f:
        file_stats = json.load(f)

    # ── Co-change graph
    G_cochange = build_cochange_graph(commits)
    print(f"  Co-change graph:   {G_cochange.number_of_nodes()} düğüm, "
          f"{G_cochange.number_of_edges()} kenar")

    # ── Semantic graph
    print("  Semantic graph hesaplanıyor...")
    G_semantic = build_semantic_graph(file_stats)

    # ── Dependency graph
    G_dependency = build_dependency_graph(file_stats)
    print(f"  Dependency graph:  {G_dependency.number_of_nodes()} düğüm, "
          f"{G_dependency.number_of_edges()} kenar")

    # ── Kaydet
    os.makedirs("graphs", exist_ok=True)
    prefix = f"graphs/{owner}_{repo}"

    with open(f"{prefix}_cochange.pkl", "wb") as f:
        pickle.dump(G_cochange, f)
    with open(f"{prefix}_semantic.pkl", "wb") as f:
        pickle.dump(G_semantic, f)
    with open(f"{prefix}_dependency.pkl", "wb") as f:
        pickle.dump(G_dependency, f)

    print(f"  Graflar kaydedildi → graphs/{owner}_{repo}_*.pkl")

    return G_cochange, G_semantic, G_dependency


if __name__ == "__main__":
    for owner, repo in REPOS:
        build_all_graphs(owner, repo)
    print("\nTüm graflar başarıyla oluşturuldu!")