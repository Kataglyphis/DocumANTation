"""Keep the standalone Renovate wrapper usable without a sibling hub checkout."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_missing_hub_bootstraps_and_cleans_up(tmp_path: Path) -> None:
    """A fresh checkout gets the shared driver and preserves its exit status."""
    source = Path(__file__).resolve().parents[1]
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    style = repo / "style"
    scripts.mkdir(parents=True)
    style.mkdir()
    shutil.copy2(source / "scripts/renovate-local.sh", scripts / "renovate-local.sh")
    shutil.copy2(source / "style/brand.json", style / "brand.json")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git_stub = bin_dir / "git"
    git_stub.write_text(
        "#!/usr/bin/env bash\n"
        'printf \'%s\\n\' "$@" > "$RENOVATE_CLONE_LOG"\n'
        "for last; do :; done\n"
        'mkdir -p "$last/linux/scripts"\n'
        "cat > \"$last/linux/scripts/renovate-local.sh\" <<'DRIVER'\n"
        "#!/usr/bin/env bash\n"
        'printf \'%s\\n\' "$@" > "$RENOVATE_DRIVER_LOG"\n'
        'exit "${RENOVATE_DRIVER_EXIT:-0}"\n'
        "DRIVER\n",
        encoding="utf-8",
    )
    git_stub.chmod(0o755)

    scratch = tmp_path / "scratch"
    scratch.mkdir()
    clone_log = tmp_path / "clone.log"
    driver_log = tmp_path / "driver.log"
    env = os.environ.copy()
    env.pop("ANTFRASTRUCTURE_DIR", None)
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "TMPDIR": str(scratch),
            "RENOVATE_CLONE_LOG": str(clone_log),
            "RENOVATE_DRIVER_LOG": str(driver_log),
        }
    )

    subprocess.run(["bash", str(scripts / "renovate-local.sh"), "--help"], check=True, env=env)
    home = json.loads((style / "brand.json").read_text(encoding="utf-8"))["identity"]["github_url"]
    assert f"{home}/ANTfrastructure.git" in clone_log.read_text(encoding="utf-8").splitlines()
    assert driver_log.read_text(encoding="utf-8").splitlines() == [str(repo), "--help"]
    assert not list(scratch.iterdir())

    env["RENOVATE_DRIVER_EXIT"] = "7"
    with pytest.raises(subprocess.CalledProcessError) as failure:
        subprocess.run(["bash", str(scripts / "renovate-local.sh"), "--apply"], check=True, env=env)
    assert failure.value.returncode == 7
    assert not list(scratch.iterdir())
