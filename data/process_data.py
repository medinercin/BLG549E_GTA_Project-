import json
import os
import re
from collections import defaultdict

# Bug ile ilgili anahtar kelimeler
BUG_KEYWORDS = [
    r'\bfix\b', r'\bbug\b', r'\bdefect\b', r'\berror\b',
    r'\bcrash\b', r'\bissue\b', r'\bfault\b', r'\bpatch\b',
    r'\bhotfix\b', r'\bresolve\b', r'\bcorrect\b', r'\bregression\b'
]

# Atlanacak dosya türleri — bunlar analizimizi bozar
SKIP_PATTERNS = [
    r'test_',           # test dosyaları
    r'_test\.py',
    r'setup\.py',
    r'conf\.py',        # sphinx config
    r'docs/',           # dokümantasyon
    r'examples/',       # örnek kodlar
    r'benchmarks/',     # benchmark kodları
    r'\.github/',       # github workflow dosyaları
]

REPOS = [
    ("psf", "requests"),
    ("pallets", "flask"),
    ("scikit-learn", "scikit-learn")
]


def is_bug_fix(message):
    """Commit mesajı bug fix mi?"""
    msg = message.lower()
    return any(re.search(kw, msg) for kw in BUG_KEYWORDS)


def should_skip(filename):
    """Bu dosyayı atlamalı mıyız?"""
    return any(re.search(pattern, filename) for pattern in SKIP_PATTERNS)


def process_repo(owner, repo):
    print(f"\n{owner}/{repo} işleniyor...")

    # Ham veriyi yükle
    input_file = f"data/raw/{owner}_{repo}_commit_files.json"
    with open(input_file, "r", encoding="utf-8") as f:
        commits = json.load(f)

    # --- 1. Commit düzeyinde işleme ---
    processed_commits = []
    bug_fix_count = 0

    for commit in commits:
        # Sadece .py dosyalarını al, atlanacakları çıkar
        clean_files = [
            f for f in commit["files"]
            if f["filename"].endswith(".py")
            and not should_skip(f["filename"])
        ]

        if not clean_files:
            continue  # Bu committe işe yarar .py dosyası yoksa atla

        is_bug = is_bug_fix(commit["message"])
        if is_bug:
            bug_fix_count += 1

        processed_commits.append({
            "sha": commit["sha"],
            "message": commit["message"],
            "date": commit["date"],
            "is_bug_fix": is_bug,
            "files": clean_files
        })

    print(f"  Toplam commit: {len(commits)}")
    print(f"  İşlenebilir commit: {len(processed_commits)}")
    print(f"  Bug-fix commit: {bug_fix_count} "
          f"(%{100*bug_fix_count//len(processed_commits)})")

    # --- 2. Dosya düzeyinde özet çıkar ---
    # Her dosya için istatistik topla
    file_stats = defaultdict(lambda: {
        "total_commits": 0,       # kaç committe yer aldı
        "bug_fix_commits": 0,     # kaç bug-fix committe yer aldı
        "total_changes": 0,       # toplam değişen satır
        "commit_messages": [],    # bu dosyayla ilgili tüm mesajlar (NLP için)
        "co_changed_with": defaultdict(int)  # hangi dosyayla kaç kez birlikte değişti
    })

    for commit in processed_commits:
        file_list = [f["filename"] for f in commit["files"]]

        for f in commit["files"]:
            fname = f["filename"]
            file_stats[fname]["total_commits"] += 1
            file_stats[fname]["total_changes"] += f["changes"]
            file_stats[fname]["commit_messages"].append(commit["message"])

            if commit["is_bug_fix"]:
                file_stats[fname]["bug_fix_commits"] += 1

            # Co-change: bu dosyayla aynı committe olan diğer dosyalar
            for other in file_list:
                if other != fname:
                    file_stats[fname]["co_changed_with"][other] += 1

    # --- 3. Bug label oluştur ---
    # En az 1 bug-fix commitinde yer alan dosya = buggy
    buggy_files = set()
    for fname, stats in file_stats.items():
        if stats["bug_fix_commits"] >= 1:
            buggy_files.add(fname)

    print(f"  Toplam dosya: {len(file_stats)}")
    print(f"  Buggy dosya: {len(buggy_files)} "
          f"(%{100*len(buggy_files)//len(file_stats)})")

    # --- 4. Kaydet ---
    os.makedirs("data/processed", exist_ok=True)

    # İşlenmiş commitler
    commits_out = f"data/processed/{owner}_{repo}_commits_clean.json"
    with open(commits_out, "w", encoding="utf-8") as f:
        json.dump(processed_commits, f, indent=2, ensure_ascii=False)

    # Dosya istatistikleri — defaultdict'i normale çevir
    stats_serializable = {}
    for fname, stats in file_stats.items():
        stats_serializable[fname] = {
            "total_commits": stats["total_commits"],
            "bug_fix_commits": stats["bug_fix_commits"],
            "total_changes": stats["total_changes"],
            "is_buggy": fname in buggy_files,
            "commit_messages": stats["commit_messages"],
            "co_changed_with": dict(stats["co_changed_with"])
        }

    stats_out = f"data/processed/{owner}_{repo}_file_stats.json"
    with open(stats_out, "w", encoding="utf-8") as f:
        json.dump(stats_serializable, f, indent=2, ensure_ascii=False)

    print(f"  Kaydedildi: {commits_out}")
    print(f"  Kaydedildi: {stats_out}")

    return stats_serializable, buggy_files


if __name__ == "__main__":
    for owner, repo in REPOS:
        process_repo(owner, repo)
    print("\nTüm repolar başarıyla işlendi!")