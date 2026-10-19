"""The theme's link handling, proven on a real `sphinx-build -W` of a throwaway repository."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from sphinx.cmd.build import build_main
from sphinx_kataglyphis.links import repository_root

REPO_URL = "https://github.com/org/repo"
BLOB = f"{REPO_URL}/blob/develop"

HEAD = "# Repo\n\n```{toctree}\n:hidden:\npage\n```\n\n"

LINKS = """\
- [agents](../AGENTS.md)
- [agents section](../AGENTS.md#image-and-tag-naming)
- [tool](../linux/tool/README.md)
- [scripts](../linux/scripts/)
- [patches](upstream/patches/)
- [page heading](page.md#a-heading-with-punctuation)
- [in page](#no-active-session--grpc-the-client-is-closing-mid-chain)
- [data](data.json)

## `no active session` / `grpc: the client is closing` mid-chain
"""


def _repository(tmp_path: Path, body: str = LINKS) -> Path:
    """A repo with docs/ as the Sphinx source dir and files beside it the site never publishes."""
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Agents\n\n## Image and tag naming\n", encoding="utf-8")
    (root / "linux" / "tool").mkdir(parents=True)
    (root / "linux" / "tool" / "README.md").write_text("# Tool\n", encoding="utf-8")
    (root / "linux" / "scripts").mkdir()
    (root / "linux" / "scripts" / "run.sh").write_text("true\n", encoding="utf-8")
    docs = root / "docs"
    (docs / "upstream" / "patches").mkdir(parents=True)
    (docs / "upstream" / "patches" / "0001.patch").write_text("", encoding="utf-8")
    (docs / "data.json").write_text("{}\n", encoding="utf-8")
    (docs / "page.md").write_text("# Page\n\n## A heading, with punctuation!\n", encoding="utf-8")
    (docs / "index.md").write_text(HEAD + body, encoding="utf-8")
    return docs


def _build(docs: Path, tmp_path: Path, capsys, conf: str) -> tuple[int, str, str]:
    (docs / "conf.py").write_text(
        f"from sphinx_kataglyphis import setup_theme\nsetup_theme(globals(), {conf})\n",
        encoding="utf-8",
    )
    out = tmp_path / "html"
    code = build_main(["-W", "-N", "-q", "-b", "html", str(docs), str(out)])
    index = out / "index.html"
    html = index.read_text(encoding="utf-8") if index.exists() else ""
    return code, html, capsys.readouterr().err


def _hrefs(html: str) -> set[str]:
    return set(re.findall(r'href="([^"]+)"', html))


def test_links_resolve_on_the_site_or_on_github(tmp_path, capsys):
    docs = _repository(tmp_path)
    code, html, warnings = _build(docs, tmp_path, capsys, f"repository_url={REPO_URL!r}")
    assert code == 0, warnings
    hrefs = _hrefs(html)
    assert {
        f"{BLOB}/AGENTS.md",
        f"{BLOB}/AGENTS.md#image-and-tag-naming",
        f"{BLOB}/linux/tool/README.md",
        f"{REPO_URL}/tree/develop/linux/scripts",
        f"{REPO_URL}/tree/develop/docs/upstream/patches",
        "page.html#a-heading-with-punctuation",
        "#no-active-session-grpc-the-client-is-closing-mid-chain",
    } <= hrefs
    # A file under the source dir is published, so it stays Sphinx's own download.
    assert any(h.startswith("_downloads/") and h.endswith("/data.json") for h in hrefs)
    assert not list((tmp_path / "html" / "_downloads").rglob("AGENTS.md"))


def test_a_missing_repository_file_still_fails_the_build(tmp_path, capsys):
    """Only an existing file is redirected; a broken link must stay a -W failure."""
    docs = _repository(tmp_path, body="[gone](../MISSING.md)\n")
    code, _, warnings = _build(docs, tmp_path, capsys, f"repository_url={REPO_URL!r}")
    assert code != 0
    assert "MISSING" in warnings


@pytest.mark.parametrize(
    "conf",
    [f"repository_url={REPO_URL!r}, kataglyphis_repository_links=False", "project_name='Repo'"],
    ids=["opted-out", "no-repository-url"],
)
def test_links_stay_sphinx_downloads_without_a_repository_to_point_at(tmp_path, capsys, conf):
    docs = _repository(tmp_path, body="[run](../linux/scripts/run.sh)\n")
    code, html, warnings = _build(docs, tmp_path, capsys, conf)
    assert code == 0, warnings
    runs = [h for h in _hrefs(html) if h.endswith("run.sh")]
    assert runs and all(h.startswith("_downloads/") for h in runs)


def test_the_branch_is_configurable(tmp_path, capsys):
    docs = _repository(tmp_path, body="[agents](../AGENTS.md)\n")
    conf = f"repository_url={REPO_URL!r}, kataglyphis_repository_branch='main'"
    code, html, warnings = _build(docs, tmp_path, capsys, conf)
    assert code == 0, warnings
    assert f"{REPO_URL}/blob/main/AGENTS.md" in _hrefs(html)


def test_the_repository_root_is_the_nearest_git_checkout(tmp_path):
    """A submodule's .git is a file, and the submodule, not its superproject, is the repository."""
    (tmp_path / ".git").mkdir()
    sub = tmp_path / "third_party" / "hub"
    (sub / "docs").mkdir(parents=True)
    (sub / ".git").write_text("gitdir: ../../.git/modules/hub\n", encoding="utf-8")
    assert repository_root(sub / "docs") == sub
    assert repository_root(tmp_path / "third_party") == tmp_path
