---
name: circuit-diagram-refiner
description: Create, verify, and iteratively refine publication-quality electrical circuit schematics (digital logic, combinational and sequential circuits, analog, power, mixed-signal) with LaTeX TikZ and CircuiTikZ. Use when asked to draw, reproduce, fix, or audit circuit diagrams and deliver clean PDF/PNG/TEX with accurate net connections, orthogonal routing, readable labels, and visual quality assurance.
license: MIT
compatibility: Requires a terminal with LaTeX (TikZ, CircuiTikZ, standalone), Python 3.9+, and preferably Poppler (pdftoppm); image-reading capability in the host agent is essential for visual review. PyMuPDF and Pillow are optional.
metadata:
  author: OpenAI
  version: "1.0.0"
---

# Circuit Diagram Refiner

Produce **electrically correct, readable, publication-ready** diagrams. Work on the actual rendered image, not just valid LaTeX. This skill applies to digital logic, analog, mixed-signal, power, and general schematics. Use the full review loop below for every delivered diagram.

## Scope and non-negotiables

- Preserve the specified **topology, connectivity, pin polarity, power rails, units, component values, signal names, net labels, and truth/transfer behavior**. Never silently redesign a circuit for aesthetics.
- An aesthetically plausible diagram can be electrically wrong; a successful compile does not demonstrate electrical correctness. Check both independently.
- Prefer proper TikZ/CircuiTikZ symbols and exact pin anchors. Do not manually draw standard circuit symbols unless essential and validated.
- Enforce **no accidental wire-to-wire, label-to-wire, component-to-wire, or label-to-label overlaps**. Orthogonal wiring is preferred, not a mandate that distorts circuit meaning. A junction is a filled dot; an ordinary crossing must be unambiguously nonconnected. Never imply electrical contact through visual proximity alone.
- No invented symbols, labels, component values, IC pinouts, or hidden electrical connections. When requirements are genuinely underspecified, state assumptions.
- If the host agent cannot access rendered PNGs, it **cannot honestly claim the visual audit passed**. Return a clearly labeled unverified result and instructions instead.

## 0. Preflight (once per working environment)

Run from this skill folder:

```bash
python3 scripts/doctor.py
```

Ensure `pdflatex` or `lualatex`, TikZ, CircuiTikZ, and `standalone` exist. `pdftoppm` is preferred. No EDA suite or additional graph-layout package is required for small/medium diagrams. When circuits have dozens of modules or hundreds of wires, consider graph-layout algorithms or manually structured hierarchical subcircuits; Graphviz is optional and **does not validate electrical connectivity**.

## 1. Parse the specification into a connectivity model (BEFORE coordinates)

1. Identify each physical component, symbol, port, named net, power rail and ground reference.
2. Make a concise pin-to-net table. For every connection, record endpoints. For multi-bit buses, include exact bit indices and bit order. For DFFs, record active edges and asynchronous/synchronous control polarity. For analog circuits, record junctions and reference grounds explicitly.
3. Optionally write JSON per `assets/netlist.example.json`, then run:

```bash
python3 scripts/validate_netlist.py path/to/netlist.json
```

This validator detects duplicates, missing pins and conflicting net assignments (declare intentionally unused pins in `no_connect`), **not actual correctness against the circuit problem or TikZ geometry**. Never treat it as a simulation, ERC, or proof that the rendered drawing matches the netlist.
4. Choose the correct circuit representation. A symbolic block diagram is not interchangeable with a gate-level schematic; a functional timing diagram is not an electrical schematic.

## 2. Design a layout before writing long wire paths

Read `references/LAYOUT_PLAYBOOK.md` and `references/CIRCUIT_CONVENTIONS.md` selectively.

- Pick signal flow: left-to-right for combinational paths; show sequential feedback clearly; analog circuitry follows common schematic conventions (e.g. supply top, ground bottom) rather than forcing left-to-right everything.
- Group stages, align anchors, and budget **separate lanes for feedback and crossing-sensitive nets**. Choose a consistent grid (e.g. 0.5 or 1.0 cm) and minimum spacing. Reserve space for long pin labels and component annotations.
- Use named coordinates and anchors (`(U1.in+)`, `(U1.out)`, `(A.output)`), `|-` / `-|` routing, and distinct junction dots. Avoid geometric tricks that look connected but are not.
- Layout wide rather than stuffing symbols tightly. Favor generous whitespace, uniform line weight, font size, and element scale. Keep standard symbol orientations.
- **Topology comes first**: never resolve a visual collision by joining, removing, rerouting to the wrong pin, or changing a net.

## 3. Write the LaTeX source

Start from `assets/logic.tex` or `assets/analog.tex` when useful. Prefer `standalone` so the resulting PDF is tightly cropped. Use standard LaTeX math for signal names and clear sub/superscripts. Emit self-contained source; do not assume undocumented custom LaTeX packages. Mark every intentional junction visibly. Avoid ambiguous touching between crossing wires.

## 4. Compile and render (EVERY revision)

From the skill root:

```bash
python3 scripts/render.py /path/to/circuit.tex --out /path/to/reviews/round01 --engine pdflatex --dpi 220
```

The script writes a fresh PDF, high-resolution PNG(s), compiler log, and `render_report.json`. It uses a clean temporary build directory to avoid accepting stale outputs. Fix all compilation errors. If fonts, external packages or labels cannot render correctly, do not accept the revision.

Optional PDF analysis (requires PyMuPDF):

```bash
python3 scripts/audit_pdf.py /path/to/reviews/round01/circuit.pdf --out /path/to/reviews/round01
```

This yields `audit.json` and annotated PNG(s) with **heuristic** overlap warnings. It may report intended graphics near labels or miss semantic errors; treat it as an assistant, not the final judge.

## 5. VISUAL REVIEW — mandatory agent step

**Actually open or inspect the rendered PNG via the host's image-viewing tool.** Inspect overall figure and zoomed details. Check the criteria in `references/REVIEW_STANDARD.md`:

1. **Electrical correctness**: trace each net visually from source to each sink against the pin-to-net table; verify junctions/crossings, power/ground and polarity. A check of `netlist.json` alone is insufficient.
2. **Geometry**: wires do not pass through symbols, text, unrelated pins, or other wires except deliberate clearly marked crossings/junctions. No crooked, floating, near-miss endpoints or stray segments.
3. **Legibility**: readable text at normal use size, no touching labels, unclipped annotation, unambiguous inversion bubbles, clock wedges, polarity symbols and supply rails.
4. **Composition**: evenly aligned functional groups, limited line crossings and bend count, visually balanced margins, legible signal flow, not excessive white space.
5. **Circuit-type checklist**: digital vs analog vs mixed-signal requirements in `references/CIRCUIT_CONVENTIONS.md`.

Do **not** infer diagram quality from TeX code alone. Record concrete observations, e.g. "CLK wire crosses DFF label", not "looks poor".

## Review-cycle helper (recommended for auditable repeatability)

For a machine-readable revision history, use `scripts/cycle.py` instead of ad hoc round folders:

```bash
python3 scripts/cycle.py render /path/to/circuit.tex --workspace /path/to/reviews
# OPEN AND REALLY INSPECT /path/to/reviews/round01/circuit.png
# Fill assets/review.template.json truthfully with gate booleans, detailed notes and scores.
python3 scripts/cycle.py review --workspace /path/to/reviews --file /path/to/review.json
# On failure: revise .tex and repeat render -> image inspection -> review.
# On success: approved .tex/.pdf/.png appear in reviews/final/.
```

This script never calls a vision model. It enforces that an **explicit agent-rendered-image review** is recorded and that final artifacts match reviewed source hashes. Merely setting booleans to true without viewing the PNG violates this skill. Never report acceptance solely from `audit_pdf.py`.

## 6. Revise and repeat until the gate passes

Cycle: **source → compile → PNG → inspect → defect list → surgical source edits → recompile → re-inspect**.

- First repair electrical hazards, then text/geometry collisions, then composition, then minor polish.
- Keep a `review_notes.md` (or clear agent notes) with pass number, issues found, fixes, outstanding issues and score; do not hide unresolved issues.
- Minimum **two rendered passes** for a newly authored complex schematic (first render and at least one quality-improvement / verification pass). For a trivial diagram that already passes first render, an unchanged second pass is unnecessary.
- Cap unattended iterations at **six** by default; if not passing, report remaining issues rather than pretending completion or looping indefinitely. An agent with time/budget limits may stop earlier but must report status honestly.
- If every criterion passes after a revision, stop. Re-inspect the *final* rendered artifacts, not a prior revision.
- Never "fix" the image in a raster editor while delivering old mismatching `.tex`; the source, PDF, PNG and annotations must correspond.

### Acceptance gate (release only if passed)

- Hard gates: correct topology/net connections, correct symbols/polarity, compilation successful, no cropped content, zero **unintended** intersections and zero unreadable/overlapping text. Every hard gate must pass regardless of a numeric score.
- Soft target: >= 90/100 on the rubric in `references/REVIEW_STANDARD.md` (topology 35, geometry 25, labels 15, readability 15, aesthetics 10).
- Independent visual review is mandatory. The automated PDF audit is advisory and does not automatically certify pass/fail.

## 7. Deliver

Provide at minimum final **`.tex`, `.pdf`, `.png`** and a brief note on topology verification, remaining caveats, and number of review passes. If useful, supply the pin-to-net JSON and reviewer notes as well. Name outputs consistently. **Never call the figure IEEE-certified or standard-compliant solely because it looks professional**; standards differ by circuit domain and publication.

## Example commands

```bash
python3 scripts/doctor.py
python3 scripts/render.py assets/logic.tex  --out examples/logic-run  --dpi 220
python3 scripts/render.py assets/analog.tex --out examples/analog-run --dpi 220
python3 scripts/audit_pdf.py examples/logic-run/logic.pdf --out examples/logic-run
```

See `README.md` for Chinese installation instructions and `references/TROUBLESHOOTING.md` for failures.
