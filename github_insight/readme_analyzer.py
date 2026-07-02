"""README and metadata signal extraction."""

from __future__ import annotations

import re

from github_insight.models import RepositoryRaw


INSTALL_PAT = re.compile(r"\b(install|installation|pip install|npm install|docker run|setup)\b", re.I)
USAGE_PAT = re.compile(r"\b(usage|example|quickstart|getting started|demo)\b", re.I)
DEMO_PAT = re.compile(r"\b(demo|live app|screenshot|preview|hosted)\b|https?://", re.I)
DOCS_PAT = re.compile(r"\b(docs|documentation|guide|tutorial)\b", re.I)
DATASET_PAT = re.compile(r"\b(dataset|data set|csv|parquet|sql|database|benchmark data)\b", re.I)
MODEL_PAT = re.compile(r"\b(model|weights|checkpoint|benchmark|baseline|evaluation|metric)\b", re.I)
NOTEBOOK_PAT = re.compile(r"\b(notebook|ipynb|jupyter|colab)\b", re.I)
DOCKER_PAT = re.compile(r"\b(docker|dockerfile|container)\b", re.I)
REQUIREMENTS_PAT = re.compile(r"\b(requirements\.txt|pyproject\.toml|environment\.yml|package\.json)\b", re.I)
HYPE_PAT = re.compile(r"\b(revolutionary|game[- ]changing|magic|best ever|sota|production-ready)\b", re.I)


def synthesize_mock_readme(repo: RepositoryRaw) -> str:
    topics = ", ".join(repo.topics)
    return (
        f"# {repo.name}\n\n"
        f"{repo.description}\n\n"
        f"Topics: {topics}.\n\n"
        "Installation: use the documented setup for this fixture.\n\n"
        "Usage: review the example workflow and adapt it into a small portfolio note.\n\n"
        "This deterministic README is for offline testing and does not claim live README evidence."
    )


def analyze_readme(text: str, repo: RepositoryRaw) -> dict[str, object]:
    source = text or ""
    lower = source.lower()
    length = len(source)
    has_install = bool(INSTALL_PAT.search(source))
    has_usage = bool(USAGE_PAT.search(source))
    has_demo = bool(DEMO_PAT.search(source)) or repo.homepage not in {"", "unavailable"}
    has_docs = bool(DOCS_PAT.search(source))
    has_dataset = bool(DATASET_PAT.search(source))
    has_model = bool(MODEL_PAT.search(source))
    has_notebook = bool(NOTEBOOK_PAT.search(source)) or repo.language.lower() == "jupyter notebook"
    has_docker = bool(DOCKER_PAT.search(source))
    has_requirements = bool(REQUIREMENTS_PAT.search(source))
    has_csv_or_sql = "csv" in lower or "sql" in lower or "database" in lower or "duckdb" in lower
    signals = []
    if has_install:
        signals.append("installation instructions")
    if has_usage:
        signals.append("usage examples")
    if has_notebook:
        signals.append("notebook signal")
    if has_docker:
        signals.append("docker signal")
    if has_requirements:
        signals.append("dependency file signal")
    if has_dataset:
        signals.append("dataset signal")
    if has_model:
        signals.append("model or benchmark signal")

    score = 0.0
    score += min(30.0, length / 80.0)
    score += 15.0 if has_install else 0.0
    score += 15.0 if has_usage else 0.0
    score += 10.0 if has_demo else 0.0
    score += 10.0 if has_docs else 0.0
    score += 10.0 if signals else 0.0
    score += 10.0 if repo.description != "unavailable" else 0.0
    score = max(0.0, min(100.0, score))

    risk_flags = []
    if not source:
        risk_flags.append("no README evidence")
    elif length < 400:
        risk_flags.append("README too short")
    if not has_install:
        risk_flags.append("installation unclear")
    if not has_usage:
        risk_flags.append("usage examples unclear")
    if HYPE_PAT.search(source) and len(signals) < 2:
        risk_flags.append("hype language without enough evidence")

    return {
        "readme_text_excerpt": source[:1200] if source else "unavailable",
        "readme_length": length,
        "readme_quality_score": round(score, 2),
        "has_installation_instructions": has_install,
        "has_usage_examples": has_usage,
        "has_demo_link": has_demo,
        "has_docs_link": has_docs,
        "has_notebook": has_notebook,
        "has_dataset": has_dataset,
        "has_csv_or_sql": has_csv_or_sql,
        "has_dockerfile": has_docker,
        "has_requirements": has_requirements,
        "has_environment_file": "environment.yml" in lower or "conda" in lower,
        "has_pyproject": "pyproject.toml" in lower,
        "has_package_file": "package.json" in lower,
        "reproducibility_signals": signals,
        "risk_flags": risk_flags,
    }
