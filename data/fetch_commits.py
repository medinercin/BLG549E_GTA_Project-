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

def get_commits(owner, repo):
    print(f"\n{owner}/{repo} için commitler çekiliyor...")
    commits = []
    page = 1

    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        params = {
            "per_page": 100,
            "page": page,
            "since": "2022-01-01T00:00:00Z"  # son 3 yıl yeterli
        }

        r = requests.get(url, headers=HEADERS, params=params)

        # Rate limit kontrolü
        remaining = int(r.headers.get("X-RateLimit-Remaining", 1))
        if remaining < 10:
            reset_time = int(r.headers.get("X-RateLimit-Reset", time.time()))
            wait = reset_time - int(time.time()) + 5
            print(f"Rate limit yaklaşıyor, {wait} saniye bekleniyor...")
            time.sleep(wait)
            continue

        if r.status_code == 403:
            print("Rate limit aşıldı, 60 saniye bekleniyor...")
            time.sleep(60)
            continue

        if r.status_code != 200:
            print(f"Hata: {r.status_code}")
            break

        data = r.json()
        if not data:
            break

        for commit in data:
            commits.append({
                "sha": commit["sha"],
                "message": commit["commit"]["message"],
                "date": commit["commit"]["author"]["date"],
                "author": commit["commit"]["author"]["name"]
            })

        print(f"  Sayfa {page}: {len(data)} commit alındı (toplam: {len(commits)})")
        page += 1
        time.sleep(0.5)  # API'yi yormamak için

    return commits


def save_commits(owner, repo, commits):
    os.makedirs("data/raw", exist_ok=True)
    filename = f"data/raw/{owner}_{repo}_commits.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(commits, f, indent=2, ensure_ascii=False)
    print(f"Kaydedildi: {filename} ({len(commits)} commit)")


if __name__ == "__main__":
    for owner, repo in REPOS:
        commits = get_commits(owner, repo)
        save_commits(owner, repo, commits)
    print("\nTüm commitler başarıyla çekildi!")