"""The theme's link handling, proven on a real `sphinx-build -W` of a throwaway repository."""

from __future__ import annotations

import re
import sys
import types
from pathlib import Path

import pytest
from sphinx.application import Sphinx
from sphinx.cmd.build import build_main
from sphinx_kataglyphis.links import repository_root, repository_url, web_url

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


EXPORTED_LINKS = """\
- [scripts](../linux/scripts/)
- [patches](upstream/patches/)
- [agents](../AGENTS.md)
"""


@pytest.mark.parametrize("marker", [".github", ".gitmodules"])
def test_an_exported_tree_without_git_links_like_a_checkout(tmp_path, capsys, marker):
    """`git archive` drops .git; the hub's directory links became dead `#../linux/...` anchors."""
    docs = _repository(tmp_path, body=EXPORTED_LINKS)
    root = docs.parent
    (root / ".git").rmdir()
    if marker == ".github":
        (root / marker).mkdir()
    else:
        (root / marker).write_text("", encoding="utf-8")
    code, html, warnings = _build(docs, tmp_path, capsys, f"repository_url={REPO_URL!r}")
    assert code == 0, warnings
    assert {
        f"{REPO_URL}/tree/develop/linux/scripts",
        f"{REPO_URL}/tree/develop/docs/upstream/patches",
        f"{BLOB}/AGENTS.md",
    } <= _hrefs(html)


def test_a_directory_link_with_no_repository_root_fails_the_build(tmp_path, capsys):
    """Without a root there is no GitHub path, and MyST's warning keeps -W from shipping `#`."""
    docs = _repository(tmp_path, body="[scripts](../linux/scripts/)\n")
    (docs.parent / ".git").rmdir()
    if repository_root(docs) is not None:
        pytest.skip("an ancestor of the temp dir is itself a repository")
    code, _, warnings = _build(docs, tmp_path, capsys, f"repository_url={REPO_URL!r}")
    assert code != 0
    assert "linux/scripts/" in warnings


def test_the_branch_is_configurable(tmp_path, capsys):
    docs = _repository(tmp_path, body="[agents](../AGENTS.md)\n")
    conf = f"repository_url={REPO_URL!r}, kataglyphis_repository_branch='main'"
    code, html, warnings = _build(docs, tmp_path, capsys, conf)
    assert code == 0, warnings
    assert f"{REPO_URL}/blob/main/AGENTS.md" in _hrefs(html)


SUBMODULE_LINKS = """\
- [hub index](../third_party/hub/docs/INDEX.md#the-index)
- [hub scripts](../third_party/hub/linux/scripts/)
- [hub](../third_party/hub/)
- [nested](../third_party/hub/third_party/doc/README.md)
- [not a submodule](../third_party/hubby/notes.md)
"""


def _checkout(path: Path, gitmodules: str = "") -> Path:
    """A submodule checkout: ``.git`` is a file, ``.gitmodules`` declares its own submodules."""
    path.mkdir(parents=True, exist_ok=True)
    (path / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    if gitmodules:
        (path / ".gitmodules").write_text(gitmodules, encoding="utf-8")
    return path


def test_a_link_into_a_submodule_goes_to_the_submodules_repository(tmp_path, capsys):
    """GitHub serves no file under a gitlink; .gitmodules names the repository that has it."""
    docs = _repository(tmp_path, body=SUBMODULE_LINKS)
    root = docs.parent
    (root / ".gitmodules").write_text(
        '[submodule "hub"]\n\tpath = third_party/hub\n'
        "\turl = git@github.com:Org/Hub.git\n\tbranch = main\n",
        encoding="utf-8",
    )
    hub = _checkout(
        root / "third_party" / "hub",
        '[submodule "third_party/doc"]\n'
        "\tpath = third_party/doc\n\turl = https://github.com/Org/Doc.git\n",
    )
    (hub / "docs").mkdir()
    (hub / "docs" / "INDEX.md").write_text("# The index\n", encoding="utf-8")
    (hub / "linux" / "scripts").mkdir(parents=True)
    (hub / "linux" / "scripts" / "run.sh").write_text("true\n", encoding="utf-8")
    nested = _checkout(hub / "third_party" / "doc")
    (nested / "README.md").write_text("# Doc\n", encoding="utf-8")
    (root / "third_party" / "hubby").mkdir()
    (root / "third_party" / "hubby" / "notes.md").write_text("# Notes\n", encoding="utf-8")

    code, html, warnings = _build(docs, tmp_path, capsys, f"repository_url={REPO_URL!r}")
    assert code == 0, warnings
    assert {
        "https://github.com/Org/Hub/blob/main/docs/INDEX.md#the-index",
        "https://github.com/Org/Hub/tree/main/linux/scripts",
        "https://github.com/Org/Hub/tree/main",
        # No `branch =` in the hub's .gitmodules: the family's default branch.
        "https://github.com/Org/Doc/blob/develop/README.md",
        f"{BLOB}/third_party/hubby/notes.md",
    } <= _hrefs(html)


@pytest.mark.parametrize(
    ("clone_url", "web"),
    [
        ("https://github.com/Org/Hub.git", "https://github.com/Org/Hub"),
        ("https://github.com/google/fuzztest", "https://github.com/google/fuzztest"),
        ("git@github.com:Org/Hub.git", "https://github.com/Org/Hub"),
        ("ssh://git@github.com/Org/Hub.git/", "https://github.com/Org/Hub"),
        ("../Sibling.git", "https://github.com/org/Sibling"),
    ],
)
def test_a_clone_url_becomes_the_repositorys_web_url(clone_url, web):
    assert web_url(clone_url, REPO_URL) == web


def test_a_dot_branch_follows_the_superprojects_branch(tmp_path):
    """`branch = .` is git's spelling for "the branch the superproject is on"."""
    (tmp_path / ".gitmodules").write_text(
        '[submodule "lib"]\n\tpath = lib\n\turl = https://github.com/org/lib\n\tbranch = .\n',
        encoding="utf-8",
    )
    target = _checkout(tmp_path / "lib") / "README.md"
    target.write_text("# Lib\n", encoding="utf-8")
    url = repository_url(REPO_URL, "main", tmp_path.resolve(), target.resolve(), "")
    assert url == "https://github.com/org/lib/blob/main/README.md"


def test_the_repository_root_is_the_nearest_git_checkout(tmp_path):
    """A submodule's .git is a file, and the submodule, not its superproject, is the repository."""
    (tmp_path / ".git").mkdir()
    sub = tmp_path / "third_party" / "hub"
    (sub / "docs").mkdir(parents=True)
    (sub / ".git").write_text("gitdir: ../../.git/modules/hub\n", encoding="utf-8")
    assert repository_root(sub / "docs") == sub
    assert repository_root(tmp_path / "third_party") == tmp_path


EXHALE_HREF = "classKataglyphis_1_1Foo.html#exhale-class-classKataglyphis-1-1Foo"


def _exhale_site(tmp_path: Path) -> Path:
    """What Exhale writes: a tree view of raw HTML included by library_root, and a labelled page."""
    docs = tmp_path / "repo" / "docs"
    api = docs / "api"
    api.mkdir(parents=True)
    (docs / "index.md").write_text(
        "# Repo\n\n```{toctree}\napi/library_root\napi/classKataglyphis_1_1Foo\n```\n",
        encoding="utf-8",
    )
    (api / "library_root.rst").write_text(
        "Library API\n===========\n\n.. include:: class_view_hierarchy.rst.include\n",
        encoding="utf-8",
    )
    (api / "class_view_hierarchy.rst.include").write_text(
        f'.. raw:: html\n\n   <ul><li>Class <a href="{EXHALE_HREF}">Foo</a></li></ul>\n',
        encoding="utf-8",
    )
    (api / "classKataglyphis_1_1Foo.rst").write_text(
        ".. _exhale_class_classKataglyphis_1_1Foo:\n\nClass Foo\n=========\n", encoding="utf-8"
    )
    return docs


@pytest.mark.parametrize("with_exhale", [True, False], ids=["exhale", "no-exhale"])
def test_exhale_tree_view_links_hit_the_ids_docutils_makes(
    tmp_path, capsys, monkeypatch, with_exhale
):
    """Exhale links `#exhale-class-classKataglyphis-1-1Foo`; docutils lowercases the label's id."""
    stub = types.ModuleType("exhale")
    stub.setup = lambda app: {"parallel_read_safe": True}
    monkeypatch.setitem(sys.modules, "exhale", stub)
    docs = _exhale_site(tmp_path)
    conf = "extensions_extra=['exhale']" if with_exhale else ""
    code, _, warnings = _build(docs, tmp_path, capsys, conf)
    assert code == 0, warnings
    api = tmp_path / "html" / "api"
    tree = {h for h in _hrefs((api / "library_root.html").read_text(encoding="utf-8")) if "#" in h}
    if not with_exhale:
        assert EXHALE_HREF in tree
        return
    assert "classKataglyphis_1_1Foo.html#exhale-class-classkataglyphis-1-1foo" in tree
    assert EXHALE_HREF not in tree
    page = (api / "classKataglyphis_1_1Foo.html").read_text(encoding="utf-8")
    assert 'id="exhale-class-classkataglyphis-1-1foo"' in page


EXHALE_APPLIER = "collapsible-lists/js/apply-collapsible-lists.js"


def _exhale_with_a_tree_view(data: Path) -> types.ModuleType:
    """Exhale 0.3.7's tree-view setup: at builder-inited it adds its data dir and two scripts."""
    js = data / "collapsible-lists" / "js"
    js.mkdir(parents=True)
    (js / "CollapsibleLists.compressed.js").write_text("var CollapsibleLists={};\n", "utf-8")
    (js / "apply-collapsible-lists.js").write_text(
        "$(document).ready(function() {\n    CollapsibleLists.apply();\n});\n", "utf-8"
    )

    def builder_inited(app: Sphinx) -> None:
        app.config.html_static_path.append(str(data))
        app.add_js_file("collapsible-lists/js/CollapsibleLists.compressed.js")
        app.add_js_file(EXHALE_APPLIER)

    def setup(app: Sphinx) -> dict:
        app.connect("builder-inited", builder_inited)
        return {"parallel_read_safe": True}

    stub = types.ModuleType("exhale")
    stub.setup = setup
    return stub


@pytest.mark.parametrize("with_exhale", [True, False], ids=["exhale", "no-exhale"])
def test_exhale_tree_view_collapses_without_jquery(tmp_path, capsys, monkeypatch, with_exhale):
    """Exhale's applier calls `$(document).ready`; Sphinx 6 and later ship no jQuery."""
    monkeypatch.setitem(sys.modules, "exhale", _exhale_with_a_tree_view(tmp_path / "exhale"))
    docs = _exhale_site(tmp_path)
    conf = "extensions_extra=['exhale']" if with_exhale else ""
    code, _, warnings = _build(docs, tmp_path, capsys, conf)
    assert code == 0, warnings
    applier = tmp_path / "html" / "_static" / EXHALE_APPLIER
    if not with_exhale:
        assert not applier.exists()
        return
    script = applier.read_text(encoding="utf-8")
    assert "$(" not in script
    assert "CollapsibleLists.apply()" in script
    page = (tmp_path / "html" / "api" / "library_root.html").read_text(encoding="utf-8")
    assert f'src="../_static/{EXHALE_APPLIER}?v=' in page
