"""Binary assets get the same discipline the brand tokens already get.

``tests/test_generate_style.py`` fails if a colour is declared in brand.json and
nothing reads it, and ``style/generate_style.py --check`` fails if one of the
three generated ``brand.tokens.json`` copies drifts. Nothing applied either rule
to the images, and both failure modes were present:

- The logo was committed **five times**, byte-identical, under five names. None
  was generated and nothing compared them, so updating the brand mark meant
  editing five files and four would have gone stale silently.
- Six images were referenced by nothing at all -- 5.4 MB of a 9.1 MB repo,
  including a single 5.0 MB JPEG that no chapter, template or preset named.
- Four screenshots existed twice, once for the README and once for the Sphinx
  gallery, because the two render from different roots.

These tests are that rule. An asset is either referenced by something, or listed
below with a reason.
"""

from __future__ import annotations

import hashlib
import subprocess
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ASSET_SUFFIXES = (".png", ".jpg", ".jpeg", ".svg")

# Byte-identical copies that have to exist, each because a consumer cannot reach
# the others. The build container mounts only md2pdfLib/ and data/, so a LaTeX
# template cannot read the host-side copy, and the host-side README cannot read
# a path that only exists inside the image.
#
# Keep the *reason*, not just the path: a copy whose consumer goes away is a
# copy to delete, and only the reason says which one that is.
DUPLICATED_ON_PURPOSE = {
    frozenset(
        {
            # README and the Sphinx docs logo/favicon, both host-side.
            "images/logo-t3-wireframe.png",
            # bookclass.cls renders it on the book title page, from the mount.
            "md2pdfLib/book/template/latex/logos/Engine_logo.png",
            # data/presentation/latex/main.tex passes it to beamer's \logo.
            "md2pdfLib/presentation/images/logo.png",
        }
    ),
}

# Assets nothing names today, kept for a stated reason rather than deleted.
UNREFERENCED_ON_PURPOSE = {
    # The vector master the PNG above is exported from. Nothing builds from it
    # yet -- it is what makes re-exporting the raster copies possible at all.
    "images/logo-t3-wireframe.svg",
    # The CV's photo slot: myCV_METADATA.cls defines \photo{<size>}{<file>} and
    # data/cv/cv.tex deliberately omits the call ("dropping it makes
    # \makecvheader give the header block the full width"). The mechanism and
    # the asset are both live; only the current layout declines to use them.
    "data/cv/images/portrait.jpg",
}


def _tracked(patterns: tuple[str, ...]) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", *patterns],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [p for p in out if (REPO_ROOT / p).is_file()]


def _tracked_assets() -> list[str]:
    return _tracked(tuple(f"*{s}" for s in ASSET_SUFFIXES))


def _digest(rel: str) -> str:
    return hashlib.sha256((REPO_ROOT / rel).read_bytes()).hexdigest()


def test_no_asset_is_committed_twice():
    """Two paths with the same bytes are two files to update and one to forget."""
    by_content: dict[str, list[str]] = defaultdict(list)
    for rel in _tracked_assets():
        by_content[_digest(rel)].append(rel)

    unexplained = [
        sorted(paths)
        for paths in by_content.values()
        if len(paths) > 1 and frozenset(paths) not in DUPLICATED_ON_PURPOSE
    ]
    assert not unexplained, (
        f"these assets are byte-identical copies: {unexplained}. Point every "
        "consumer at one path, or -- if a mount boundary genuinely prevents "
        "that -- add the set to DUPLICATED_ON_PURPOSE with the reason."
    )


def test_a_deliberate_duplicate_set_is_still_identical():
    """The allowlist says these are copies; it has to stay true.

    Listing a set here is the point at which the copies stop being compared by
    accident, so compare them on purpose. A logo updated in one root and not the
    others is exactly the drift the allowlist is permitting the *shape* of.
    """
    for group in DUPLICATED_ON_PURPOSE:
        present = sorted(p for p in group if (REPO_ROOT / p).is_file())
        assert present == sorted(group), (
            f"DUPLICATED_ON_PURPOSE lists {sorted(group)}, but only {present} "
            "exist; drop the ones whose consumer is gone"
        )
        digests = {_digest(p) for p in present}
        assert len(digests) == 1, (
            f"{present} are listed as copies of one another but their bytes "
            "differ -- re-export them from the same master"
        )


def test_every_asset_is_referenced_by_something():
    """An asset no source names is weight the clone pays for and nothing renders."""
    text_files = [
        p
        for p in _tracked(("*",))
        if not p.endswith(ASSET_SUFFIXES) and not p.endswith((".pdf", ".lock"))
    ]
    corpus = "\n".join(
        (REPO_ROOT / p).read_text(encoding="utf-8", errors="replace") for p in text_files
    )

    orphans = [
        rel
        for rel in _tracked_assets()
        if rel not in UNREFERENCED_ON_PURPOSE and Path(rel).name not in corpus
    ]
    assert not orphans, (
        f"nothing references these assets: {orphans}. Delete them, or add them "
        "to UNREFERENCED_ON_PURPOSE with the reason they are kept."
    )


def test_the_allowlists_carry_no_entry_that_stopped_applying():
    """An exemption for a file that is gone is an exemption nobody rechecks."""
    listed = set(UNREFERENCED_ON_PURPOSE) | {p for group in DUPLICATED_ON_PURPOSE for p in group}
    missing = sorted(p for p in listed if not (REPO_ROOT / p).is_file())
    assert not missing, f"these are allowlisted but no longer tracked: {missing}"
