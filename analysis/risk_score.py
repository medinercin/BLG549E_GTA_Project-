import json
import os
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MinMaxScaler

REPOS = [
    ("psf", "requests"),
    ("pallets", "flask"),
    ("scikit-learn", "scikit-learn"),
]

SIGNAL_NAMES = [
    "pagerank", "betweenness", "cochange_degree",
    "semantic_degree", "bug_keyword_density", "community_size",
]


def compute_risk_scores(owner, repo):
    print(f"\n{owner}/{repo} - risk skorlari hesaplaniyor...")

    centrality_file = f"analysis/results/{owner}_{repo}_centrality.json"
    train_stats_file = f"data/processed/{owner}_{repo}_file_stats.json"
    test_stats_file  = f"data/processed/{owner}_{repo}_test_file_stats.json"

    with open(centrality_file, "r", encoding="utf-8") as f:
        centrality = json.load(f)
    with open(train_stats_file, "r", encoding="utf-8") as f:
        train_stats = json.load(f)
    with open(test_stats_file, "r", encoding="utf-8") as f:
        test_stats = json.load(f)

    all_nodes = list(centrality.keys())

    # Feature matrix
    X_raw = np.array([
        [centrality[n].get(sig, 0.0) for sig in SIGNAL_NAMES]
        for n in all_nodes
    ])

    scaler = MinMaxScaler()
    X = scaler.fit_transform(X_raw)

    # Train labels: buggy in train period
    y_train = np.array([
        int(train_stats.get(n, {}).get("is_buggy", False))
        for n in all_nodes
    ])

    # Test labels: buggy in test period (only files that appear in test)
    y_test = np.array([
        int(test_stats.get(n, {}).get("is_buggy", False))
        for n in all_nodes
    ])

    has_test_data = np.array([n in test_stats for n in all_nodes])

    # Logistic regression on train labels
    if len(set(y_train)) < 2:
        print("  Train set'te tek sinif var, logistic regression uygulanamaz")
        return None

    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )
    model.fit(X, y_train)

    # Learned weights
    coefs = model.coef_[0]
    print("  Ogrenilmis agirliklar (logistic regression):")
    for sig, w in zip(SIGNAL_NAMES, coefs):
        print(f"    {sig:25s} {w:+.4f}")

    # Predicted probabilities as risk score
    probs = model.predict_proba(X)[:, 1]

    # Build output
    scores = {}
    for i, node in enumerate(all_nodes):
        scores[node] = {
            "risk_score": round(float(probs[i]), 6),
            "is_buggy_train": bool(y_train[i]),
            "is_buggy_test": bool(y_test[i]),
            "in_test_set": bool(has_test_data[i]),
            **{sig: round(float(X[i, j]), 6) for j, sig in enumerate(SIGNAL_NAMES)},
        }

    ranked = sorted(scores.items(), key=lambda x: x[1]["risk_score"], reverse=True)

    os.makedirs("analysis/results", exist_ok=True)
    out_file = f"analysis/results/{owner}_{repo}_risk_scores.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(dict(ranked), f, indent=2)

    # Quick stats
    test_nodes = [(n, v) for n, v in ranked if v["in_test_set"]]
    top10_test = test_nodes[:10]
    buggy_top10 = sum(1 for _, v in top10_test if v["is_buggy_test"])
    print(f"  Test setindeki ilk 10 dosyadan {buggy_top10}'i gercekten buggy (test label)")
    print(f"  Kaydedildi -> {out_file}")

    # Save model weights separately
    weights_file = f"analysis/results/{owner}_{repo}_learned_weights.json"
    with open(weights_file, "w", encoding="utf-8") as f:
        json.dump({
            "signals": SIGNAL_NAMES,
            "coefficients": [round(float(c), 4) for c in coefs],
            "intercept": round(float(model.intercept_[0]), 4),
        }, f, indent=2)

    return dict(ranked)


if __name__ == "__main__":
    for owner, repo in REPOS:
        compute_risk_scores(owner, repo)
    print("\nTum risk skorlari hesaplandi!")
