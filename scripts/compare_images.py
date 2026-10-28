#!/usr/bin/env python3
"""Create a before/after/difference visual sheet (Pillow optional)."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys


def main(argv=None):
    try:
        from PIL import Image, ImageChops, ImageDraw
    except ImportError:
        print("Pillow is optional; install with: python3 -m pip install Pillow", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    old = Image.open(args.before).convert("RGB")
    new = Image.open(args.after).convert("RGB")
    w = max(old.width, new.width)
    h = max(old.height, new.height)
    a = Image.new("RGB", (w, h), "white")
    b = Image.new("RGB", (w, h), "white")
    a.paste(old, ((w - old.width)//2, (h - old.height)//2))
    b.paste(new, ((w - new.width)//2, (h - new.height)//2))
    diff = ImageChops.difference(a, b)
    sheet = Image.new("RGB", (w*3, h+35), "white")
    for i, pane in enumerate([a, b, diff]):
        sheet.paste(pane, (i*w, 35))
    ImageDraw.Draw(sheet).text((10, 9), "BEFORE                             AFTER                             PIXEL DIFFERENCE", fill="black")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(f"Written {args.out}. Differences alone do NOT indicate visual or electrical correctness.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
