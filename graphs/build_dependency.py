"""
AST-based dependency graph builder.
Clones each repository (shallow) and parses Python imports to build
a directed graph where an edge A -> B means module A imports module B.
"""
import ast
import os
import subprocess
import networkx as nx
import pickle

REPOS = [
    ("psf", "requests"),
    ("pallets", "flask"),
    ("scikit-learn", "scikit-learn"),
]

CLONE_DIR = "graphs/repos"


def clone_repo(owner, repo):
    dest = os.path.join(CLONE_DIR, f"{owner}_{repo}")
    if os.path.exists(dest):
        print(f"  Repo zaten mevcut: {dest}")
        return dest
    url = f"https://github.com/{owner}/{repo}.git"
    print(f"  Klonlaniyor: {url}")
    subprocess.run(
        ["git", "clone", "--depth", "1", url, dest],
        capture_output=True, text=True
    )
    return dest


def extract_imports(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=filepath)
    except (SyntaxError, UnicodeDecodeError):
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])
    return imports


def find_python_files(repo_dir, known_files):
    """Find .py files that match our known file list from commit data."""
    py_files = {}
    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".tox", "node_modules")]
        for f in files:
            if f.endswith(".py"):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, repo_dir).replace("\\", "/")
                py_files[rel] = full
    return py_files


def module_name_from_path(filepath):
    """Convert file path to Python module name: src/flask/app.py -> flask.app"""
    parts = filepath.replace("\\", "/").replace("/", ".").replace(".py", "")
    if parts.startswith("src."):
        parts = parts[4:]
    return parts


def build_ast_dependency_graph(owner, repo, known_files):
    print(f"\n  {owner}/{repo} - AST dependency graph...")

    os.makedirs(CLONE_DIR, exist_ok=True)
    repo_dir = clone_repo(owner, repo)

    py_files = find_python_files(repo_dir, known_files)

    path_to_module = {}
    module_to_path = {}
    for rel_path in py_files:
        mod = module_name_from_path(rel_path)
        path_to_module[rel_path] = mod
        top_level = mod.split(".")[0]
        module_to_path[mod] = rel_path
        module_to_path[top_level] = rel_path

    G = nx.DiGraph()

    for rel_path, full_path in py_files.items():
        if rel_path not in known_files and not any(rel_path.endswith(kf.split("/")[-1]) for kf in known_files):
            continue
        matched_known = None
        for kf in known_files:
            if rel_path == kf or rel_path.endswith(kf) or kf.endswith(rel_path):
                matched_known = kf
                break
        if not matched_known:
            continue

        G.add_node(matched_known)
        imports = extract_imports(full_path)

        for imp in imports:
            for kf2 in known_files:
                kf2_mod = module_name_from_path(kf2)
                kf2_top = kf2_mod.split(".")[0]
                kf2_parts = kf2_mod.split(".")

                if imp == kf2_top or imp == kf2_mod or imp in kf2_parts:
                    if kf2 != matched_known:
                        G.add_node(kf2)
                        G.add_edge(matched_known, kf2)

    for kf in known_files:
        if not G.has_node(kf):
            G.add_node(kf)

    print(f"    {G.number_of_nodes()} dugum, {G.number_of_edges()} kenar")
    return G


if __name__ == "__main__":
    import json

    for owner, repo in REPOS:
        stats_file = f"data/processed/{owner}_{repo}_file_stats.json"
        with open(stats_file, "r", encoding="utf-8") as f:
            file_stats = json.load(f)
        known_files = set(file_stats.keys())

        G = build_ast_dependency_graph(owner, repo, known_files)

        os.makedirs("graphs", exist_ok=True)
        out = f"graphs/{owner}_{repo}_dependency.pkl"
        with open(out, "wb") as f:
            pickle.dump(G, f)
        print(f"    Kaydedildi -> {out}")

    print("\nTum AST dependency graphlari olusturuldu!")
