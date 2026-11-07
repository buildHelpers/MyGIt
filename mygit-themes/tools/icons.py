#!/usr/bin/env python3
"""Generate MyGIt desktop icons without third-party dependencies.

The source identity is assets/MyGIt-icon.svg. This rasterizer reproduces its
rounded indigo tile and white three-node branch for macOS, Windows and Linux.
It writes only to a user-selected, isolated SourceGit build worktree.
"""

from __future__ import annotations

import argparse
import math
import struct
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SIZES = (16, 32, 48, 64, 128, 256, 512, 1024)


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I", len(payload)) + kind + payload +
            struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))


def distance_to_segment(x: float, y: float,
                        x1: float, y1: float, x2: float, y2: float) -> float:
    dx, dy = x2 - x1, y2 - y1
    length2 = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / length2)) if length2 else 0
    return math.hypot(x - x1 - t * dx, y - y1 - t * dy)


def alpha_edge(dist: float, threshold: float, anti_alias: float) -> float:
    return min(1.0, max(0.0, (threshold - dist) / anti_alias + 0.5))


def cubic(t: float) -> tuple[float, float]:
    # SVG M89 138 C139 138 178 123 178 104
    inv = 1 - t
    x = inv**3 * 89 + 3 * inv * inv * t * 139 + 3 * inv * t * t * 178 + t**3 * 178
    y = inv**3 * 138 + 3 * inv * inv * t * 138 + 3 * inv * t * t * 123 + t**3 * 104
    return x, y


BRANCH_SEGMENTS = [
    (cubic(i / 24), cubic((i + 1) / 24)) for i in range(24)
]
NODES = ((89, 59), (89, 195), (178, 90))


def pixel(x: float, y: float, aa: float) -> tuple[int, int, int, int]:
    # Signed-distance rounded square, with a 53-point radius in SVG coordinates.
    dx, dy = abs(x - 128) - 67, abs(y - 128) - 67
    rounded = math.hypot(max(dx, 0), max(dy, 0)) + min(max(dx, dy), 0) - 53
    body = alpha_edge(rounded, 0, aa)
    if body <= 0:
        return 0, 0, 0, 0

    amount = max(0.0, min(1.0, 0.49 * (x / 256) + 0.51 * (y / 256)))
    stops = ((172, 155, 255), (125, 108, 242), (77, 61, 213))
    if amount < 0.47:
        t = amount / 0.47
        first, second = stops[0], stops[1]
    else:
        t = (amount - 0.47) / 0.53
        first, second = stops[1], stops[2]
    rgb = [round((1 - t) * first[k] + t * second[k]) for k in range(3)]

    # Subtle highlight in the top-left corner.
    glow = 0.13 * max(0, 1 - math.hypot(x - 62, y - 48) / 215)
    rgb = [min(255, round(value + (255 - value) * glow)) for value in rgb]

    # Draw branch lines with real geometric anti-aliasing, not image upscaling.
    if 71 <= x <= 197 and 42 <= y <= 213:
        line = distance_to_segment(x, y, 89, 73, 89, 180)
        for p1, p2 in BRANCH_SEGMENTS:
            line = min(line, distance_to_segment(x, y, *p1, *p2))
        stroke = alpha_edge(line, 5, aa)
        for cx, cy in NODES:
            ring = abs(math.hypot(x - cx, y - cy) - 14)
            stroke = max(stroke, alpha_edge(ring, 5, aa))
        rgb = [round(color * (1 - stroke) + 255 * stroke) for color in rgb]

    return *rgb, round(255 * body)


def render_png(size: int) -> bytes:
    if size not in SIZES:
        raise ValueError(f"Unsupported icon size: {size}")
    ratio = 256.0 / size
    aa = max(0.25, ratio * 0.85)
    scanlines = bytearray()
    for j in range(size):
        scanlines.append(0)  # PNG filter: none
        y = (j + 0.5) * ratio
        for i in range(size):
            x = (i + 0.5) * ratio
            scanlines.extend(pixel(x, y, aa))
    raw = zlib.compress(bytes(scanlines), level=8)
    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (PNG_SIGNATURE + chunk(b"IHDR", header) + chunk(b"IDAT", raw)
            + chunk(b"IEND", b""))


def make_ico(images: dict[int, bytes]) -> bytes:
    sizes = (16, 32, 48, 64, 128, 256)
    header = struct.pack("<HHH", 0, 1, len(sizes))
    offset = 6 + len(sizes) * 16
    directory = bytearray()
    body = bytearray()
    for size in sizes:
        data = images[size]
        directory += struct.pack("<BBBBHHII", size if size < 256 else 0,
                                 size if size < 256 else 0, 0, 0,
                                 1, 32, len(data), offset)
        body += data
        offset += len(data)
    return header + directory + body


def make_icns(images: dict[int, bytes]) -> bytes:
    names = ((16, b"icp4"), (32, b"icp5"), (64, b"icp6"),
             (128, b"ic07"), (256, b"ic08"),
             (512, b"ic09"), (1024, b"ic10"))
    chunks = b"".join(name + struct.pack(">I", len(images[size]) + 8) +
                      images[size] for size, name in names)
    return b"icns" + struct.pack(">I", len(chunks) + 8) + chunks


def generate(root: Path) -> list[Path]:
    root = root.resolve()
    project = root / "src" / "SourceGit.csproj"
    if not project.is_file() or not (root / "build" / "resources" / "app").is_dir():
        raise ValueError(f"Not a SourceGit checkout: {root}")

    images = {size: render_png(size) for size in SIZES}
    paths = {
        root / "src" / "App.ico": make_ico(images),
        root / "build" / "resources" / "app" / "App.icns": make_icns(images),
        root / "build" / "resources" / "_common" / "icons" / "sourcegit.png": images[512],
    }
    for path, data in paths.items():
        if not path.parent.is_dir():
            raise ValueError(f"Missing expected icon resource directory: {path.parent}")
        path.write_bytes(data)
        print(f"Generated MyGIt icon: {path.relative_to(root)} ({len(data)} bytes)")
    return list(paths)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True,
                        help="New detached SourceGit/MyGIt build worktree")
    args = parser.parse_args()
    try:
        generate(args.root.expanduser())
        return 0
    except (OSError, ValueError) as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
