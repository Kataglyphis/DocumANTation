"""Every binary asset is referenced by something, or allowlisted below with its reason."""

from __future__ import annotations

import hashlib
import subprocess
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ASSET_SUFFIXES = (".png", ".jpg", ".jpeg", ".svg")

# Copies a mount boundary forces; keep each reason, it says when a copy can go.
DUPLICATED_ON_PURPOSE = {
    frozenset(
        {
            # The raster master; test_theme.py holds the theme's packaged copy to it.
            "images/logo-t3-wireframe.png",
            # setup_theme()'s default logo and favicon; an installed wheel cannot reach images/.
            "sphinx-kataglyphis-theme/sphinx_kataglyphis/logo-t3-wireframe.png",
        }
    ),
    frozenset(
        {
            # bookclass.cls renders it on the book title page, from the mount.
            "md2pdfLib/book/template/latex/logos/Engine_logo.png",
            # data/presentation/latex/main.tex passes it to beamer's \logo.
            "md2pdfLib/presentation/images/logo.png",
        }
    ),
}

# Assets nothing names today, kept for a stated reason rather than deleted.
UNREFERENCED_ON_PURPOSE = {
    # The vector master the raster logos are re-exported from.
    "images/logo-t3-wireframe.svg",
    # myCV_METADATA.cls still offers \photo; only the current CV layout omits it.
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
    """Allowlisted copies must stay byte-identical, since nothing else compares them."""
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


def _jpeg_has_exif(data: bytes) -> bool:
    """True when an APP1 segment before the scan carries an Exif block."""
    i = 2
    while i + 4 <= len(data) and data[i] == 0xFF and data[i + 1] != 0xDA:
        length = int.from_bytes(data[i + 2 : i + 4], "big")
        if data[i + 1] == 0xE1 and data[i + 4 : i + 10] == b"Exif\0\0":
            return True
        i += 2 + length
    return False


def _png_has_exif(data: bytes) -> bool:
    """True when the PNG carries an eXIf chunk."""
    i = 8
    while i + 8 <= len(data):
        length = int.from_bytes(data[i : i + 4], "big")
        if data[i + 4 : i + 8] == b"eXIf":
            return True
        i += 12 + length
    return False


def test_no_raster_asset_carries_exif():
    """Camera EXIF can hold GPS coordinates, and every asset ships publicly."""
    carrying = []
    for rel in _tracked(("*.jpg", "*.jpeg", "*.png")):
        data = (REPO_ROOT / rel).read_bytes()
        if (_png_has_exif if rel.endswith(".png") else _jpeg_has_exif)(data):
            carrying.append(rel)
    assert not carrying, f"strip the EXIF block from: {carrying}"


def test_the_exif_probes_see_a_planted_block():
    """Both probes find a block, so the asset test cannot pass by reading nothing."""
    app1 = b"\xff\xe1" + (8).to_bytes(2, "big") + b"Exif\0\0"
    assert _jpeg_has_exif(b"\xff\xd8" + app1 + b"\xff\xda")
    assert not _jpeg_has_exif(b"\xff\xd8\xff\xe0\x00\x04JF\xff\xda")
    chunk = (0).to_bytes(4, "big") + b"eXIf" + b"\0" * 4
    assert _png_has_exif(b"\x89PNG\r\n\x1a\n" + chunk)
    assert not _png_has_exif(b"\x89PNG\r\n\x1a\n" + chunk.replace(b"eXIf", b"IEND"))
