"""Keep AGENTS.md's version table from drifting away from the Dockerfile.

The table calls itself a snapshot, and a snapshot nobody checks goes stale: the
Pandoc and uv rows were both wrong against the Dockerfile they name as the
authority, and they went stale twice in one afternoon because the pins are
synced in from ContainerHub without touching the prose. A doc that confidently
states the wrong version is worse than one that says nothing, so the numbers get
the same treatment as every other derived value in this repo -- checked.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = REPO_ROOT / "Dockerfile"
AGENTS_MD = REPO_ROOT / "AGENTS.md"

# AGENTS.md row label -> the Dockerfile ARG that owns the value.
PINNED_ARGS = {
    "Pandoc": "PANDOC_VERSION",
    "uv": "UV_VERSION",
}


def _dockerfile_arg(name: str) -> str:
    match = re.search(rf"^ARG {name}=(\S+)", DOCKERFILE.read_text(encoding="utf-8"), re.M)
    assert match, f"ARG {name} is gone from the Dockerfile; update AGENTS.md and this test"
    return match.group(1)


def _agents_row(label: str) -> str:
    """The version cell of the AGENTS.md table row for *label*."""
    match = re.search(
        rf"^\|\s*{re.escape(label)}\s*\|\s*([^|]+?)\s*\|",
        AGENTS_MD.read_text(encoding="utf-8"),
        re.M,
    )
    assert match, f"AGENTS.md has no version-table row for {label}"
    return match.group(1)


@pytest.mark.parametrize(("label", "arg"), sorted(PINNED_ARGS.items()))
def test_the_agents_version_table_matches_the_dockerfile(label: str, arg: str):
    assert _agents_row(label) == _dockerfile_arg(arg), (
        f"AGENTS.md says {label} {_agents_row(label)!r} but the Dockerfile pins "
        f"{arg}={_dockerfile_arg(arg)!r}. The Dockerfile is authoritative."
    )


def test_the_base_image_matches_the_dockerfile():
    """The Ubuntu row names the tag in FROM, and two other rows lean on it."""
    from_line = re.search(r"^FROM ubuntu:(\S+)", DOCKERFILE.read_text(encoding="utf-8"), re.M)
    assert from_line, "the Dockerfile no longer starts FROM ubuntu:<tag>"
    assert _agents_row("Ubuntu") == from_line.group(1)
