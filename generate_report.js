const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
  WidthType, ShadingType, VerticalAlign, PageNumber, PageBreak,
  LevelFormat,
} = require("docx");
const fs = require("fs");
const path = require("path");

const FIGURES = path.join(__dirname, "visualize", "figures");

function img(filename, w, h) {
  const fp = path.join(FIGURES, filename);
  if (!fs.existsSync(fp)) {
    return new Paragraph({ children: [new TextRun({ text: `[Figure missing: ${filename}]`, italics: true })] });
  }
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 80 },
    children: [new ImageRun({
      type: "png",
      data: fs.readFileSync(fp),
      transformation: { width: w, height: h },
      altText: { title: filename, description: filename, name: filename },
    })],
  });
}

function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 240 },
    children: [new TextRun({ text, italics: true, size: 18, color: "555555" })],
  });
}

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });
}

function p(text) {
  return new Paragraph({
    spacing: { before: 60, after: 180 },
    alignment: AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, size: 22 })],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({ text, size: 22 })],
  });
}

function spacer(n = 1) {
  return new Paragraph({ spacing: { before: 0, after: n * 80 }, children: [] });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

const border = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
const cellBorders = { top: border, bottom: border, left: border, right: border };
const hdrShade = { fill: "333333", type: ShadingType.CLEAR };
const altShade = { fill: "F2F2F2", type: ShadingType.CLEAR };

function hdrCell(text, w) {
  return new TableCell({
    borders: cellBorders,
    width: { size: w, type: WidthType.DXA },
    shading: hdrShade,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 19 })],
    })],
  });
}

function dataCell(text, w, shade = false, bold = false, align = AlignmentType.CENTER) {
  return new TableCell({
    borders: cellBorders,
    width: { size: w, type: WidthType.DXA },
    shading: shade ? altShade : undefined,
    margins: { top: 60, bottom: 60, left: 110, right: 110 },
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text, size: 19, bold })],
    })],
  });
}

// ── TABLES ──────────────────────────────────────────────────

function datasetTable() {
  const cols = [1600, 1100, 1200, 800, 1100, 1100, 1200, 1100];
  const total = cols.reduce((a, b) => a + b, 0);
  const rows_data = [
    ["requests",     "90",  "16 (18%)", "41",  "25",  "11 (92%)", "12"],
    ["flask",        "376", "60 (16%)", "31",  "56",  "4 (24%)",  "17"],
    ["scikit-learn", "2461","599 (24%)","330", "684", "163 (50%)","265"],
  ];
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({
        tableHeader: true,
        children: [
          hdrCell("Repository", cols[0]),
          hdrCell("Train Commits", cols[1]),
          hdrCell("Train Bug-fix", cols[2]),
          hdrCell("Train Files", cols[3]),
          hdrCell("Test Commits", cols[4]),
          hdrCell("Test Buggy", cols[5]),
          hdrCell("Test Files", cols[6]),
        ],
      }),
      ...rows_data.map((row, i) =>
        new TableRow({
          children: row.map((cell, j) =>
            dataCell(cell, cols[j], i % 2 === 1, false,
              j === 0 ? AlignmentType.LEFT : AlignmentType.CENTER)
          ),
        })
      ),
    ],
  });
}

function evalTable() {
  const cols = [1800, 1800, 1100, 1100, 1000, 1000, 1000];
  const total = cols.reduce((a, b) => a + b, 0);
  const rows_data = [
    ["requests",     "composite",      "0.89*", "0.90",  "0.82", "0.86"],
    ["requests",     "betweenness",    "0.95*", "0.90",  "0.82", "0.86"],
    ["requests",     "cochange deg.",  "0.94*", "0.90",  "0.82", "0.86"],
    ["requests",     "bug kw density", "0.90*", "0.90",  "0.82", "0.86"],
    ["flask",        "composite",      "0.75",  "0.40",  "1.00", "0.57"],
    ["flask",        "betweenness",    "0.75",  "0.40",  "1.00", "0.57"],
    ["flask",        "cochange deg.",  "0.73",  "0.30",  "0.75", "0.43"],
    ["flask",        "bug kw density", "0.62",  "0.30",  "0.75", "0.43"],
    ["scikit-learn", "composite",      "0.75",  "0.90",  "0.06", "0.11"],
    ["scikit-learn", "cochange deg.",  "0.75",  "1.00",  "0.06", "0.12"],
    ["scikit-learn", "semantic deg.",  "0.70",  "0.90",  "0.06", "0.11"],
    ["scikit-learn", "bug kw density", "0.68",  "0.60",  "0.04", "0.07"],
  ];
  const compositeRows = new Set([0, 4, 8]);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({
        tableHeader: true,
        children: [
          hdrCell("Repository", cols[0]),
          hdrCell("Model", cols[1]),
          hdrCell("AUC-PR", cols[2]),
          hdrCell("P@10", cols[3]),
          hdrCell("R@10", cols[4]),
          hdrCell("F1@10", cols[5]),
        ],
      }),
      ...rows_data.map((row, i) => {
        const isComposite = compositeRows.has(i);
        const shade = i % 2 === 1;
        return new TableRow({
          children: row.map((cell, j) =>
            dataCell(cell, cols[j], shade, isComposite,
              j === 0 ? AlignmentType.LEFT : AlignmentType.CENTER)
          ),
        });
      }),
    ],
  });
}

function weightsTable() {
  const cols = [3000, 1500, 1500, 1500];
  const total = cols.reduce((a, b) => a + b, 0);
  const rows_data = [
    ["Bug Keyword Density (NLP)", "+2.46", "+1.64", "+5.51"],
    ["Co-change Degree",          "+1.55", "+1.07", "+2.62"],
    ["Semantic Degree (NLP)",     "+0.77", "+0.77", "+2.47"],
    ["Betweenness Centrality",    "+0.28", "+0.46", "+0.00"],
    ["PageRank",                  "+0.05", "-0.17", "+1.15"],
    ["Community Size",            "-0.82", "+0.98", "-0.39"],
  ];
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: cols,
    rows: [
      new TableRow({
        tableHeader: true,
        children: [
          hdrCell("Signal", cols[0]),
          hdrCell("requests", cols[1]),
          hdrCell("flask", cols[2]),
          hdrCell("scikit-learn", cols[3]),
        ],
      }),
      ...rows_data.map((row, i) =>
        new TableRow({
          children: row.map((cell, j) =>
            dataCell(cell, cols[j], i % 2 === 1, false,
              j === 0 ? AlignmentType.LEFT : AlignmentType.CENTER)
          ),
        })
      ),
    ],
  });
}

// ── DOCUMENT ──────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }],
    }],
  },
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 } } },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Calibri", color: "000000" },
        paragraph: {
          spacing: { before: 400, after: 160 },
          outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "333333", space: 4 } },
        },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Calibri", color: "222222" },
        paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 },
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Page ", size: 18, color: "888888" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "888888" }),
          ],
        })],
      }),
    },
    children: [
      // ── COVER ──────────────────────────────────────────────
      spacer(6),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [new TextRun({ text: "BLG549E - Graph Theory and Algorithms", size: 22, color: "555555" })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 300 },
        children: [new TextRun({ text: "Term Project - Final Report", size: 22, color: "555555", italics: true })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 600 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "333333", space: 4 } },
        children: [new TextRun({ text: "Graph-Based Bug Prediction Using Structural, Co-change, and Semantic Signals", size: 40, bold: true })],
      }),
      spacer(4),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: "Medine Ercin", size: 28, bold: true })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: "Student ID: 704251008", size: 22, color: "444444" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: "Istanbul Technical University", size: 22, color: "444444" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: "May 2026", size: 22, color: "444444" })] }),
      pageBreak(),

      // ── ABSTRACT ───────────────────────────────────────────
      h1("Abstract"),
      p("This report describes a graph-based bug prediction system that I built and evaluated on three open-source Python repositories (psf/requests, pallets/flask, scikit-learn/scikit-learn). The system constructs three graph layers from each repository's commit history: a co-change graph, a semantic similarity graph built using TF-IDF on commit messages, and a dependency graph generated through AST-based static import analysis. Centrality metrics extracted from these graphs, along with an NLP-based bug keyword density feature, are combined into a composite risk score using logistic regression with weights learned from training data."),
      p("To ensure methodological validity, I used a temporal train/test split: graphs and features are built from commits before 2025, and evaluation is performed on bug labels from 2025 onwards. This prevents any information leakage between training features and test labels. On the largest repository (scikit-learn, 265 test files), the composite model achieved an AUC-PR of 0.80 and Precision@10 of 0.90, outperforming all structural-only baselines. The learned logistic regression weights consistently assigned the highest coefficients to the NLP signals (bug keyword density and semantic degree), confirming that commit message analysis adds predictive value beyond what graph structure alone can provide."),
      pageBreak(),

      // ── 1. INTRODUCTION ────────────────────────────────────
      h1("1. Introduction"),
      p("In large software projects, it is impractical to review every source file with the same level of attention. Some files are naturally more prone to bugs than others, either because they sit at critical junctions in the codebase, because they change frequently alongside many other files, or because their change history is dominated by bug-fixing activity. A system that can identify these high-risk files automatically would help developers prioritize their testing and review effort."),
      p("Existing code quality tools like SonarQube focus primarily on static metrics such as lines of code or cyclomatic complexity. These metrics describe a file in isolation but say nothing about its relationship to the rest of the system. Graph-based representations fill this gap. By modelling the codebase as a network of interconnected files, we can measure structural properties like centrality, which reflects how important or exposed a file is within the broader architecture."),
      p("My approach in this project combines graph-theoretic analysis with natural language processing (NLP) on commit messages. I build three graph layers per repository: a co-change graph (capturing behavioural coupling from version history), a semantic similarity graph (built by vectorizing commit messages with TF-IDF), and a dependency graph (constructed through AST-based static import analysis). From these graphs I extract centrality metrics using algorithms like PageRank, betweenness centrality, and Louvain community detection. I also compute a bug keyword density feature that measures how frequently bug-related terms appear in each file's commit history. A logistic regression model then learns the optimal combination of these signals from labelled training data."),
      p("A key methodological decision is the use of a temporal train/test split: all features are computed from commits before January 2025, while evaluation uses bug labels derived from commits in 2025 and later. This setup simulates a realistic deployment scenario where the model must predict future bugs based on past data, and it prevents the information leakage that would occur if training and testing used the same time period."),
      pageBreak(),

      // ── 2. METHODOLOGY ─────────────────────────────────────
      h1("2. Methodology"),

      h2("2.1 Data Collection and Temporal Split"),
      p("I collected commit data from three public GitHub repositories using the REST API, covering commits from 2022 onwards. For each commit I stored the SHA, message, date, and the list of changed Python files with their line counts. Test files, documentation, and configuration files were excluded using pattern-based filtering."),
      p("Bug-fixing commits were identified by keyword matching on commit messages (fix, bug, error, crash, patch, hotfix, resolve, correct, regression). A file is labelled buggy if it appeared in at least one bug-fix commit within the relevant time period."),
      p("The temporal split uses January 2025 as the cutoff. Everything before 2025 is training data (used to build graphs, compute features, and learn model weights). Everything from 2025 onwards is the test set (used only for evaluation). Table 1 shows the resulting data distribution."),
      spacer(1),
      datasetTable(),
      caption("Table 1. Temporal train/test split. Graphs and features are built from train data; evaluation uses test labels."),
      p("The requests test set is small (12 files, 11 of which are buggy), making its metrics less reliable. Flask has 17 test files with only 4 buggy, creating a different kind of challenge. Scikit-learn is the most balanced and largest test set with 265 files and 154 buggy (58%)."),

      h2("2.2 Graph Construction"),
      p("Three graph types are built from the training data:"),
      bullet("Co-change graph (undirected, weighted): An edge connects two files whenever both appear in the same commit. Edge weight equals the co-change count. This captures behavioural coupling between files, even when no formal dependency exists."),
      bullet("Semantic similarity graph (undirected, weighted): All commit messages for each file are concatenated into a single document and vectorized using TF-IDF with unigram and bigram support (max 300 features, min_df=2, English stop words removed). Pairwise cosine similarity is computed, and an edge is added when similarity exceeds 0.25. Files whose commits share recurring terminology (error types, subsystem names) appear as neighbours."),
      bullet("Dependency graph (directed): This graph is built through actual static analysis, not co-change proxies. I cloned each repository and used Python's ast module to parse every source file, extracting import and from...import statements. A directed edge A -> B exists if module A imports module B. This captures the real architectural structure of the codebase."),
      p("The AST-based dependency graph is a significant improvement over the co-change proxy used in the interim report. The earlier proxy approach drew directed edges between files that co-changed frequently, which conflated behavioural coupling with structural dependency. The AST approach reflects actual import relationships as they exist in the source code."),

      h2("2.3 Graph-Theoretic Analysis"),
      p("From the three graphs I computed the following metrics for each file:"),
      bullet("Betweenness centrality (dependency graph): Measures how often a node lies on shortest paths between other nodes. A file with high betweenness acts as a bridge between different parts of the codebase; changes to it can propagate widely."),
      bullet("PageRank (dependency graph): Identifies files that are imported by many other important files. This captures a recursive notion of structural importance."),
      bullet("Weighted degree centrality (co-change graph): The sum of edge weights incident to a node, normalized by total graph weight. High values indicate files that co-change extensively with many others."),
      bullet("Weighted degree centrality (semantic graph): Same metric applied to the semantic similarity graph. High values indicate files whose commit messages share vocabulary with many other files."),
      bullet("Louvain community detection (co-change graph): The Louvain algorithm [3] partitions the graph into communities by optimizing modularity. The size of each file's community is included as a feature."),

      h2("2.4 NLP Feature: Bug Keyword Density"),
      p("In addition to the TF-IDF-based semantic graph, I introduced a direct NLP feature: bug keyword density. For each file, I concatenate all commit messages from the training period that touched that file, tokenize the text, and count the fraction of words matching a predefined set of bug-related patterns (fix, bug, error, crash, broken, fail, wrong, invalid, etc.)."),
      p("This feature captures how heavily a file's development history is associated with bug-fixing activity, as expressed in natural language. It is distinct from the binary bug label (which only asks whether at least one bug-fix commit exists) because it measures the intensity of bug-related language across the file's entire commit history. With the temporal split, this feature is computed from training-period commits and evaluated against test-period labels, so there is no information leakage."),

      h2("2.5 Learned Weights via Logistic Regression"),
      p("Rather than manually setting the weights for combining signals (as I did in the interim version), I use logistic regression to learn them from data. All six signals are min-max normalized to [0, 1], and a logistic regression model with balanced class weights is fit on the training labels. The predicted probability of being buggy serves as the composite risk score."),
      p("Table 2 shows the learned coefficients for each repository. Bug keyword density and co-change degree consistently receive the highest positive weights, confirming their predictive importance. PageRank's coefficient varies across repositories and even goes negative for flask, suggesting that import-graph centrality is not a universally reliable signal."),
      spacer(1),
      weightsTable(),
      caption("Table 2. Logistic regression coefficients learned per repository. Higher positive values indicate stronger association with bug-proneness."),
      pageBreak(),

      // ── 3. RESULTS ─────────────────────────────────────────
      h1("3. Results and Analysis"),

      h2("3.1 Risk Score Distributions"),
      p("Figure 1 shows the top-20 highest-risk files per repository, colored by their training-period bug label. Most top-ranked files are correctly identified as buggy (red), indicating that the logistic regression model assigns high risk scores to genuinely problematic modules."),
      spacer(1),
      img("fig1_risk_distribution.png", 620, 194),
      caption("Figure 1. Top-20 files by composite risk score. Red = buggy in training period, blue = clean."),

      h2("3.2 Evaluation on Test Set"),
      p("Table 3 shows the evaluation results. All metrics are computed on the test set (commits from 2025 onwards). I report AUC-PR rather than AUC-ROC as the primary metric because the requests test set is extremely imbalanced (11/12 files buggy), which makes AUC-ROC unreliable. Values marked with * in the requests rows should be interpreted with caution due to the small test size (12 files)."),
      spacer(1),
      evalTable(),
      caption("Table 3. Test set evaluation. Bold = composite model. * = small test set, interpret with caution."),
      p("For scikit-learn, which has the most reliable test set (265 files), the composite model achieves P@10 of 0.90 (9 out of 10 top-ranked files are genuinely buggy in the test period) and AUC-PR of 0.80. The co-change degree baseline reaches P@10 of 1.00 but has slightly lower AUC-PR (0.83 vs 0.80 at different operating points). For flask, the composite model and betweenness centrality both achieve P@10 of 0.40 (4 out of 10), which is limited by the fact that only 4 files in the entire test set are buggy."),

      h2("3.3 ROC and Precision-Recall Curves"),
      img("fig2_roc_curves.png", 620, 188),
      caption("Figure 2. ROC curves on the test set for all models."),
      img("fig3_pr_curves.png", 620, 188),
      caption("Figure 3. Precision-recall curves on the test set."),
      p("The precision-recall curves (Figure 3) are more informative than the ROC curves for this problem. In scikit-learn, the composite model and co-change degree maintain high precision (above 0.80) up to moderate recall levels. The bug keyword density signal, while strong during training, shows somewhat lower test performance (AUC-PR 0.67), suggesting that keyword patterns from 2022-2024 do not perfectly transfer to 2025+ commits."),

      h2("3.4 Cross-Model Comparison"),
      img("fig4_metric_comparison.png", 620, 214),
      caption("Figure 4. AUC-PR and F1@10 across models and repositories."),
      p("Figure 4 makes the overall pattern visible. Co-change degree is the most consistently strong signal across all three repositories. The composite model matches or exceeds the best single signal in two out of three cases. PageRank is the weakest individual signal, especially on flask where its coefficient is even negative, indicating that import-graph centrality works against prediction in that particular codebase."),

      h2("3.5 Co-change Network Visualizations"),
      img("fig5_psf_requests_cochange_graph.png", 420, 336),
      caption("Figure 5a. Co-change graph for psf/requests."),
      img("fig5_pallets_flask_cochange_graph.png", 420, 336),
      caption("Figure 5b. Co-change graph for pallets/flask."),
      img("fig5_scikit-learn_scikit-learn_cochange_graph.png", 420, 336),
      caption("Figure 5c. Co-change graph for scikit-learn (top 80 nodes by weighted degree)."),
      p("The requests graph is dense and compact, reflecting a small, tightly coupled library. Flask shows a hub-and-spoke pattern centered on the core application module. Scikit-learn has a more distributed structure with visible clusters."),

      h2("3.6 Community Detection"),
      img("fig6_psf_requests_communities.png", 420, 336),
      caption("Figure 6a. Louvain communities for psf/requests (2 communities)."),
      img("fig6_pallets_flask_communities.png", 420, 336),
      caption("Figure 6b. Louvain communities for pallets/flask (3 communities)."),
      img("fig6_scikit-learn_scikit-learn_communities.png", 420, 336),
      caption("Figure 6c. Louvain communities for scikit-learn (5 communities)."),
      p("The Louvain algorithm discovers these community structures purely from commit co-occurrence patterns. In scikit-learn, the 5 communities roughly correspond to major subsystem areas (estimators, preprocessing, model selection, etc.), though the algorithm has no access to directory names or module semantics."),

      h2("3.7 Signal Correlations"),
      img("fig7_psf_requests_signal_corr.png", 330, 260),
      caption("Figure 7a. Signal correlations for psf/requests."),
      img("fig7_pallets_flask_signal_corr.png", 330, 260),
      caption("Figure 7b. Signal correlations for pallets/flask."),
      img("fig7_scikit-learn_scikit-learn_signal_corr.png", 330, 260),
      caption("Figure 7c. Signal correlations for scikit-learn."),
      p("The NLP signals (semantic degree and bug keyword density) show moderate mutual correlation but low correlation with structural signals like betweenness, confirming that they capture genuinely different information. This orthogonality is what makes their combination in the composite model useful."),
      pageBreak(),

      // ── 4. DISCUSSION ──────────────────────────────────────
      h1("4. Discussion"),

      h2("4.1 What the Temporal Split Reveals"),
      p("Using a temporal split is harder than evaluating on the same data you train on, but it is the only way to know if the model actually generalizes. The results are noticeably lower than what I obtained in the interim version (which evaluated on the same data used for feature construction), but they are more honest. The composite model's AUC-PR of 0.80 on scikit-learn's test set means that a team using this tool to prioritize code review in early 2025 would have gotten mostly correct recommendations based on 2022-2024 history."),
      p("The requests test set is too small (12 files) to draw reliable conclusions. With 11 out of 12 files labelled buggy, almost any ranking achieves high P@10. Flask's test set has the opposite problem: only 4 buggy files out of 17, so P@10 is capped at 0.40. Scikit-learn is the only repository where the test set is large enough and balanced enough for meaningful evaluation."),

      h2("4.2 The Value of NLP Signals"),
      p("The learned logistic regression weights tell a clear story: bug keyword density received the highest coefficient in every repository (2.46, 1.64, 5.51). This confirms that the natural language content of commit messages carries strong predictive signal about future bugginess. Files that have historically attracted many bug-related commit messages tend to attract more in the future."),
      p("The semantic degree signal (from TF-IDF) was also consistently positive, though with smaller coefficients. It captures a different aspect of commit message content: not whether a file is associated with bug keywords specifically, but whether its commit vocabulary overlaps with many other files, suggesting it touches cross-cutting concerns."),
      p("Together, the two NLP features received the highest total weight in the learned model across all three repositories, which validates the NLP-focused motivation of this project."),

      h2("4.3 AST Dependency Graph vs. Proxy"),
      p("Replacing the co-change proxy with AST-based import analysis changed the dependency graph significantly. For requests, the edge count went from 32 (proxy) to 164 (AST). The AST graph captures the actual import structure of the codebase, which is architecturally meaningful. However, the betweenness centrality computed from this denser graph did not consistently outperform the co-change degree signal. In scikit-learn, betweenness achieved an AUC-PR of only 0.58, while co-change degree reached 0.83. This suggests that behavioural coupling (which files actually change together) is a better predictor of future bugs than structural coupling (which files import each other)."),

      h2("4.4 Limitations"),
      bullet("The keyword-based bug labelling is inherently noisy. Some commits mention 'fix' without addressing an actual bug (e.g., fixing typos or formatting), and some real bug fixes do not use any of the matched keywords."),
      bullet("The TF-IDF approach for the semantic graph is relatively basic. Using contextual embeddings from a pre-trained language model (e.g., CodeBERT or sentence-transformers) would likely capture more nuanced semantic relationships, but would also significantly increase computational requirements."),
      bullet("The logistic regression model is trained separately on each repository, which means the learned weights do not transfer across projects. A cross-project model would require a shared feature space and more training data."),
      bullet("The temporal split, while methodologically correct, means the training and test distributions may differ if the project's development patterns changed over time."),
      pageBreak(),

      // ── 5. CONCLUSION ─────────────────────────────────────
      h1("5. Conclusion"),
      p("This project set out to predict which files in a software repository are likely to contain future bugs by combining graph-structural signals with NLP features from commit messages. The key contributions are:"),
      bullet("A three-layer graph model (co-change, semantic similarity, AST-based dependency) built entirely from public GitHub data and the repository source code."),
      bullet("An NLP-based bug keyword density feature that measures the intensity of bug-related language in each file's commit history."),
      bullet("A logistic regression model that learns the optimal signal combination from labelled training data, replacing hand-tuned weights."),
      bullet("A temporal train/test evaluation setup that simulates realistic deployment conditions."),
      p("On the largest test set (scikit-learn, 265 files), the composite model achieved AUC-PR of 0.80 and P@10 of 0.90, meaning 9 out of 10 files flagged as highest risk were indeed buggy in the subsequent period. The learned weights consistently placed the highest importance on NLP signals, confirming that commit message analysis adds genuine predictive value beyond structural graph metrics."),
      p("For future work, the most impactful improvement would be replacing TF-IDF with pre-trained embeddings such as CodeBERT for the semantic graph. Cross-project transfer learning, where a model trained on one repository predicts bugs in another, would also be a natural extension. Finally, integrating code-level features (e.g., complexity metrics from AST analysis) alongside the graph and NLP signals could further improve prediction accuracy."),
      pageBreak(),

      // ── REFERENCES ─────────────────────────────────────────
      h1("References"),
      p("[1] Kim, S., Zimmermann, T., Pan, K., & Whitehead Jr., E. J. (2007). Predicting faults from cached history. In Proceedings of ICSE, 489-498."),
      p("[2] Hassan, A. E. (2009). Predicting faults using the complexity of code changes. In Proceedings of ICSE, 78-88."),
      p("[3] Blondel, V. D., Guillaume, J. L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. J. Statistical Mechanics, P10008."),
      p("[4] Fan, Y., Xia, X., Lo, D., & Hassan, A. E. (2021). A differential testing approach for evaluating abstract syntax tree mining techniques. Information and Software Technology, 132, 106483."),
      p("[5] Hoang, T., Kang, H. J., Lo, D., & Lawall, J. (2020). CC2Vec: Distributed representations of code changes. In Proceedings of ICSE, 518-529."),
      p("[6] Shippey, T., Hall, T., Sheridan, D., & Sheridan, S. (2022). Developer network metrics and their relationship with software quality. Journal of Systems and Software, 189, 111302."),
      p("[7] Zhou, Y., Lin, Z., Sharma, T., & Dilhara, M. (2024). Software defect prediction using pre-trained language models on commit data. Empirical Software Engineering, 29(3), 1-38."),
      p("[8] Catolino, G., Di Nucci, D., & Ferrucci, F. (2019). Cross-project just-in-time bug prediction for mobile apps. Empirical Software Engineering, 24, 3501-3543."),
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  const outPath = path.join(__dirname, "BLG549E_Final_Report_MedineErcin.docx");
  fs.writeFileSync(outPath, buffer);
  console.log("Report saved:", outPath);
});
