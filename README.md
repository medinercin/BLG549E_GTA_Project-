# BLG549E - Graph Theory and Algorithms
## Term Project: Graph-Based Bug Prediction

Medine Erçin - 704251008

---

## What This Project Is About

The idea is to predict which source files in a software project are likely to contain bugs, using graph theory. Instead of just looking at code metrics, I represent the repository as a graph and use structural signals to compute a risk score for each module.

Three open-source Python repositories are used as data sources: `psf/requests`, `pallets/flask`, and `scikit-learn/scikit-learn`. All data is collected from their public GitHub histories. No private access is needed.

---

## What I Have Done So Far
 
### Step 1 — Data Collection (`data/fetch_commits.py`)
I used the GitHub REST API to pull the full commit history of each repository (from 2022 onwards). For each commit I saved the SHA, message, date, and author. Rate limiting and checkpoint logic are handled in the script so it can resume if interrupted.
 
### Step 2 — File-Level Data (`data/fetch_files.py`)
For each commit, I made a separate API call to get the list of files that were changed. I kept only `.py` files and recorded the filename, lines added, lines deleted, and change status. This was the most time-consuming step — scikit-learn alone has several thousand commits.
 
### Step 3 — Cleaning and Labelling (`data/process_data.py`)
I filtered out test files, docs, setup scripts, and anything not directly part of the source code. Then I tagged each commit as a bug-fix or not based on keywords in the message (fix, bug, error, crash, patch, etc.). Any file that appeared in at least one bug-fix commit is labelled as buggy — this becomes the ground truth for evaluation later.
 
**Results after cleaning:**
 
| Repository | Commits processed | Bug-fix commits | Files | Buggy files |
|---|---|---|---|---|
| psf/requests | 115 | 35 (30%) | 41 | 22 (53%) |
| pallets/flask | 432 | 66 (15%) | 31 | 22 (70%) |
| scikit-learn | 3145 | 819 (26%) | 391 | 225 (57%) |
 
### Step 4 — Building the Graphs (`graphs/build_graphs.py`)
I built three different graph representations for each repository. For this step I got help from an AI assistant (Claude) to write the graph construction code.
 
- **Co-change graph** (undirected, weighted): files that were modified together in the same commit get an edge; weight = number of times they co-changed.
- **Semantic similarity graph** (undirected, weighted): commit messages for each file are combined into a text document, vectorized with TF-IDF, and files with cosine similarity above 0.25 get an edge.
- **Dependency graph** (directed): built from co-change frequency as a proxy for import relationships — frequently co-changed files in the same direction are treated as structurally dependent.
**Graph sizes after construction:**
 
| Repository | Co-change | Semantic | Dependency |
|---|---|---|---|
| psf/requests | 41 nodes, 415 edges | 31 nodes, 147 edges | 41 nodes, 32 edges |
| pallets/flask | 31 nodes, 304 edges | 31 nodes, 280 edges | 31 nodes, 266 edges |
| scikit-learn | 382 nodes, 34954 edges | 342 nodes, 39184 edges | 391 nodes, 13469 edges |
 
---
 
## What Is Left
 
- Compute centrality metrics (betweenness, PageRank, weighted degree) on each graph
- Combine signals into a composite risk score per module
- Evaluate predictions against ground truth labels (Precision, Recall, F1, AUC-ROC)
- Compare full model against baselines (single-signal models)
---

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