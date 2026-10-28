#!/usr/bin/env python3
"""Agent-driven review-cycle manager. A model MUST inspect rendered PNGs.

'cycle.py' does not call an LLM or claim automated visual understanding.
It tracks immutable revision outputs, associates explicit image-review reports,
and only promotes a verified revision to final/ when gates are acknowledged.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
RUBRIC = {"topology": 35, "routing": 25, "labels": 15, "readability": 15, "aesthetics": 10}
GATES = ("topology_verified", "symbols_and_polarity_correct", "geometry_clear",
         "labels_clear", "crop_clear", "visual_image_inspected")


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_state(workspace):
    statefile = workspace / "review_state.json"
    if not statefile.exists():
        return {"max_rounds": 6, "rounds": [], "accepted_round": None}
    return json.loads(statefile.read_text(encoding="utf8"))


def save_state(workspace, state):
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "review_state.json").write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf8")


def render(args, workspace):
    state = read_state(workspace)
    if state.get("accepted_round") is not None:
        raise ValueError("Already accepted; start a fresh workspace for a new task")
    if state["rounds"] and state["rounds"][-1]["review"] is None:
        raise ValueError("Review the current round before rendering another")
    limit = state.get("max_rounds", args.max_rounds)
    if not state["rounds"]:
        state["max_rounds"] = args.max_rounds
        limit = args.max_rounds
    if len(state["rounds"]) >= limit:
        raise ValueError(f"Reached {limit} rounds. Report outstanding problems; do not claim approval.")
    src = args.source.expanduser().resolve()
    if not src.is_file():
        raise ValueError(f"Source not found: {src}")
    index = len(state["rounds"]) + 1
    folder = workspace / f"round{index:02d}"
    cmd = [sys.executable, str(HERE / "render.py"), str(src), "--out", str(folder),
           "--engine", args.engine, "--dpi", str(args.dpi)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode:
        print(proc.stdout + proc.stderr, file=sys.stderr)
        raise RuntimeError(f"Round {index} compile/render failed; see {folder / 'compile.log'}")
    meta = json.loads((folder / "render_report.json").read_text(encoding="utf8"))
    if not meta["success"]:
        raise RuntimeError("Render report is not successful")
    pngs = [Path(p) for p in meta["images"]]
    audit = subprocess.run([sys.executable, str(HERE / "audit_pdf.py"), meta["pdf"],
                            "--out", str(folder)], capture_output=True, text=True)
    row = {"round": index, "source": str(src), "source_sha256": digest(src),
           "pdf": meta["pdf"], "pdf_sha256": digest(Path(meta["pdf"])),
           "images": [str(p) for p in pngs],
           "image_sha256": {p.name: digest(p) for p in pngs},
           "audit": "done" if audit.returncode == 0 else "unavailable",
           "review": None, "created_utc": datetime.now(timezone.utc).isoformat()}
    state["rounds"].append(row)
    save_state(workspace, state)
    print(f"RENDERED round{index:02d}: {pngs}")
    print("REQUIRED: Open and inspect final PNG(s), check source/netlist, then submit a review JSON.")
    print(f"Review template: {HERE.parent / 'assets' / 'review.template.json'}")
    if audit.returncode:
        print(f"Optional PDF geometry audit unavailable: {audit.stderr.strip()}")
    return 0


def review(args, workspace):
    state = read_state(workspace)
    if not state["rounds"]:
        raise ValueError("No rendered rounds. Run 'render' first.")
    row = state["rounds"][-1]
    if row["review"] is not None:
        raise ValueError("Latest round already reviewed. Render a new revised round.")
    if digest(Path(row["source"])) != row["source_sha256"]:
        raise ValueError("Source changed since rendering. Restore or re-render before review.")
    for p in row["images"]:
        if not Path(p).exists() or digest(Path(p)) != row["image_sha256"][Path(p).name]:
            raise ValueError("Rendered image changed; review must match original rendering.")
    assessment = json.loads(args.file.expanduser().resolve().read_text(encoding="utf8"))
    if not isinstance(assessment, dict):
        raise ValueError("Review must be a JSON object")
    # Explicit traceable review: the host agent must really have opened the image.
    unknown = [key for key in GATES if not isinstance(assessment.get(key), bool)]
    if unknown:
        raise ValueError(f"Missing/invalid boolean gates: {unknown}")
    scores = assessment.get("scores")
    if not isinstance(scores, dict):
        raise ValueError("Review must include scores object")
    for category, maximum in RUBRIC.items():
        score = scores.get(category)
        if not isinstance(score, (float, int)) or isinstance(score, bool) or not 0 <= score <= maximum:
            raise ValueError(f"Score {category} must be a number between 0 and {maximum}")
    issues = assessment.get("issues")
    if not isinstance(issues, list) or any(not isinstance(x, str) for x in issues):
        raise ValueError("Review issues must be an array of strings")
    notes = assessment.get("notes")
    if not isinstance(notes, str) or not notes.strip():
        raise ValueError("Review must include specific nonempty notes")
    total = sum(scores.values())
    accepted = all(assessment[k] for k in GATES) and not issues and total >= 90
    row["review"] = {"accepted": accepted, "score": total, "assessment": assessment,
                     "reviewed_utc": datetime.now(timezone.utc).isoformat()}
    if accepted:
        state["accepted_round"] = row["round"]
        final = workspace / "final"
        final.mkdir(parents=True, exist_ok=True)
        source = Path(row["source"])
        pdf = Path(row["pdf"])
        shutil.copy2(source, final / source.name)
        shutil.copy2(pdf, final / pdf.name)
        for p in row["images"]:
            image = Path(p)
            shutil.copy2(image, final / image.name)
        (final / "review_approval.json").write_text(json.dumps(row["review"], indent=2, ensure_ascii=False), encoding="utf8")
    save_state(workspace, state)
    if accepted:
        print(f"ACCEPTED: round{row['round']:02d}, score {total}/100; final files at {workspace / 'final'}")
    else:
        print(f"REVISE: score {total}/100; gates={all(assessment[k] for k in GATES)}; {len(issues)} issue(s)")
        if len(state["rounds"]) >= state["max_rounds"]:
            print("Round limit reached. Report unresolved defects and do not claim acceptance.")
    return 0 if accepted else 3


def status(workspace):
    state = read_state(workspace)
    print(json.dumps({"max_rounds": state["max_rounds"],
                      "rounds": [{"round": r["round"], "review": None if r["review"] is None
                                  else {"accepted": r["review"]["accepted"], "score": r["review"]["score"]}}
                                 for r in state["rounds"]],
                      "accepted_round": state["accepted_round"]}, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    p = subs.add_parser("render", help="Compile next revision and prepare image for host-agent inspection")
    p.add_argument("source", type=Path)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--engine", choices=["pdflatex", "lualatex", "xelatex"], default="pdflatex")
    p.add_argument("--dpi", type=int, default=220)
    p.add_argument("--max-rounds", type=int, default=6)
    p = subs.add_parser("review", help="Record Agent's ACTUAL image inspection and quality gates")
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--file", type=Path, required=True)
    p = subs.add_parser("status", help="Display current review state")
    p.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    workspace = args.workspace.expanduser().resolve()
    try:
        if args.action == "render":
            if not 1 <= args.max_rounds <= 30:
                raise ValueError("--max-rounds must be between 1 and 30")
            return render(args, workspace)
        if args.action == "review":
            return review(args, workspace)
        return status(workspace)
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
