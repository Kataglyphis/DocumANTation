"""Identity comes from style/brand.json; prose may name it, no template or config may copy it."""

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
# Build inputs with no suffix, which a suffix-only filter never reads.
CONFIG_BASENAMES = ("Makefile", "Dockerfile")

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
    # Manifests cannot read JSON at parse time; pinned by a test below instead.
    "pyproject.toml",
    "sphinx-kataglyphis-theme/pyproject.toml",
    # These tests, which necessarily name the values they check.
    "tests/test_identity_is_single_source.py",
}

# CV sections name the institute as prose with another meaning; only that key is exempt there.
EXEMPT_PROSE_PREFIX = ("data/cv/section_",)
EXEMPT_PROSE_KEYS = frozenset({"institute"})

# Values distinctive enough that a match means it was typed; first or last name alone is not.
SCANNED = ("name", "email", "contact_email", "url", "url_display", "github_url", "institute")


def _tracked_config_files(prose_exempt_key: str | None = None) -> list[str]:
    """Tracked files a build reads; CV prose is skipped only for a *prose_exempt_key*."""
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    skip_prose = prose_exempt_key in EXEMPT_PROSE_KEYS
    return [
        p
        for p in out
        if (p.endswith(CONFIG_SUFFIXES) or p.rsplit("/", 1)[-1] in CONFIG_BASENAMES)
        and p not in EXEMPT
        and not (skip_prose and p.startswith(EXEMPT_PROSE_PREFIX))
        # git ls-files still lists a deleted but unstaged file.
        and (REPO_ROOT / p).is_file()
    ]


def _code_of(rel: str) -> str:
    """*rel* without whole-line comments, which document a value rather than copy it."""
    text = (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace")
    return "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(("%", "#", "//"))
    )


@pytest.mark.parametrize("key", SCANNED)
def test_no_config_file_hardcodes_an_identity_value(key: str):
    value = IDENTITY[key]
    offenders: list[str] = []
    for rel in _tracked_config_files(prose_exempt_key=key):
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        # A comment naming a value documents it; it is not a copy the build reads.
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


def test_no_config_file_writes_the_name_with_a_separator():
    r"""A filename-safe spelling is still the name; no \b anchors, as _ is a word character."""
    first, last = IDENTITY["first_name"], IDENTITY["last_name"]
    joined = re.compile(re.escape(first) + r"[_.\-]" + re.escape(last), re.IGNORECASE)
    offenders = [rel for rel in _tracked_config_files() if joined.search(_code_of(rel))]
    assert not offenders, (
        f"these spell the author's name into a value: {offenders}. Build it "
        "from identity.first_name / identity.last_name instead -- see the "
        "CV basename in scripts/build_in_container.sh."
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


# The manifests EXEMPT excuses, each checked below, so the exemption buys a pin, not a blind spot.
PINNED_MANIFESTS = ("pyproject.toml", "sphinx-kataglyphis-theme/pyproject.toml")


@pytest.mark.parametrize("manifest", PINNED_MANIFESTS)
def test_the_package_manifest_agrees_with_the_identity(manifest: str):
    """A pyproject.toml cannot be generated, so it is checked instead."""
    text = (REPO_ROOT / manifest).read_text(encoding="utf-8")
    authors = re.search(r"authors\s*=\s*\[\s*\{([^}]*)\}", text)
    assert authors, f"{manifest} has no authors entry"
    assert IDENTITY["name"] in authors.group(1), manifest
    assert IDENTITY["email"] in authors.group(1), manifest
    assert f'Homepage = "{IDENTITY["url"]}"' in text, (
        f"{manifest} Homepage must be {IDENTITY['url']}, the identity's URL"
    )
    assert f'Repository = "{IDENTITY["github_url"]}/' in text, (
        f"{manifest} Repository must sit under {IDENTITY['github_url']}"
    )


def test_every_exempt_manifest_is_actually_pinned():
    """An exempt manifest must be paid for by the pin above."""
    manifests = {p for p in EXEMPT if p.endswith((".toml", ".cfg"))}
    assert manifests <= set(PINNED_MANIFESTS), (
        f"exempt but unpinned: {sorted(manifests - set(PINNED_MANIFESTS))}; "
        "add them to PINNED_MANIFESTS or stop exempting them"
    )


def test_the_latex_identity_file_defines_every_macro_the_templates_use():
    """A template using an undefined macro renders the macro name, or errors."""
    generated = (REPO_ROOT / "md2pdfLib" / "style" / "brand-identity.tex").read_text("utf-8")
    defined = set(re.findall(r"\\providecommand\{\\(\w+)\}", generated))

    # Only macros this file owns: `\\brand*` also matches the font and code-box macros.
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


# Assembled URLs (a prefix plus an argument), which a whole-value scan cannot see


def test_no_template_builds_a_github_url_by_hand():
    r"""Only brand-identity.tex names this brand's GitHub URL; www.github.com is always wrong."""
    own = r"https?://(?:www\.)?github\.com/" + re.escape(IDENTITY["github"])
    offenders = []
    for rel in _tracked_config_files():
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        code = "\n".join(
            line
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
            if not line.lstrip().startswith(("%", "#", "//"))
        )
        if re.search(own, code) or re.search(r"https?://www\.github\.com", code):
            offenders.append(rel)
    assert not offenders, (
        f"these build this brand's GitHub URL by hand: {offenders}. "
        r"Use \brandGithubUrl, \github{<repo>} or \githubProfile instead."
    )


def test_no_template_writes_the_handle_as_a_path_prefix():
    r"""`\github{Kataglyphis/Thing}` spelled the handle out ten times in the CV."""
    handle = IDENTITY["github"]
    offenders = []
    for rel in _tracked_config_files():
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        code = "\n".join(
            line
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
            if not line.lstrip().startswith(("%", "#", "//"))
        )
        if f"{{{handle}/" in code:
            offenders.append(rel)
    assert not offenders, (
        f"these pass the handle as part of an argument: {offenders}. "
        r"\github{<repo>} prefixes the owner from the brand."
    )


def test_the_personal_site_is_never_linked_over_http():
    """The CV linked http://www.<host> -- insecure, and a host spelling of its own."""
    host = IDENTITY["url_display"]
    offenders = []
    for rel in _tracked_config_files():
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        code = "\n".join(
            line
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
            if not line.lstrip().startswith(("%", "#", "//"))
        )
        if re.search(r"http://(?:www\.)?" + re.escape(host), code):
            offenders.append(rel)
    assert not offenders, (
        f"these link this brand's site over plain HTTP: {offenders}; " + r"use \brandUrl"
    )


def test_the_social_layer_is_defined_exactly_once():
    r"""Shared social macros live once, never as a copy per document class."""
    classes = [
        REPO_ROOT / "md2pdfLib" / "book" / "template" / "latex" / "bookclass.cls",
        REPO_ROOT / "md2pdfLib" / "cv" / "template" / "latex" / "myCV_METADATA.cls",
    ]
    definition = re.compile(r"\\(?:new|renew|provide)command\*?\s*\{?\\([a-zA-Z@]+)\}?")
    defined = []
    for path in classes:
        code = "\n".join(
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("%")
        )
        defined.append(set(definition.findall(code)))

    shared = defined[0] & defined[1]
    assert not shared, (
        f"these commands are defined in both document classes: {sorted(shared)}. "
        "Shared macros belong in md2pdfLib/common/latex/, which both classes input."
    )
