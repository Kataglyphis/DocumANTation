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
# Build inputs with no suffix at all. A suffix-only filter never saw these, and
# the Makefile was carrying `CV_Jonas_Heinle_Mistral_RSE` while every check
# passed -- the file was not being read, not passing a read.
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
#
# Scoped to the keys that genuinely appear as prose. It used to exempt those
# files from *every* check, which is why `\github{Kataglyphis/Repo}` -- markup,
# not prose -- sat unnoticed in section_projects.tex ten times over, and why
# the guard written to catch exactly that passed on its own fault injection.
EXEMPT_PROSE_PREFIX = ("data/cv/section_",)
EXEMPT_PROSE_KEYS = frozenset({"institute"})

# Values distinctive enough that finding one in a config file means it was typed
# there. "Jonas"/"Heinle" alone are too short to scan for safely, and the full
# name is the one that mattered.
SCANNED = ("name", "email", "contact_email", "url", "url_display", "github_url", "institute")


def _tracked_config_files(prose_exempt_key: str | None = None) -> list[str]:
    """Tracked files a build reads.

    Args:
        prose_exempt_key: When this identity key is one that legitimately
            appears in CV prose, those section files are skipped. Any other
            check sees them, because markup in them is still markup.
    """
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
        # git ls-files still lists a file deleted but not yet staged, and every
        # caller reads what it returns.
        and (REPO_ROOT / p).is_file()
    ]


def _code_of(rel: str) -> str:
    """*rel*'s content with whole-line comments dropped.

    A comment explaining where a value comes from is documentation, not a second
    copy the build reads. ``#`` covers shell, YAML, TOML and make; ``%`` LaTeX;
    ``//`` the odd JS-flavoured config.
    """
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


def test_no_config_file_writes_the_name_with_a_separator():
    r"""A filename-safe spelling of the name is still the name.

    The scan above looks for ``"Jonas Heinle"`` verbatim. A build output named
    after the author cannot contain a space, so both the container script and
    the Makefile wrote ``CV_Jonas_Heinle_...`` -- the identity, in the one form
    the guard could not see, in the two files it was not reading either.

    Both now build the basename from ``identity.first_name`` /
    ``identity.last_name``, so the name reaches the filename without any caller
    spelling it.

    Separators only, no space: the space spelling is the plain name and belongs
    to the scan above, so each test owns one spelling and a single defect is
    reported once.

    No ``\b`` anchors either. ``_`` is a word character, so ``\bJonas`` never
    matches inside ``CV_Jonas_Heinle_`` -- a first draft of this test anchored
    that way and passed against both real defects it was written for.
    """
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


# Every manifest EXEMPT excuses for being unable to read JSON at parse time.
# Both are checked below, so the exemption buys a pin, not a blind spot -- the
# theme's entry used to be listed here as "pinned instead by
# test_the_package_manifest_agrees_with_the_identity", while that test read only
# the root manifest and the theme's carried no author at all.
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
    """An EXEMPT entry has to be paid for by a check somewhere.

    EXEMPT is the list of files allowed to carry an identity literal. For the
    generated ones the generator is the check; for a manifest it is the test
    above, and nothing previously connected the two lists.
    """
    manifests = {p for p in EXEMPT if p.endswith((".toml", ".cfg"))}
    assert manifests <= set(PINNED_MANIFESTS), (
        f"exempt but unpinned: {sorted(manifests - set(PINNED_MANIFESTS))}; "
        "add them to PINNED_MANIFESTS or stop exempting them"
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


# ── assembled URLs, which a literal scan cannot see ──────────────────────────
#
# The scan above looks for whole identity values. It missed three real defects
# because each built a URL from a prefix plus an argument:
#
#   \github{#1}       -> https://www.github.com/#1     (a host the brand does not use)
#   \personalLink{#1} -> http://www.#1                 (HTTP, plus a www.)
#   \github{Kataglyphis/Repo}                          (the handle, typed ten times)
#
# None of those contains an identity value verbatim, so none tripped the scan.


def test_no_template_builds_a_github_url_by_hand():
    r"""Only brand-identity.tex may name *this* brand's GitHub URL.

    Scoped to the handle on purpose: a third-party GitHub URL is ordinary
    content -- the workflow downloads pandoc from jgm/pandoc, and the scaffold
    writes "org/repo" as a placeholder. Neither is a copy of the identity.
    A www.github.com host is always wrong, though: the brand never uses it,
    and the CV class did.
    """
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
    r"""bookclass and myCV each carried a copy, and \github had drifted apart.

    Same name, different meaning: the book prefixed the profile URL to a repo,
    the CV hardcoded https://www.github.com and took a full path.
    """
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
