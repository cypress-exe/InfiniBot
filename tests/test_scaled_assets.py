"""
Tests for the site's scaled-asset manifest and its generator.

``github-pages-site/scale_assets.py`` produces the downscaled image twins that
external listings (discordbotlist) embed. It runs from a workflow on pushes to
main, which means a typo'd path in the manifest wouldn't surface until after a
merge — these tests are the pre-merge guard that catches it instead.

Only the manifest and the pure validation logic are exercised here. Encoding
isn't: it needs ffmpeg and would spend a minute of CI re-crunching 100MB of GIFs
to tell us what the workflow already tells us.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_ROOT = REPO_ROOT / "github-pages-site"
SCRIPT_PATH = SITE_ROOT / "scale_assets.py"

# The container excludes github-pages-site via .dockerignore — the bot image has
# no reason to carry 100MB of demo GIFs — so this module has nothing to test
# when it runs there. Skipping at module level matters: importing the script by
# path would otherwise raise during collection and take the whole suite down
# with it. The host job that gates merges does have the site tree and runs these.
if not SCRIPT_PATH.is_file():
    pytest.skip(
        "github-pages-site/ is not present (excluded from the container image)",
        allow_module_level=True,
    )


def _load_script_module():
    """Import scale_assets.py by path.

    It lives outside the importable source tree (it's site tooling, not bot
    code) and carries a PEP 723 header so it can be run standalone with `uv run`
    without being a project dependency.
    """
    spec = importlib.util.spec_from_file_location("scale_assets", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["scale_assets"] = module
    spec.loader.exec_module(module)
    return module


scale_assets = _load_script_module()


@pytest.fixture(scope="module")
def manifest() -> tuple[str, list]:
    return scale_assets.load_manifest()


def test_manifest_parses(manifest: tuple[str, list]) -> None:
    output_dir, assets = manifest

    assert output_dir == "discordbotlist-variants"
    assert assets, "the manifest should list at least one asset"


def test_every_listed_source_exists(manifest: tuple[str, list]) -> None:
    """The failure this is really here for: a renamed or typo'd image path."""
    _, assets = manifest

    missing = [asset.src.as_posix() for asset in assets if not asset.src_path.is_file()]

    assert missing == [], f"manifest lists sources that don't exist: {missing}"


def test_widths_are_in_a_plausible_range(manifest: tuple[str, list]) -> None:
    """Catches a slipped decimal point or a height pasted into `width`.

    Upscaling is permitted (join-message.png is deliberately enlarged past its
    401px source), so this can't assert the target is smaller. It bounds the
    value instead, and separately flags upscales far beyond their source, where
    the blur would be severe enough to suggest a mistake.

    Read from the PNG/GIF header rather than ffprobe so this needs no ffmpeg.
    """
    _, assets = manifest

    for asset in assets:
        source_width = _read_image_width(asset.src_path)
        assert 16 <= asset.width <= 4000, (
            f"{asset.src.as_posix()}: width {asset.width} is outside the sane range"
        )
        assert asset.width <= source_width * 2, (
            f"{asset.src.as_posix()}: width {asset.width} is more than double "
            f"the source's {source_width}px, which would be badly blurred"
        )


def test_outputs_land_in_the_variants_subdirectory(manifest: tuple[str, list]) -> None:
    output_dir, assets = manifest

    for asset in assets:
        out = asset.out_path(output_dir)
        assert out.parent.name == output_dir
        assert out.parent.parent == asset.src_path.parent
        assert out.name == asset.src.name


@pytest.mark.parametrize(
    ("bad_yaml", "expected_message"),
    [
        ("output_dir: v\nassets: []", "non-empty list"),
        ("output_dir: v\nassets:\n  - {src: a.png, width: 0}", "positive integer"),
        ("output_dir: v\nassets:\n  - {src: a.png, width: true}", "positive integer"),
        ("output_dir: v\nassets:\n  - {src: a.png}", "positive integer"),
        ("output_dir: v\nassets:\n  - {width: 100}", "non-empty string"),
        ("output_dir: v\nassets:\n  - {src: ../escape.png, width: 100}", "relative path"),
        ("output_dir: v\nassets:\n  - {src: a.mp4, width: 100}", "unsupported file type"),
        (
            "output_dir: v\nassets:\n  - {src: a.png, width: 1}\n  - {src: a.png, width: 2}",
            "duplicate",
        ),
        # `fps` was removed when GIFs moved to gifsicle; a stale manifest that
        # still carries it must say so rather than silently ignoring the key.
        ("output_dir: v\nassets:\n  - {src: a.gif, width: 100, fps: 25}", "unknown key"),
        ("output_dir: nested/dir\nassets:\n  - {src: a.png, width: 100}", "single directory name"),
        ("assets:\n  - {src: a.png, width: 100}", "single directory name"),
    ],
)
def test_malformed_manifests_are_rejected(
    tmp_path: Path, bad_yaml: str, expected_message: str
) -> None:
    """Bad config should fail loudly at parse time, not as a cryptic encoder error."""
    manifest_file = tmp_path / "scaled-assets.yml"
    manifest_file.write_text(bad_yaml)

    with pytest.raises(scale_assets.ManifestError, match=expected_message):
        scale_assets.load_manifest(manifest_file)


def test_fingerprint_changes_when_settings_change() -> None:
    """Staleness detection rests on this: same inputs in, same fingerprint out."""
    asset = scale_assets.Asset(src=Path("assets/demos/x.gif"), width=550)
    wider = scale_assets.Asset(src=Path("assets/demos/x.gif"), width=700)

    baseline = scale_assets.fingerprint(asset, "abc123")

    assert scale_assets.fingerprint(asset, "abc123") == baseline
    assert scale_assets.fingerprint(asset, "different-source") != baseline
    assert scale_assets.fingerprint(wider, "abc123") != baseline


def test_fingerprint_pins_the_encoder_settings() -> None:
    """A change to the pipeline must invalidate outputs built by the old one.

    Without this, switching GIFs from ffmpeg to gifsicle would have left every
    existing file in place, since their sources never changed.
    """
    asset = scale_assets.Asset(src=Path("assets/demos/x.gif"), width=550)

    recorded = scale_assets.fingerprint(asset, "abc123")

    assert recorded["pipeline"] == scale_assets.PIPELINE_VERSION
    assert recorded["resize_method"] == scale_assets.RESIZE_METHOD


def test_prune_only_removes_files_the_script_recorded(tmp_path: Path) -> None:
    """Pruning must never reach a file the generator didn't create."""
    output = tmp_path / "dropped.gif"
    output.write_bytes(b"generated")
    bystander = tmp_path / "not-ours.gif"
    bystander.write_bytes(b"hand-placed")

    monkey_root = scale_assets.SITE_ROOT
    scale_assets.SITE_ROOT = tmp_path
    try:
        removed = scale_assets.prune_orphans(
            state={"dropped.gif": {}, "not-ours.gif": {}, "never-existed.gif": {}},
            fresh_state={"not-ours.gif": {}},
        )
    finally:
        scale_assets.SITE_ROOT = monkey_root

    assert removed == ["dropped.gif"]
    assert not output.exists()
    assert bystander.exists(), "a file still in the manifest must survive"


def _read_image_width(path: Path) -> int:
    """Width from a PNG or GIF header, without pulling in an image library."""
    header = path.read_bytes()[:26]

    if header[:8] == b"\x89PNG\r\n\x1a\n":
        # IHDR width is a big-endian uint32 at offset 16.
        return int.from_bytes(header[16:20], "big")
    if header[:6] in (b"GIF87a", b"GIF89a"):
        # Logical screen width is a little-endian uint16 at offset 6.
        return int.from_bytes(header[6:8], "little")

    raise AssertionError(f"unhandled image format for {path}")
