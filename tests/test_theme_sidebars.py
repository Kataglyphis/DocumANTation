"""The sidebar toggles, proven on a real `sphinx-build -W` of a throwaway site."""

from __future__ import annotations

import re
from pathlib import Path

from sphinx.cmd.build import build_main
from sphinx_kataglyphis import brand_css_path


def _index_html(tmp_path: Path) -> str:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "conf.py").write_text(
        "from sphinx_kataglyphis import setup_theme\nsetup_theme(globals(), project_name='Repo')\n",
        encoding="utf-8",
    )
    (docs / "index.md").write_text(
        "# Repo\n\n```{toctree}\npage\n```\n\n## Section\n", encoding="utf-8"
    )
    (docs / "page.md").write_text("# Page\n\n## A\n\n## B\n", encoding="utf-8")
    out = tmp_path / "html"
    assert build_main(["-W", "-N", "-q", "-b", "html", str(docs), str(out)]) == 0
    return (out / "index.html").read_text(encoding="utf-8")


def test_each_sidebar_has_one_toggle_the_theme_js_can_bind(tmp_path):
    """The JS binds the first `.primary-toggle`; pydata 0.20's header put a hidden one there."""
    html = _index_html(tmp_path)
    toggles = re.findall(r'<button class="([^"]*sidebar-toggle[^"]*)"', html)
    assert sum("primary-toggle" in c for c in toggles) == 1, toggles
    assert sum("secondary-toggle" in c for c in toggles) == 1, toggles


def test_the_brand_css_leaves_the_primary_sidebars_position_to_the_theme():
    """A sticky sidebar stays in the flow as a drawer and pushes the article's toggle off-screen."""
    css = re.sub(r"/\*.*?\*/", "", brand_css_path().read_text(encoding="utf-8"), flags=re.S)
    rules = [
        b for s, b in re.findall(r"([^{}]+)\{([^}]*)\}", css) if s.strip() == ".bd-sidebar-primary"
    ]
    assert rules
    for body in rules:
        assert not re.search(r"(^|[;\s])(position|top|max-height)\s*:", body), body
