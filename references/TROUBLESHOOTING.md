# Troubleshooting

- `circuitikz.sty not found`: install the CircuiTikZ package in the existing LaTeX distribution; on a full TeX Live installation it is typically included.
- `standalone.cls not found`: install the `standalone` class or use `article` with `preview`; margins may need custom handling.
- `pdftoppm not found`: install Poppler (macOS Homebrew: `brew install poppler`), or optionally install PyMuPDF (`python3 -m pip install PyMuPDF`) for rendering fallback.
- `audit_pdf.py` missing dependency: `python3 -m pip install PyMuPDF`; this optional script is not needed for the core visual feedback loop.
- `compare_images.py` missing dependency: `python3 -m pip install Pillow`.
- Compilation succeeds but image missing: inspect `render_report.json`, compiler log, and Poppler/PyMuPDF status.
- Compilation fails after revision: fix the specific line using `compile.log`; the renderer does not accept stale PDFs.
- Lines visually overlap labels despite no audit warning: actual raster visual inspection overrides heuristic checks.
- Automatic audit reports hundreds of issues: inspect annotations; PDF vector paths include shapes internal to components. Filter manual false positives rather than moving electrically meaningful lines arbitrarily.
- PDF audit may classify a dot/line near a math text label as a collision; verify at 200% zoom before acting.
- For huge diagrams, split by hierarchy or increase standalone canvas size, but do not silently change requirements.
- An agent without image-reading ability can compile and run approximate geometry checks but **cannot complete the mandatory visual-approval gate**.
