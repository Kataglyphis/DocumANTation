"""Every preset must be buildable, and every source must be built by a preset.

Two orphan classes hid here for a long time, both silent:

- ``data/example/`` had no preset at all. Its own getting-started chapter told
  the reader to put their Markdown there and run ``make book`` -- which builds
  ``data/book/`` -- so following the instructions produced nothing.
- ``data/presentation/demo/`` sat one level below the beamer input directory,
  and :func:`get_sorted_markdown_files` lists a single level, so pandoc never
  saw it. Two rotted references (an image that had been deleted and a theme path
  that had moved) lived in it unnoticed, because no build ever read them.

Neither showed up as a failure anywhere. These tests make both impossible: a
preset whose inputs are missing fails, and a Markdown source no preset collects
fails.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from md2pdfLib.pandoc_builder import get_sorted_markdown_files, resolve_project_path
from md2pdfLib.presets import PRESETS

REPO_ROOT = Path(__file__).resolve().parents[1]

# Markdown that is documentation *about* a directory rather than content built
# from it. Anything else under data/ must belong to a preset.
PROSE_EXEMPT = {
    "data/cv/README.md",
    "data/cv/profiles/README.md",
}


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_every_preset_has_the_files_it_names(name: str):
    """A preset naming a path that does not exist fails at build time, in a
    container, on someone else's machine. Catch it here instead."""
    config = PRESETS[name]()

    input_dir = resolve_project_path(config.input_dir)
    assert input_dir.is_dir(), f"{name}: input_dir {config.input_dir} does not exist"
    assert get_sorted_markdown_files(input_dir), f"{name}: no .md sources in {config.input_dir}"

    for field in ("metadata_file", "include_in_header", "highlight_style", "bibliography"):
        value = getattr(config, field)
        if value:
            assert resolve_project_path(value).is_file(), f"{name}: {field} missing: {value}"

    for flag, value in zip(config.extra_args, config.extra_args[1:], strict=False):
        # Only the filter and template paths; the rest of extra_args are values.
        if flag in ("--lua-filter", "--template"):
            assert resolve_project_path(value).is_file(), f"{name}: {flag} missing: {value}"


def _collected_sources() -> set[str]:
    """Every markdown file any preset actually hands to pandoc."""
    collected: set[str] = set()
    for factory in PRESETS.values():
        input_dir = resolve_project_path(factory().input_dir)
        for path in get_sorted_markdown_files(input_dir):
            collected.add(Path(path).resolve().relative_to(REPO_ROOT).as_posix())
    return collected


def test_no_markdown_source_is_orphaned():
    on_disk = {
        p.relative_to(REPO_ROOT).as_posix()
        for p in (REPO_ROOT / "data").rglob("*.md")
        if "out" not in p.relative_to(REPO_ROOT).parts
    }
    orphans = on_disk - _collected_sources() - PROSE_EXEMPT
    assert not orphans, (
        "these Markdown sources are built by no preset, so nothing reads them "
        f"and nothing notices when they rot: {sorted(orphans)}. Add a preset in "
        "md2pdfLib/presets.py, move them under one, or delete them."
    )


def test_a_subdirectory_of_an_input_dir_needs_its_own_preset():
    """The specific trap: get_sorted_markdown_files() does not recurse.

    Dropping a chapter into a subdirectory of an input_dir looks like it should
    work and silently builds nothing, so every such subdirectory must itself be
    some preset's input_dir.
    """
    input_dirs = {resolve_project_path(f().input_dir).resolve() for f in PRESETS.values()}
    for input_dir in sorted(input_dirs):
        for child in sorted(p for p in input_dir.iterdir() if p.is_dir()):
            if not any(child.glob("*.md")):
                continue  # images/, latex/ and friends carry no sources
            assert child.resolve() in input_dirs, (
                f"{child.relative_to(REPO_ROOT).as_posix()} holds Markdown inside "
                f"{input_dir.relative_to(REPO_ROOT).as_posix()}, which is listed one "
                "level deep -- so pandoc never sees it. Give it its own preset."
            )


# ── a preset the user cannot find, or the wrappers cannot build ──────────────
#
# Adding a document type touches six places: presets.py, the Makefile, the
# container script, AGENTS.md, README.md and the docs site. Two targets were
# added and the docs site was missed on the first pass -- the published
# instructions listed four of the six ways to build. Nothing failed, because
# nothing checks prose against code.

MAKEFILE = REPO_ROOT / "Makefile"
CONTAINER_SCRIPT = REPO_ROOT / "scripts" / "build_in_container.sh"
# Where the list of targets is authoritative for a reader.
TARGET_DOCS = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "docs" / "getting-started.md",
)


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_the_makefile_can_build_every_preset(name: str):
    """`make <type>` must work for anything in PRESETS."""
    targets = re.search(r"^DOC_TARGETS\s*=\s*(.+)$", MAKEFILE.read_text("utf-8"), re.M)
    assert targets, "DOC_TARGETS is gone from the Makefile"
    assert name in targets.group(1).split(), (
        f"`make {name}` does not exist: add {name} to DOC_TARGETS in the Makefile"
    )


@pytest.mark.parametrize("name", sorted(PRESETS))
def test_the_container_script_can_build_every_preset(name: str):
    """The script is the documented path; a preset it cannot dispatch is unreachable."""
    script = CONTAINER_SCRIPT.read_text("utf-8")
    cases = re.findall(r"^\s{4}([a-z|]+)\)$", script, re.M)
    dispatchable = {target for case in cases for target in case.split("|")}
    assert name in dispatchable, (
        f"./scripts/build_in_container.sh {name} falls through to usage: "
        f"add a case for it (dispatchable today: {sorted(dispatchable)})"
    )
    # And the usage line has to offer it, or nobody finds it.
    usage = re.search(r"^\s*printf 'Usage: %s (<[^>]+>)", script, re.M)
    assert usage and name in usage.group(1), f"{name} is missing from the usage line"


@pytest.mark.parametrize("doc", [p.name for p in TARGET_DOCS])
def test_every_preset_is_documented(doc: str):
    """A target nobody is told about might as well not exist."""
    path = next(p for p in TARGET_DOCS if p.name == doc)
    text = path.read_text("utf-8")
    missing = sorted(name for name in PRESETS if name not in text)
    assert not missing, f"{doc} never mentions these build targets: {missing}"
