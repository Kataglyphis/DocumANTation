"""Identity belongs to style/brand.json, exactly like the colours do.

AGENTS.md has stated the rule for a long time -- "All \\url{}, \\email{},
\\github{} references must use consistent values. The canonical URL is
... and GitHub handle is ..." -- and nothing enforced it. So the author name was
typed by hand into 16 files, and the supporting values had already drifted:

    URL        www.jonasheinle.de   jonasheinle.de
    email      contact@jonasheinle.de   jonasheinle@googlemail.com
    institute  Karlsruhe Institute of Technology   ... (KIT)

Every one of those now comes from the `identity` section of brand.json, through
md2pdfLib/style/brand-identity.tex for LaTeX, the generated Pandoc metadata for
Pandoc, and brand.tokens.json for everything else. These tests are the rule.

Prose is exempt: a README or a chapter may say the author's name. What may not
happen is a *template or config* carrying the value, because that is the copy
that silently goes stale.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
IDENTITY = json.loads((REPO_ROOT / "style" / "brand.tokens.json").read_text("utf-8"))["identity"]

# Where a literal is a bug rather than content: things a build reads.
CONFIG_SUFFIXES = (".tex", ".cls", ".yml", ".yaml", ".py", ".sh", ".toml", ".json")

# Files that legitimately carry a literal, each for a stated reason.
EXEMPT = {
    # The source of truth itself.
    "style/brand.json",
    # Generated from it -- that is the point.
    "style/brand.tokens.json",
    "md2pdfLib/style/brand.tokens.json",
    "md2pdfLib/style/brand-identity.tex",
    "sphinx-kataglyphis-theme/sphinx_kataglyphis/brand.tokens.json",
    "md2pdfLib/pandoc/base.yml",
    "md2pdfLib/presentation/pandoc/metadata.yml",
    "md2pdfLib/example/pandoc/metadata.yml",
    # Packaging manifests cannot read a JSON file at parse time. Pinned instead
    # by test_the_package_manifest_agrees_with_the_identity below.
    "pyproject.toml",
    "sphinx-kataglyphis-theme/pyproject.toml",
    # These tests, which necessarily name the values they check.
    "tests/test_identity_is_single_source.py",
}

# CV section files are prose that happens to be written in LaTeX. The institute
# name appears in them as the provider of a course and as a referee's employer --
# the same string as the author's affiliation, meaning something different. A
# reworded sentence there is content, not brand drift.
EXEMPT_PROSE = ("data/cv/section_",)

# Values distinctive enough that finding one in a config file means it was typed
# there. "Jonas"/"Heinle" alone are too short to scan for safely, and the full
# name is the one that mattered.
SCANNED = ("name", "email", "contact_email", "url", "url_display", "github_url", "institute")


def _tracked_config_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    return [
        p
        for p in out
        if p.endswith(CONFIG_SUFFIXES) and p not in EXEMPT and not p.startswith(EXEMPT_PROSE)
    ]


@pytest.mark.parametrize("key", SCANNED)
def test_no_config_file_hardcodes_an_identity_value(key: str):
    value = IDENTITY[key]
    offenders: list[str] = []
    for rel in _tracked_config_files():
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        # Skip comment-only mentions: a comment explaining where a value comes
        # from is documentation, not a second copy the build reads.
        code = "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith(("%", "#", "//"))
        )
        if value in code:
            offenders.append(rel)
    assert not offenders, (
        f"identity.{key} ({value!r}) is written by hand in: {offenders}. "
        "Read it from style/brand.json instead -- brand-identity.tex for LaTeX, "
        "the generated Pandoc metadata for Pandoc, brand()['identity'] for Python."
    )


def test_the_url_has_exactly_one_spelling():
    """It had three: https://jonasheinle.de, jonasheinle.de and www.jonasheinle.de."""
    spellings: set[str] = set()
    pattern = re.compile(r"(?:https?://)?(?:www\.)?jonasheinle\.de")
    for rel in _tracked_config_files():
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        spellings.update(pattern.findall(path.read_text(encoding="utf-8", errors="replace")))
    assert spellings <= {IDENTITY["url"], IDENTITY["url_display"]}, (
        f"unexpected URL spellings in config files: {sorted(spellings)}; "
        f"the identity defines only {IDENTITY['url']!r} and {IDENTITY['url_display']!r}"
    )


def test_the_package_manifest_agrees_with_the_identity():
    """pyproject.toml cannot be generated, so it is checked instead."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    authors = re.search(r"authors\s*=\s*\[\s*\{([^}]*)\}", text)
    assert authors, "pyproject.toml has no authors entry"
    assert IDENTITY["name"] in authors.group(1)
    assert IDENTITY["email"] in authors.group(1)
    assert f'Homepage = "{IDENTITY["url"]}"' in text, (
        f"pyproject Homepage must be {IDENTITY['url']}, the identity's URL"
    )


def test_the_latex_identity_file_defines_every_macro_the_templates_use():
    """A template using an undefined macro renders the macro name, or errors."""
    generated = (REPO_ROOT / "md2pdfLib" / "style" / "brand-identity.tex").read_text("utf-8")
    defined = set(re.findall(r"\\providecommand\{\\(\w+)\}", generated))

    # Only the macros this file could own. `\\brand*` also matches the font and
    # code-box macros that brand-fonts.tex and brand-code-block.tex define, and
    # those are not this file's business.
    candidates = re.compile(r"\\(" + "|".join(sorted(defined, key=len, reverse=True)) + r")\b")
    used: set[str] = set()
    for rel in _tracked_config_files():
        if not rel.endswith((".tex", ".cls")):
            continue
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        used.update(candidates.findall(path.read_text("utf-8")))

    assert used, "no template reads the identity macros -- the wiring is gone"
    assert used <= defined


def test_the_identity_reaches_every_output_kind():
    """LaTeX, Pandoc and Python each need their own route to the same values."""
    latex = (REPO_ROOT / "md2pdfLib" / "style" / "brand-identity.tex").read_text("utf-8")
    assert IDENTITY["name"] in latex

    for metadata in (
        "md2pdfLib/pandoc/base.yml",
        "md2pdfLib/presentation/pandoc/metadata.yml",
        "md2pdfLib/example/pandoc/metadata.yml",
    ):
        text = (REPO_ROOT / metadata).read_text("utf-8")
        assert f"author: {IDENTITY['name']}" in text, metadata

    # Python consumers read the resolved tokens, including inside the wheel.
    for tokens in (
        "style/brand.tokens.json",
        "md2pdfLib/style/brand.tokens.json",
        "sphinx-kataglyphis-theme/sphinx_kataglyphis/brand.tokens.json",
    ):
        payload = json.loads((REPO_ROOT / tokens).read_text("utf-8"))
        assert payload["identity"] == IDENTITY, tokens
