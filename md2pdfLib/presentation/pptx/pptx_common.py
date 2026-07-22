"""Shared helpers for OOXML deck post-processing.

Every module in this package rewrites pptx archives and resolves slide layouts
from zip handles. The two patterns -- read-modify-write on a ZipFile and
layout lookup from a slide's rels part -- were copy-pasted across three
modules before being extracted here.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

_LAYOUT_RELS_RE = re.compile(
    r'Target="\.\./slideLayouts/(slideLayout\d+\.xml)"'
)


def rewrite_zip(deck: Path, updates: dict[str, bytes]) -> None:
    """Rewrite *deck* with *updates* merged into its existing parts.

    Reads the full archive into memory, applies the updates dict, and writes
    the result back. Compression metadata (timestamps, extra fields) is
    preserved for unmodified parts by reading their ZipInfo objects.

    Args:
        deck: Path to the .pptx file to rewrite in-place.
        updates: Mapping of archive filenames to replacement payloads.
            Only listed parts are changed; everything else is copied verbatim.
    """
    with zipfile.ZipFile(deck) as z:
        infos = {i.filename: i for i in z.infolist()}
        existing: dict[str, bytes] = {}
        for name in infos:
            existing[name] = z.read(name)
    existing.update(updates)
    with zipfile.ZipFile(deck, "w", zipfile.ZIP_DEFLATED) as z:
        for name, payload in existing.items():
            z.writestr(infos.get(name, name), payload)


def layout_for(z: zipfile.ZipFile, slide: str) -> str:
    """The XML content of *slide*'s layout part, or ``""`` if unresolvable.

    Walks from a slide part through its rels part to the layout part.
    Returns the decoded XML string, or an empty string when the rels or
    layout part does not exist.

    Args:
        z: An open ZipFile handle (not closed by this function).
        slide: Archive path of the slide part (e.g. ``ppt/slides/slide3.xml``).
    """
    rels = f"ppt/slides/_rels/{slide.rsplit('/', 1)[-1]}.rels"
    if rels not in z.namelist():
        return ""
    target = _LAYOUT_RELS_RE.search(z.read(rels).decode())
    if target is None:
        return ""
    part = f"ppt/slideLayouts/{target.group(1)}"
    return z.read(part).decode() if part in z.namelist() else ""
