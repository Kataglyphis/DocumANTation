#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

START_MARKER = "<!-- generated:version-snapshot:start -->"
END_MARKER = "<!-- generated:version-snapshot:end -->"

# Repo root and canonical source paths are configured at runtime from CLI
# arguments (see parse_args / configure_paths) so this generator can run
# against any consuming repository from the shared docs-tooling submodule.
REPO_ROOT = Path.cwd()
VERSIONS_ENV = REPO_ROOT / "linux/scripts/01-core/versions.env"

# ---------------------------------------------------------------------------
# Inline version marker system
#
# In doc files, wrap a version number with paired markers:
#   <!-- generated:cuda -->13.3<!-- /generated:cuda -->
#
# The script replaces the content between markers with the canonical value
# from versions.env, so version references never go stale.
# ---------------------------------------------------------------------------

# marker_name -> (versions.env key, transform)
# transform: 'raw', 'no_v' (strip leading v), 'major', 'major_minor'
INLINE_MARKER_MAP: dict[str, tuple[str, str]] = {
    "cuda": ("CUDA_VERSION", "major_minor"),
    "cuda_full": ("CUDA_VERSION", "raw"),
    "cuda_major_minor": ("CUDA_VERSION_MAJOR_MINOR", "raw"),
    "gstreamer": ("GSTREAMER_VERSION", "no_v"),
    "gstreamer_full": ("GSTREAMER_VERSION", "raw"),
    "llvm": ("LLVM_RELEASE", "raw"),
    "gcc": ("GCC_VERSION", "raw"),
    "gcc_major": ("GCC_VERSION", "major"),
    "cmake": ("CMAKE_VERSION", "raw"),
    "vulkan": ("VULKAN_VERSION", "raw"),
    "python": ("PYTHON_VERSION", "raw"),
    "onnx": ("ONNXRUNTIME_VERSION", "no_v"),
    "onnx_full": ("ONNXRUNTIME_VERSION", "raw"),
    "litert": ("LITERT_VERSION", "no_v"),
    "opencv": ("OPENCV_VERSION", "raw"),
    "node": ("NODE_VERSION", "raw"),
    "uv": ("UV_VERSION", "raw"),
    "android_sdk": ("ANDROID_SDK_VERSION", "raw"),
    "android_ndk": ("ANDROID_NDK_VERSION", "raw"),
    "android_cmake": ("ANDROID_CMAKE_VERSION", "raw"),
    "android_build_tools": ("ANDROID_BUILD_TOOLS", "raw"),
    "android_compile_sdk": ("ANDROID_COMPILE_SDK", "raw"),
    "android_api_level": ("ANDROID_API_LEVEL", "raw"),
    "cudnn": ("CUDNN_VERSION", "raw"),
    "tensorrt": ("TENSORRT_VERSION", "raw"),
    "tvm": ("TVM_REF", "raw"),
    "ubuntu": ("UBUNTU_VERSION", "raw"),
    "onnx_genai": ("ONNXRUNTIME_GENAI_VERSION", "no_v"),
}

INLINE_MARKER_RE = re.compile(r"<!-- generated:(\w+) -->(.*?)<!-- /generated:\1 -->", re.DOTALL)


def transform_value(value: str, transform: str) -> str:
    if transform == "raw":
        return value
    if transform == "no_v":
        return value.lstrip("v")
    if transform == "major":
        return value.split(".")[0]
    if transform == "major_minor":
        parts = value.split(".")
        return ".".join(parts[:2]) if len(parts) >= 2 else value
    return value


def resolve_inline_marker_value(versions: dict[str, str], marker_name: str) -> str | None:
    if marker_name not in INLINE_MARKER_MAP:
        return None
    env_var, transform = INLINE_MARKER_MAP[marker_name]
    raw = versions.get(env_var)
    if raw is None:
        return None
    return transform_value(raw, transform)


def inline_marker_replacement(match: re.Match, versions: dict[str, str]) -> str:
    name = match.group(1)
    resolved = resolve_inline_marker_value(versions, name)
    if resolved is None:
        return match.group(0)
    return f"<!-- generated:{name} -->{resolved}<!-- /generated:{name} -->"


# ---------------------------------------------------------------------------


def read_repo_file(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def extract(pattern: str, text: str, description: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find {description}")
    return match.group(1)


def parse_versions_env() -> dict[str, str]:
    versions_path = VERSIONS_ENV
    if not versions_path.exists():
        raise ValueError(f"Canonical versions file not found: {versions_path}")
    result: dict[str, str] = {}
    for line in versions_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()
        if not key or not value:
            continue
        result[key] = value
    return result


def collect_versions() -> dict[str, str]:
    v = parse_versions_env()

    linux_webserver = read_repo_file("linux/webserver/Dockerfile")
    windows_base = read_repo_file("windows/Dockerfile.base")
    windows_nvidia = read_repo_file("windows/Dockerfile.nvidia")
    windows_media = read_repo_file("windows/Dockerfile.media")
    windows_vs = read_repo_file("windows/scripts/setup-vs.ps1")

    return {
        "linux_ubuntu": v["UBUNTU_VERSION"],
        "linux_cmake": v["CMAKE_VERSION"],
        "linux_vulkan": v["VULKAN_VERSION"],
        "linux_llvm": extract(
            r"(\d+\.\d+\.\d+)",
            v.get("LLVM_RELEASE", "0.0.0"),
            "Linux LLVM version",
        ),
        "linux_gcc": extract(
            r"(\d+)",
            v.get("GCC_VERSION", "0"),
            "Linux GCC major version",
        ),
        "android_sdk": v["ANDROID_SDK_VERSION"],
        "android_ndk": v["ANDROID_NDK_VERSION"],
        "android_cmake": v["ANDROID_CMAKE_VERSION"],
        "webserver_ubuntu": extract(
            r"^FROM ubuntu:([^\s]+)$", linux_webserver, "Webserver Ubuntu version"
        ),
        "windows_ltsc": extract(
            r"^ARG WINDOWS_LTSC=([^\s]+)$",
            windows_base,
            "Windows LTSC version",
        ),
        "windows_vulkan": extract(
            r"^ARG VULKAN_VERSION=([^\s]+)$", windows_base, "Windows Vulkan version"
        ),
        "windows_gstreamer": extract(
            r"^ARG GSTREAMER_VERSION=([^\s]+)$", windows_base, "Windows GStreamer version"
        ),
        "windows_cuda": extract(
            r"^ARG CUDA_VERSION=([^\s]+)$", windows_nvidia, "Windows CUDA version"
        ),
        "windows_onnx": extract(
            r"^ARG ONNXRUNTIME_VERSION=([^\s]+)$", windows_media, "Windows ONNX Runtime version"
        ),
        "windows_vs": extract(
            r"Visual Studio\\([0-9]+)\\BuildTools",
            windows_vs,
            "Visual Studio Build Tools major version",
        ),
    }


def render_snapshot() -> str:
    versions = collect_versions()
    return "\n".join(
        [
            START_MARKER,
            "## Source-Controlled Version Snapshot",
            "",
            "This block is generated from the Dockerfiles and setup scripts by `python3 external/Kataglyphis-DocumANTation/docs-tooling/scripts/sync_versions.py --write`.",
            "",
            "| Target | Source-controlled defaults |",
            "| --- | --- |",
            (
                "| Linux base image | "
                f"Ubuntu {versions['linux_ubuntu']}, LLVM/Clang {versions['linux_llvm']}, "
                f"GCC {versions['linux_gcc']}, CMake {versions['linux_cmake']}, "
                f"Vulkan SDK {versions['linux_vulkan']} |"
            ),
            (
                "| Android layer | "
                f"Android SDK {versions['android_sdk']}, NDK {versions['android_ndk']}, "
                f"CMake {versions['android_cmake']} |"
            ),
            f"| Webserver image | Ubuntu {versions['webserver_ubuntu']} |",
            (
                "| Windows build image | "
                f"Windows Server Core LTSC {versions['windows_ltsc']}, "
                f"Visual Studio Build Tools {versions['windows_vs']}, "
                f"Vulkan SDK {versions['windows_vulkan']}, "
                f"GStreamer {versions['windows_gstreamer']}, "
                f"CUDA {versions['windows_cuda']}, "
                f"ONNX Runtime {versions['windows_onnx']} |"
            ),
            END_MARKER,
        ]
    )


# -- Snapshot block helpers -------------------------------------------------


def update_marked_block(file_path: Path, replacement: str) -> bool:
    original = file_path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
    if not pattern.search(original):
        raise ValueError(f"Markers not found in {file_path}")
    updated = pattern.sub(replacement, original, count=1)
    if updated == original:
        return False
    file_path.write_text(updated, encoding="utf-8")
    return True


def is_marked_block_current(file_path: Path, replacement: str) -> bool:
    original = file_path.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
    if not pattern.search(original):
        raise ValueError(f"Markers not found in {file_path}")
    updated = pattern.sub(replacement, original, count=1)
    return updated == original


# -- Inline marker helpers --------------------------------------------------


def inline_marker_target_files() -> list[Path]:
    return sorted(
        path
        for path in (REPO_ROOT / "docs").rglob("*.md")
        if "_build" not in path.parts and ".venv" not in path.parts
    ) + [REPO_ROOT / "README.md", REPO_ROOT / "AGENTS.md"]


def resolve_all_inline_markers(text: str, versions: dict[str, str]) -> str:
    def _replacer(match: re.Match) -> str:
        return inline_marker_replacement(match, versions)

    return INLINE_MARKER_RE.sub(_replacer, text)


def update_inline_markers(file_path: Path, versions: dict[str, str]) -> bool:
    original = file_path.read_text(encoding="utf-8")
    updated = resolve_all_inline_markers(original, versions)
    if updated == original:
        return False
    file_path.write_text(updated, encoding="utf-8")
    return True


def inline_markers_are_current(file_path: Path, versions: dict[str, str]) -> bool:
    original = file_path.read_text(encoding="utf-8")
    updated = resolve_all_inline_markers(original, versions)
    return updated == original


def check_inline_markers(versions: dict[str, str]) -> int:
    stale = []
    for path in inline_marker_target_files():
        if not inline_markers_are_current(path, versions):
            stale.append(str(path.relative_to(REPO_ROOT)))
    if stale:
        print("Inline version markers are stale in:", file=sys.stderr)
        for p in stale:
            print(f"- {p}", file=sys.stderr)
        print(
            "Run: python3 external/Kataglyphis-DocumANTation/docs-tooling/scripts/sync_versions.py --write",
            file=sys.stderr,
        )
        return 1
    print("Inline version markers are up to date.")
    return 0


def write_inline_markers(versions: dict[str, str]) -> int:
    changed = []
    for path in inline_marker_target_files():
        if update_inline_markers(path, versions):
            changed.append(str(path.relative_to(REPO_ROOT)))
    if changed:
        print("Updated inline version markers in:")
        for p in changed:
            print(f"- {p}")
    else:
        print("Inline version markers already up to date.")
    return 0


# -- Deps table (third-party-licenses.md) -----------------------------------

DEPS_START_MARKER = "<!-- generated:deps-table:start -->"
DEPS_END_MARKER = "<!-- generated:deps-table:end -->"
DEPS_JSON_PATH = REPO_ROOT / "docs/deps/deps.json"
DEPS_TABLE_FILE = REPO_ROOT / "docs/third-party-licenses.md"


def configure_paths(repo_root: Path, versions_env: Path | None, deps_json: Path | None) -> None:
    """Point the module-level path globals at the consuming repository."""
    global REPO_ROOT, VERSIONS_ENV, DEPS_JSON_PATH, DEPS_TABLE_FILE
    REPO_ROOT = repo_root.resolve()
    VERSIONS_ENV = (
        versions_env.resolve()
        if versions_env is not None
        else REPO_ROOT / "linux/scripts/01-core/versions.env"
    )
    DEPS_JSON_PATH = (
        deps_json.resolve() if deps_json is not None else REPO_ROOT / "docs/deps/deps.json"
    )
    DEPS_TABLE_FILE = REPO_ROOT / "docs/third-party-licenses.md"


def load_deps_metadata() -> dict:
    import json

    return json.loads(DEPS_JSON_PATH.read_text(encoding="utf-8"))


def resolve_dep_version(entry: dict, versions: dict[str, str]) -> str:
    var = entry.get("var")
    if var and var in versions:
        return versions[var]
    fixed = entry.get("version_fixed")
    if fixed:
        return fixed
    return "—"


def render_deps_table(versions: dict[str, str]) -> str:
    metadata = load_deps_metadata()
    lines: list[str] = [DEPS_START_MARKER]

    for section in metadata["sections"]:
        title = section["title"]
        tag = section.get("tag", "")
        heading = f"## {title}"
        if tag:
            heading += f" (`{tag}`)"
        lines.append("")
        lines.append(heading)
        lines.append("")

        for subsection in section["subsections"]:
            subtitle = subsection["title"]
            df = subsection.get("dockerfile", "")
            sub_heading = f"### {subtitle}"
            if df:
                sub_heading += f" (`{df}`)"
            lines.append(sub_heading)
            lines.append("")
            lines.append("| Software | Version | Repository | License |")
            lines.append("| --- | --- | --- | --- |")

            for entry in subsection["entries"]:
                name = entry["name"]
                ver = resolve_dep_version(entry, versions)
                url = entry.get("url", "")
                lic = entry.get("license", "")
                if url:
                    display = url.replace("https://", "").replace("http://", "").rstrip("/")
                    repo = f"[{display}]({url})"
                else:
                    repo = "—"
                lines.append(f"| {name} | {ver} | {repo} | {lic} |")

            lines.append("")

    lines.append(DEPS_END_MARKER)
    return "\n".join(lines)


def _deps_marker_pattern() -> re.Pattern:
    return re.compile(re.escape(DEPS_START_MARKER) + r".*?" + re.escape(DEPS_END_MARKER), re.DOTALL)


def update_deps_table(file_path: Path, replacement: str) -> bool:
    original = file_path.read_text(encoding="utf-8")
    pattern = _deps_marker_pattern()
    if not pattern.search(original):
        raise ValueError(f"Deps table markers not found in {file_path}")
    updated = pattern.sub(replacement, original, count=1)
    if updated == original:
        return False
    file_path.write_text(updated, encoding="utf-8")
    return True


def is_deps_table_current(file_path: Path, replacement: str) -> bool:
    original = file_path.read_text(encoding="utf-8")
    pattern = _deps_marker_pattern()
    if not pattern.search(original):
        raise ValueError(f"Deps table markers not found in {file_path}")
    updated = pattern.sub(replacement, original, count=1)
    return updated == original


def check_deps_table(versions: dict[str, str]) -> int:
    try:
        replacement = render_deps_table(versions)
    except FileNotFoundError as e:
        print(f"Deps metadata not found: {e}", file=sys.stderr)
        return 1
    try:
        if is_deps_table_current(DEPS_TABLE_FILE, replacement):
            print("Dependency table is up to date.")
            return 0
        print("Dependency table is out of date.", file=sys.stderr)
        print(
            "Run: python3 external/Kataglyphis-DocumANTation/docs-tooling/scripts/sync_versions.py --write",
            file=sys.stderr,
        )
        return 1
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1


def write_deps_table(versions: dict[str, str]) -> int:
    try:
        replacement = render_deps_table(versions)
    except FileNotFoundError as e:
        print(f"Deps metadata not found: {e}", file=sys.stderr)
        return 1
    try:
        if update_deps_table(DEPS_TABLE_FILE, replacement):
            print(f"Updated dependency table in {DEPS_TABLE_FILE.relative_to(REPO_ROOT)}")
        else:
            print("Dependency table already up to date.")
        return 0
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1


# -- Combined flow ----------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync generated documentation version snapshots.")
    parser.add_argument(
        "--check", action="store_true", help="Fail if generated sections are out of date."
    )
    parser.add_argument("--write", action="store_true", help="Rewrite generated sections in place.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Root of the consuming repository (default: current directory).",
    )
    parser.add_argument(
        "--versions-env",
        type=Path,
        default=None,
        help="Path to versions.env (default: <repo-root>/linux/scripts/01-core/versions.env).",
    )
    parser.add_argument(
        "--deps-json",
        type=Path,
        default=None,
        help="Path to deps.json (default: <repo-root>/docs/deps/deps.json).",
    )
    return parser.parse_args()


def target_files() -> list[Path]:
    return [REPO_ROOT / "README.md", REPO_ROOT / "docs/overview.md"]


def check_snapshot(replacement: str) -> int:
    stale_files = [
        str(path.relative_to(REPO_ROOT))
        for path in target_files()
        if not is_marked_block_current(path, replacement)
    ]
    if stale_files:
        print("Generated version snapshot is out of date in:", file=sys.stderr)
        for path in stale_files:
            print(f"- {path}", file=sys.stderr)
        print(
            "Run: python3 external/Kataglyphis-DocumANTation/docs-tooling/scripts/sync_versions.py --write",
            file=sys.stderr,
        )
        return 1
    print("Generated version snapshot is up to date.")
    return 0


def write_snapshot(replacement: str) -> int:
    changed_files = [
        str(path.relative_to(REPO_ROOT))
        for path in target_files()
        if update_marked_block(path, replacement)
    ]
    if changed_files:
        print("Updated generated version snapshot in:")
        for path in changed_files:
            print(f"- {path}")
    else:
        print("Generated version snapshot already up to date.")
    return 0


def determine_mode(args: argparse.Namespace) -> str:
    if args.check and args.write:
        raise ValueError("Use either --check or --write, not both.")
    return "check" if args.check or not args.write else "write"


def main() -> int:
    args = parse_args()
    configure_paths(args.repo_root, args.versions_env, args.deps_json)
    try:
        mode = determine_mode(args)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    versions = parse_versions_env()
    snapshot = render_snapshot()

    if mode == "check":
        result = check_snapshot(snapshot)
        result |= check_inline_markers(versions)
        result |= check_deps_table(versions)
        return result

    result = write_snapshot(snapshot)
    result |= write_inline_markers(versions)
    result |= write_deps_table(versions)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
