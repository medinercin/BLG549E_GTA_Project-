import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {TOKEN}"}

REPOS = [
    ("psf", "requests"),
    ("pallets", "flask"),
    ("scikit-learn", "scikit-learn")
]

def get_commit_files(owner, repo, sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    
    while True:
        r = requests.get(url, headers=HEADERS)
        
        remaining = int(r.headers.get("X-RateLimit-Remaining", 1))
        if remaining < 10:
            reset_time = int(r.headers.get("X-RateLimit-Reset", time.time()))
            wait = reset_time - int(time.time()) + 5
            print(f"\nRate limit yaklaşıyor, {wait} saniye bekleniyor...")
            time.sleep(wait)
            continue
        
        if r.status_code == 403:
            print("\nRate limit aşıldı, 60 saniye bekleniyor...")
            time.sleep(60)
            continue
        
        if r.status_code != 200:
            return []
        
        data = r.json()
        files = []
        for f in data.get("files", []):
            if f["filename"].endswith(".py"):
                files.append({
                    "filename": f["filename"],
                    "changes": f.get("changes", 0),
                    "additions": f.get("additions", 0),
                    "deletions": f.get("deletions", 0),
                    "status": f.get("status", "")
                })
        return files


def process_repo(owner, repo):
    # Daha önce çekilen commitleri yükle
    commits_file = f"data/raw/{owner}_{repo}_commits.json"
    with open(commits_file, "r", encoding="utf-8") as f:
        commits = json.load(f)
    
    print(f"\n{owner}/{repo} — {len(commits)} commit için dosyalar çekiliyor...")
    
    # Kaldığı yerden devam etmek için checkpoint sistemi
    output_file = f"data/raw/{owner}_{repo}_commit_files.json"
    
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            results = json.load(f)
        done_shas = {r["sha"] for r in results}
        print(f"  Checkpoint bulundu: {len(results)} commit zaten işlenmiş, kaldığı yerden devam ediliyor...")
    else:
        results = []
        done_shas = set()
    
    remaining_commits = [c for c in commits if c["sha"] not in done_shas]
    total = len(remaining_commits)
    
    for i, commit in enumerate(remaining_commits):
        files = get_commit_files(owner, repo, commit["sha"])
        
        results.append({
            "sha": commit["sha"],
            "message": commit["message"],
            "date": commit["date"],
            "author": commit["author"],
            "files": files
        })
        
        # Her 50 committe bir kaydet — çökerse veri kaybolmasın
        if (i + 1) % 50 == 0:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"  İlerleme: {i+1}/{total} commit işlendi ve kaydedildi")
        
        time.sleep(0.5)
    
    # Son kayıt
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"  Tamamlandı: {len(results)} commit kaydedildi → {output_file}")
    return results


if __name__ == "__main__":
    for owner, repo in REPOS:
        process_repo(owner, repo)
    print("\nTüm repo dosyaları başarıyla çekildi!")