"""Sphinx extension: repository links go to GitHub; Exhale's tree views link right and collapse."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, NamedTuple
from urllib.parse import quote, urljoin, urlsplit

from docutils import nodes
from docutils.nodes import make_id
from myst_parser.mdit_to_docutils.sphinx_ import SphinxRenderer
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.transforms import SphinxTransform

HREF_ATTR = "kataglyphis_href"
_WRAPPED_FLAG = "_kataglyphis_keeps_href"
SUBMODULE_BRANCH = "develop"
# An export (git archive) has no .git; .gitmodules and .github are tracked and live at the root.
ROOT_MARKERS = (".git", ".gitmodules", ".github")
_GITMODULES_SECTION = re.compile(r'\s*\[submodule\s+"[^"]*"\s*\]')
_GITMODULES_KEY = re.compile(r"\s*(path|url|branch)\s*=\s*(.*?)\s*$", re.IGNORECASE)
EXHALE_TREE_VIEW_SUFFIX = "_view_hierarchy.rst.include"
# Exhale's tree view links a label with its case and dots kept; the docutils id has neither.
_EXHALE_TREE_LINK = re.compile(r'(href="[^"#]+\.html#)([^"]+)"')
EXHALE_TREE_APPLIER = "collapsible-lists/js/apply-collapsible-lists.js"
_EXHALE_STATIC = Path(__file__).resolve().parent / "exhale_static"


class Submodule(NamedTuple):
    path: Path
    url: str
    branch: str


def repository_root(srcdir: Path) -> Path | None:
    """The nearest directory at or above *srcdir* holding one of the ``ROOT_MARKERS``."""
    for candidate in (srcdir, *srcdir.parents):
        if any((candidate / marker).exists() for marker in ROOT_MARKERS):
            return candidate
    return None


def submodules(root: Path) -> list[Submodule]:
    """The submodules *root*'s ``.gitmodules`` declares that have a path and a url."""
    gitmodules = root / ".gitmodules"
    if not gitmodules.is_file():
        return []
    entries: list[dict[str, str]] = []
    for line in gitmodules.read_text(encoding="utf-8").splitlines():
        if _GITMODULES_SECTION.match(line):
            entries.append({})
        elif entries and (key := _GITMODULES_KEY.match(line)):
            entries[-1][key[1].lower()] = key[2].strip('"')
    return [
        Submodule((root / entry["path"]).resolve(), entry["url"], entry.get("branch", ""))
        for entry in entries
        if entry.get("path") and entry.get("url")
    ]


def web_url(clone_url: str, parent_url: str) -> str:
    """``https://<host>/<owner>/<repo>`` for a clone URL: https, ssh, scp form, or relative."""
    url = clone_url.strip().rstrip("/").removesuffix(".git")
    if url.startswith(("./", "../")):
        return urljoin(f"{parent_url.rstrip('/')}/", url).rstrip("/")
    if "://" in url:
        parts = urlsplit(url)
        return f"https://{parts.hostname}{parts.path}"
    host, _, path = url.partition(":")
    return f"https://{host.rpartition('@')[2]}/{path.lstrip('/')}"


def repository_url(base_url: str, branch: str, root: Path, target: Path, fragment: str) -> str:
    """``<repo>/blob/<branch>/<path>`` (``tree`` for a directory) in the repo holding *target*."""
    while sub := next(
        (s for s in submodules(root) if s.path != root and target.is_relative_to(s.path)), None
    ):
        base_url, root = web_url(sub.url, base_url), sub.path
        # `branch = .` is git's "the superproject's branch".
        branch = branch if sub.branch == "." else sub.branch or SUBMODULE_BRANCH
    kind = "tree" if target.is_dir() else "blob"
    path = target.relative_to(root).as_posix()
    url = f"{base_url.rstrip('/')}/{kind}/{branch}"
    if path != ".":
        url = f"{url}/{quote(path)}"
    return f"{url}#{fragment}" if fragment else url


def _is_myst_link(node: nodes.Node) -> bool:
    return (
        isinstance(node, (addnodes.download_reference, addnodes.pending_xref))
        and node.get("reftype") == "myst"
    )


def _myst_links(parent: nodes.Element) -> list[nodes.Element]:
    return [node for node in parent.findall(nodes.Element) if _is_myst_link(node)]


def _href(node: nodes.Element) -> str | None:
    """The link as written; without the recorded href only a path-valued reftarget will do."""
    if HREF_ATTR in node:
        return node[HREF_ATTR]
    if isinstance(node, addnodes.download_reference) or node.get("refdomain") is None:
        return node["reftarget"]
    return None


class RepositoryFileLinks(SphinxTransform):
    """Send a MyST link to a repository file the site does not publish to that file on GitHub."""

    # Before DoctreeReadEvent (880), so the download collector never sees a rewritten link.
    default_priority = 500

    def apply(self, **kwargs: Any) -> None:
        base_url = (self.config.html_theme_options or {}).get("repository_url", "")
        if not self.config.kataglyphis_repository_links or not base_url:
            return
        srcdir = Path(self.env.srcdir).resolve()
        root = repository_root(srcdir)
        if root is None:
            return
        for node in _myst_links(self.document):
            href = _href(node)
            if not href or "://" in href:
                continue
            path, _, fragment = href.partition("#")
            if not path:
                continue
            target = Path(self.env.relfn2path(path, self.env.docname)[1]).resolve()
            if not target.exists() or not target.is_relative_to(root):
                continue
            if self._published(node, target, srcdir):
                continue
            url = repository_url(
                base_url, self.config.kataglyphis_repository_branch, root, target, fragment
            )
            children = [child.deepcopy() for child in node.children]
            if not node.astext():
                children = [nodes.literal(path, path)]
            node.replace_self(nodes.reference("", "", *children, refuri=url))

    def _published(self, node: nodes.Element, target: Path, srcdir: Path) -> bool:
        """A document in the build, or a file under the source dir Sphinx copies as a download."""
        if target.is_dir() or not target.is_relative_to(srcdir):
            return False
        if node.get("refdomain") == "doc":
            return node["reftarget"] in self.env.found_docs
        return True


def _keep_hrefs_of_path_links() -> None:
    """MyST keeps no link's href and drops a file link's #fragment; record the href on the node."""
    if getattr(SphinxRenderer, _WRAPPED_FLAG, False):
        return
    original = SphinxRenderer.render_link_unknown

    def render_link_unknown(self: SphinxRenderer, token: Any) -> None:
        start = len(self.current_node.children)
        original(self, token)
        href = self.md.normalizeLinkText(str(token.attrGet("href") or ""))
        for node in self.current_node.children[start:]:
            if isinstance(node, nodes.Element) and _is_myst_link(node):
                node[HREF_ATTR] = href

    SphinxRenderer.render_link_unknown = render_link_unknown
    setattr(SphinxRenderer, _WRAPPED_FLAG, True)


def exhale_tree_anchors(
    app: Sphinx, relative_path: Path, parent_docname: str, content: list[str]
) -> None:
    """With Exhale loaded, point its tree views' links at the ids docutils gives its labels."""
    if "exhale" in app.extensions and relative_path.name.endswith(EXHALE_TREE_VIEW_SUFFIX):
        content[0] = _EXHALE_TREE_LINK.sub(lambda m: f'{m[1]}{make_id(m[2])}"', content[0])


def exhale_tree_without_jquery(app: Sphinx) -> None:
    """Copy a jQuery-free applier over Exhale's, whose ``$`` Sphinx 6 no longer ships."""
    static = app.config.html_static_path
    ours = str(_EXHALE_STATIC)
    if ours not in static and any(
        (Path(app.confdir, entry) / EXHALE_TREE_APPLIER).is_file() for entry in static
    ):
        # Sphinx copies html_static_path in order and overwrites, so the last entry wins.
        static.append(ours)


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_config_value("kataglyphis_repository_links", True, "env", bool)
    app.add_config_value("kataglyphis_repository_branch", "develop", "env", str)
    app.connect("include-read", exhale_tree_anchors)
    # After Exhale's own builder-inited (priority 500), which adds its tree view's static dir.
    app.connect("builder-inited", exhale_tree_without_jquery, priority=900)
    _keep_hrefs_of_path_links()
    app.add_transform(RepositoryFileLinks)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
