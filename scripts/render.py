#!/usr/bin/env python3
"""Compile a standalone LaTeX schematic in a clean directory and render each page.

Dependency-free core: Python standard library + TeX + pdftoppm OR PyMuPDF.
The .tex is not modified. External LaTeX code is executable input: do not compile
untrusted TeX files without a sandbox (disabling shell escape is not a full sandbox).
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def run_command(args, cwd, timeout):
    try:
        r = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                           errors="replace", timeout=timeout)
        return r.returncode, (r.stdout or "") + "\n" + (r.stderr or "")
    except subprocess.TimeoutExpired as exc:
        return 124, f"TIMEOUT ({timeout}s): {exc}"
    except OSError as exc:
        return 127, f"COMMAND FAILED: {exc}"


def pages_from_pdfinfo(pdf):
    exe = shutil.which("pdfinfo")
    if exe:
        rc, output = run_command([exe, str(pdf)], pdf.parent, 30)
        if rc == 0:
            for line in output.splitlines():
                if line.startswith("Pages:"):
                    try:
                        return int(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass
    try:
        import fitz
        with fitz.open(pdf) as doc:
            return len(doc)
    except ImportError:
        return None


def render_pngs(pdf, out, stem, dpi, n_pages, timeout):
    paths = []
    exe = shutil.which("pdftoppm")
    if exe:
        prefix = out / stem
        if n_pages == 1:
            argv = [exe, "-f", "1", "-singlefile", "-r", str(dpi), "-png", str(pdf), str(prefix)]
        else:
            argv = [exe, "-r", str(dpi), "-png", str(pdf), str(prefix)]
        rc, message = run_command(argv, out, timeout)
        if rc != 0:
            raise RuntimeError(f"pdftoppm failed: {message[-2000:]}")
        paths = ([out / (stem + ".png")] if n_pages == 1 else
                 sorted(out.glob(stem + "-*.png")))
    else:
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("Install Poppler (pdftoppm) or PyMuPDF for rendering") from exc
        with fitz.open(pdf) as doc:
            for i, page in enumerate(doc):
                destination = out / (f"{stem}.png" if len(doc) == 1 else f"{stem}-{i+1}.png")
                page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False).save(destination)
                paths.append(destination)
    if not paths or not all(p.exists() and p.stat().st_size > 0 for p in paths):
        raise RuntimeError("Renderer produced no nonempty PNG(s)")
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Existing .tex source")
    parser.add_argument("--out", type=Path, required=True, help="Revision-specific output directory")
    parser.add_argument("--engine", choices=["pdflatex", "lualatex", "xelatex"], default="pdflatex")
    parser.add_argument("--dpi", type=int, default=220)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)
    src = args.source.expanduser().resolve()
    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    report = {"source": str(src), "engine": args.engine, "dpi": args.dpi,
              "output_directory": str(out), "success": False, "pdf": None,
              "images": [], "page_count": None, "error": None}
    stem = src.stem
    # Remove only this stem's previous outputs, so a failed rebuild cannot leave
    # a visually plausible stale PDF/PNG in the same review directory.
    for stale in [out / f"{stem}.pdf", out / f"{stem}.png", *out.glob(f"{stem}-*.png")]:
        if stale.is_file():
            stale.unlink()
    (out / "compile.log").unlink(missing_ok=True)
    (out / "render_report.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    try:
        if not src.is_file() or src.suffix.lower() != ".tex":
            raise ValueError(f"Expected an existing .tex file: {src}")
        if not 72 <= args.dpi <= 600:
            raise ValueError("--dpi should be between 72 and 600")
        if args.timeout <= 0:
            raise ValueError("--timeout must be positive")
        exe = shutil.which(args.engine)
        if not exe:
            raise RuntimeError(f"Missing LaTeX engine {args.engine}")
        # The temp output directory prevents accidental reuse of stale builds.
        with tempfile.TemporaryDirectory(prefix="schematic-compile-") as temp:
            build = Path(temp)
            cmd = [exe, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
                   "-no-shell-escape", f"-output-directory={build}", src.name]
            rc, message = run_command(cmd, src.parent, args.timeout)
            (out / "compile.log").write_text(message, encoding="utf8")
            pdf_created = build / f"{stem}.pdf"
            if rc != 0 or not pdf_created.is_file() or pdf_created.stat().st_size == 0:
                raise RuntimeError(f"LaTeX failed with exit code {rc}; see compile.log")
            pdf = out / f"{stem}.pdf"
            shutil.copy2(pdf_created, pdf)
        count = pages_from_pdfinfo(pdf)
        report["pdf"] = str(pdf)
        report["page_count"] = count
        images = render_pngs(pdf, out, stem, args.dpi, count, args.timeout)
        report["images"] = [str(p) for p in images]
        report["success"] = True
        print(f"PASS: {pdf}, {len(images)} PNG(s) rendered. Open the PNG(s) and audit visually.")
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        report["error"] = str(exc)
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        report["elapsed_seconds"] = round(time.time() - started, 2)
        (out / "render_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")


if __name__ == "__main__":
    sys.exit(main())
