#!/usr/bin/env python3
"""Report available dependencies without installing/modifying the host system."""
import importlib.util
import json
import shutil
import subprocess
import sys


def package_exists(tex_file):
    exe = shutil.which("kpsewhich")
    if not exe:
        return None
    try:
        result = subprocess.run([exe, tex_file], capture_output=True, text=True, timeout=15)
        return bool(result.returncode == 0 and result.stdout.strip())
    except (OSError, subprocess.TimeoutExpired):
        return False


def main():
    engines = {name: bool(shutil.which(name)) for name in ("pdflatex", "lualatex", "xelatex")}
    required = {name: package_exists(name) for name in ("tikz.sty", "circuitikz.sty", "standalone.cls")}
    extras = {"pdftoppm": bool(shutil.which("pdftoppm")),
              "pdfinfo": bool(shutil.which("pdfinfo")),
              "pymupdf": bool(importlib.util.find_spec("fitz")),
              "pillow": bool(importlib.util.find_spec("PIL"))}
    can_render = extras["pdftoppm"] or extras["pymupdf"]
    ok = any(engines.values()) and all(v is True for v in required.values()) and can_render
    report = {"status": "ready" if ok else "missing_dependencies",
              "python": sys.version.split()[0], "latex_engines": engines,
              "latex_packages": required, "rendering": extras,
              "note": "A host-agent image viewer is still required for semantic visual QA."}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
