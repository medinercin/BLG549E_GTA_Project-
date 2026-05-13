# BLG549E - Graph Theory and Algorithms
## Term Project: Graph-Based Bug Prediction

---

## About

This project predicts which source files in a software project are likely to contain bugs using graph theory and NLP on commit messages. Three open-source Python repositories are used: `psf/requests`, `pallets/flask`, and `scikit-learn/scikit-learn`.

Each repository is modelled as three graph layers (dependency, co-change, semantic similarity). Centrality metrics from these graphs are combined with an NLP-based bug keyword density feature into a composite risk score per file.

---

## Results Summary

| Repository | Composite AUC-ROC | P@10 | Bug KW Density AUC-ROC |
|---|---|---|---|
| psf/requests | 0.85 | 0.90 | 1.00 |
| pallets/flask | 0.96 | 1.00 | 0.96 |
| scikit-learn | 0.90 | 0.90 | 1.00 |

---

## Project Structure

```
blg549e_term_project/
├── data/
│   ├── raw/                  <- raw JSON from GitHub API
│   ├── processed/            <- cleaned commits + per-file stats
│   ├── fetch_commits.py
│   ├── fetch_files.py
│   └── process_data.py
├── graphs/
│   ├── build_graphs.py
│   └── *.pkl                 <- pickled graph objects
├── analysis/
│   ├── compute_centrality.py <- betweenness, PageRank, Louvain, weighted degree, bug kw density
│   ├── risk_score.py         <- composite risk score computation
│   ├── evaluate.py           <- AUC-ROC, AUC-PR, P@k, F1@k evaluation
│   └── results/              <- JSON/CSV output files
├── visualize/
│   ├── plot_graphs.py        <- all figure generation
│   └── figures/              <- PNG outputs (13 figures)
├── generate_report.js        <- Word report generator
├── BLG549E_Final_Report_MedineErcin.docx
└── README.md
```

---

## How to Run

```bash
# 1. Install dependencies
pip install requests networkx scikit-learn pandas matplotlib python-dotenv
npm install docx

# 2. Data collection (requires GITHUB_TOKEN in .env)
python data/fetch_commits.py
python data/fetch_files.py

# 3. Data processing
python data/process_data.py

# 4. Build graphs
python graphs/build_graphs.py

# 5. Analysis pipeline
python analysis/compute_centrality.py
python analysis/risk_score.py
python analysis/evaluate.py

# 6. Generate figures
python visualize/plot_graphs.py

# 7. Generate report
node generate_report.js
```

A GitHub personal access token is required for data collection (stored in `.env`, not committed).
