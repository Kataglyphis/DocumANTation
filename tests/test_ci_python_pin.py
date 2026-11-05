"""The lane and the image run only the pinned CPython, never a runner or distro interpreter."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LANE = (REPO_ROOT / ".github/workflows/linux-x64.yml").read_text(encoding="utf-8")
DOCKERFILE = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")


def test_the_lane_runs_both_image_interpreters():
    assert "ci-image-leg.sh pinned " in LANE
    assert "ci-image-leg.sh pinnedt " in LANE
    assert "setup-uv" not in LANE


def test_the_image_venv_uses_the_pin_not_the_distro_python():
    assert "python3-full" not in DOCKERFILE
    assert 'uv venv --managed-python --python "${PYTHON_VERSION}" md2pdf' in DOCKERFILE
