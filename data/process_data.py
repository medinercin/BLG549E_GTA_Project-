import json
import os
import re
from collections import defaultdict

BUG_KEYWORDS = [
    r'\bfix\b', r'\bbug\b', r'\bdefect\b', r'\berror\b',
    r'\bcrash\b', r'\bissue\b', r'\bfault\b', r'\bpatch\b',
    r'\bhotfix\b', r'\bresolve\b', r'\bcorrect\b', r'\bregression\b'
]

SKIP_PATTERNS = [
    r'test_', r'_test\.py', r'setup\.py', r'conf\.py',
    r'docs/', r'examples/', r'benchmarks/', r'\.github/',
]

REPOS = [
    ("psf", "requests"),
    ("pallets", "flask"),
    ("scikit-learn", "scikit-learn")
]

SPLIT_DATE = "2025-01-01T00:00:00Z"


def is_bug_fix(message):
    msg = message.lower()
    return any(re.search(kw, msg) for kw in BUG_KEYWORDS)


def should_skip(filename):
    return any(re.search(pattern, filename) for pattern in SKIP_PATTERNS)


def build_file_stats(commit_list):
    stats = defaultdict(lambda: {
        "total_commits": 0,
        "bug_fix_commits": 0,
        "total_changes": 0,
        "commit_messages": [],
        "co_changed_with": defaultdict(int)
    })
    for commit in commit_list:
        file_list = [f["filename"] for f in commit["files"]]
        for f in commit["files"]:
            fname = f["filename"]
            stats[fname]["total_commits"] += 1
            stats[fname]["total_changes"] += f["changes"]
            stats[fname]["commit_messages"].append(commit["message"])
            if commit["is_bug_fix"]:
                stats[fname]["bug_fix_commits"] += 1
            for other in file_list:
                if other != fname:
                    stats[fname]["co_changed_with"][other] += 1
    return stats


def serialize_stats(stats):
    out = {}
    for fname, s in stats.items():
        out[fname] = {
            "total_commits": s["total_commits"],
            "bug_fix_commits": s["bug_fix_commits"],
            "total_changes": s["total_changes"],
            "is_buggy": s["bug_fix_commits"] >= 1,
            "commit_messages": s["commit_messages"],
            "co_changed_with": dict(s["co_changed_with"])
        }
    return out


def process_repo(owner, repo):
    print(f"\n{owner}/{repo} isleniyor...")

    commits_file = f"data/processed/{owner}_{repo}_commits_clean.json"
    with open(commits_file, "r", encoding="utf-8") as f:
        all_commits = json.load(f)

    train_commits = [c for c in all_commits if c["date"] < SPLIT_DATE]
    test_commits  = [c for c in all_commits if c["date"] >= SPLIT_DATE]

    train_stats = build_file_stats(train_commits)
    test_stats  = build_file_stats(test_commits)

    train_buggy = sum(1 for s in train_stats.values() if s["bug_fix_commits"] >= 1)
    test_buggy  = sum(1 for s in test_stats.values() if s["bug_fix_commits"] >= 1)

    print(f"  Train (<2025): {len(train_commits)} commit, {len(train_stats)} dosya, {train_buggy} buggy")
    print(f"  Test (>=2025): {len(test_commits)} commit, {len(test_stats)} dosya, {test_buggy} buggy")

    prefix = f"data/processed/{owner}_{repo}"

    with open(f"{prefix}_train_commits.json", "w", encoding="utf-8") as f:
        json.dump(train_commits, f, indent=2, ensure_ascii=False)
    with open(f"{prefix}_test_commits.json", "w", encoding="utf-8") as f:
        json.dump(test_commits, f, indent=2, ensure_ascii=False)
    with open(f"{prefix}_file_stats.json", "w", encoding="utf-8") as f:
        json.dump(serialize_stats(train_stats), f, indent=2, ensure_ascii=False)
    with open(f"{prefix}_test_file_stats.json", "w", encoding="utf-8") as f:
        json.dump(serialize_stats(test_stats), f, indent=2, ensure_ascii=False)

    print(f"  Kaydedildi")


if __name__ == "__main__":
    for owner, repo in REPOS:
        process_repo(owner, repo)
    print("\nTum repolar islendi!")
