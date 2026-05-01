# BLG549E - Graph Theory and Algorithms
## Term Project: Graph-Based Bug Prediction

Medine Erçin - 704251008

---

## What This Project Is About

The idea is to predict which source files in a software project are likely to contain bugs, using graph theory. Instead of just looking at code metrics, I represent the repository as a graph and use structural signals to compute a risk score for each module.

Three open-source Python repositories are used as data sources: `psf/requests`, `pallets/flask`, and `scikit-learn/scikit-learn`. All data is collected from their public GitHub histories. No private access is needed.

---

## What I Have Done So Far

##

## Project Structure

```
blg549e_term_project/
├── data/
│   ├── raw/                  ← raw JSON from GitHub API
│   ├── processed/            ← cleaned commits + per-file stats
│   ├── fetch_commits.py
│   ├── fetch_files.py
│   └── process_data.py
├── graphs/
│   ├── build_graphs.py
│   ├── *_cochange.pkl        ← co-change graphs
│   ├── *_semantic.pkl        ← semantic similarity graphs
│   └── *_dependency.pkl      ← dependency graphs
├── analysis/                 ← risk score computation (next step)
├── evaluation/               ← metrics output (next step)
└── README.md
```

---

## Dependencies

```
pip install requests networkx scikit-learn pandas matplotlib python-dotenv
```

A GitHub personal access token is required (stored in `.env`, not committed).