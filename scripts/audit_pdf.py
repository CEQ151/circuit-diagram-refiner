#!/usr/bin/env python3
"""Advisory geometric PDF audit, NOT electrical or semantic visual verification.

Uses PyMuPDF (pip install PyMuPDF). Draws magenta boxes for overlapping text
and orange boxes for candidate horizontal/vertical lines that cross text.
False positives are normal near symbols and embedded math typography.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys


def overlap_fraction(a, b):
    area = (a & b).get_area()
    return area / max(0.01, min(a.get_area(), b.get_area()))


def line_through_rect(p1, p2, r, min_length=8.0):
    x1, y1, x2, y2 = p1.x, p1.y, p2.x, p2.y
    if (x2-x1)**2+(y2-y1)**2 < min_length**2:
        return False
    # Restrict to horizontal/vertical wires. Diagonals are often glyph/symbol internals.
    if abs(y2-y1) < 0.4:
        if r.y0 + 0.6 < (y1+y2)/2 < r.y1 - 0.6:
            return max(min(x1, x2), r.x0) < min(max(x1, x2), r.x1) - 1.5
    if abs(x2-x1) < 0.4:
        if r.x0 + 0.6 < (x1+x2)/2 < r.x1 - 0.6:
            return max(min(y1, y2), r.y0) < min(max(y1, y2), r.y1) - 1.5
    return False


def scan_page(page, max_details=80):
    import fitz
    words = []
    for item in page.get_text("words", sort=False):
        if len(item) >= 5 and str(item[4]).strip():
            rect = fitz.Rect(*item[:4])
            if rect.width > 0 and rect.height > 0:
                words.append((rect, str(item[4])))
    collisions = []
    for i, (left, ltext) in enumerate(words):
        for right, rtext in words[i+1:]:
            # LaTeX fragments in the same math expression may overlap slight
            # glyph bounding boxes even if visually well spaced.
            if overlap_fraction(left, right) >= 0.33:
                collisions.append({"type": "text_overlap_candidate", "items": [ltext, rtext],
                                   "bbox": list(left | right)})
                if len(collisions) >= max_details:
                    break
        if len(collisions) >= max_details:
            break
    text_line = []
    line_count = 0
    for shape in page.get_drawings():
        for item in shape.get("items", []):
            if item[0] != "l":
                continue
            line_count += 1
            p1, p2 = item[1], item[2]
            for rect, label in words:
                if line_through_rect(p1, p2, rect):
                    text_line.append({"type": "line_through_text_candidate", "label": label,
                                      "bbox": list(rect)})
                    break
            if len(text_line) >= max_details:
                break
        if len(text_line) >= max_details:
            break
    clip_warnings = []
    for shape in page.get_drawings():
        r = shape.get("rect")
        if r is not None and not page.rect.intersects(r):
            clip_warnings.append(list(r))
            if len(clip_warnings) > 10:
                break
    return {"width_pt": round(page.rect.width, 2), "height_pt": round(page.rect.height, 2),
            "word_count": len(words), "vector_line_segments": line_count,
            "text_overlap_candidates": collisions, "text_line_candidates": text_line,
            "off_page_shape_candidates": clip_warnings,
            "candidates_truncated": len(collisions) >= max_details or len(text_line) >= max_details}


def draw_annotations(page, scan, output, dpi):
    import fitz
    overlay = fitz.open()
    new_page = overlay.new_page(width=page.rect.width, height=page.rect.height)
    new_page.show_pdf_page(new_page.rect, page.parent, page.number)
    for item in scan["text_overlap_candidates"]:
        new_page.draw_rect(fitz.Rect(item["bbox"]), color=(1, 0, 0.8), width=0.6, overlay=True)
    for item in scan["text_line_candidates"]:
        new_page.draw_rect(fitz.Rect(item["bbox"]), color=(1, 0.55, 0), width=0.6, overlay=True)
    new_page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False).save(output)
    overlay.close()


def main(argv=None):
    try:
        import fitz
    except ImportError:
        print("PyMuPDF not installed. Optional: python3 -m pip install PyMuPDF", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=180)
    args = parser.parse_args(argv)
    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    path = args.pdf.expanduser().resolve()
    if not path.is_file():
        print(f"Missing PDF: {path}", file=sys.stderr)
        return 1
    scans = []
    try:
        with fitz.open(path) as doc:
            for i, page in enumerate(doc):
                scan = scan_page(page)
                scan["page"] = i + 1
                annotated = out / f"audit-page-{i+1}.png"
                draw_annotations(page, scan, annotated, args.dpi)
                scan["annotated_image"] = str(annotated)
                scans.append(scan)
    except Exception as exc:
        print(f"PDF audit failed: {exc}", file=sys.stderr)
        return 1
    summary = {"pdf": str(path), "page_count": len(scans), "pages": scans,
               "total_text_overlap_candidates": sum(len(p["text_overlap_candidates"]) for p in scans),
               "total_line_text_candidates": sum(len(p["text_line_candidates"]) for p in scans),
               "disclaimer": "HEURISTIC ONLY: not an electrical validation, not an AI image inspection, and not an automatic pass/fail."}
    (out / "audit.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf8")
    print(f"Advisory audit saved: {out / 'audit.json'}")
    print(f"Candidates: text/text={summary['total_text_overlap_candidates']}, text/line={summary['total_line_text_candidates']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
