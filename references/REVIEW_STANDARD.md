# Publication-style circuit drawing acceptance rubric

Use this rubric in addition to subjective inspection. **Hard gates override any score.**

| Category | Weight | Requirements |
|---|---:|---|
| Electrical topology / semantics | 35 | All specified nets and endpoints correct, every required node/port present; current/voltage symbols and polarities correct; clock/reset/control semantics and supply/ground correct |
| Routing and spatial separation | 25 | No unintended overlaps or incidental electrical joins, right-angle routing where feasible, precise pin anchors, clear distinction between crossing and junction, adequate clearance from other components |
| Signal / device labels | 15 | Legible and unambiguous net IDs, component designators, values/units and bit indices; no label collisions or cropped text |
| Readability / scale | 15 | Natural signal flow, functional grouping, consistent conventions, enough space at actual display/print size, no misleading shape or floating wire |
| Composition | 10 | Consistent line weight/symbol sizes, orderly alignments, balanced space and no gratuitous bends |

Scoring rule: Rate each category 0..max, record evidence. Suggested pass >= 90/100, **only after all hard gates** are satisfied.

## Hard failures (automatic reject)

- Net connects to wrong gate input, pin or physical element.
- Junction dot omitted at a visually connected T-intersection, or unintended ambiguous connectivity at crossing.
- Misstated active-low/active-high reset or clock edge; incorrectly oriented diode/transistor/operational amplifier input; absent power rails where necessary to the requested representation.
- Wire through an unrelated device; unreadable overlap between text and wire; labels clipped by page boundary.
- Render or LaTeX compile failure; PDF not corresponding to delivered source.

## Visual inspection at 3 scales

1. Overview — confirm flow, functional grouping, balance and page crop.
2. 100% or intended print scale — confirm every signal name, value and symbol is readable.
3. Zoom 200–400% — trace each pin endpoint, junction and potentially ambiguous crossing.

## Review note format

```
Round: 2
Files: circuit.tex -> circuit.pdf -> circuit.png
Compile: pass
Netlist-vs-render: pass / fail / not verified
Geometry hard gates: pass / fail
Labels/crop hard gates: pass / fail
Score: topology 35/35; routing 23/25; labels 15/15; readability 14/15; aesthetics 9/10 => 96/100
Defects: (1) ... (2) ...
Fixes: ...
Final disposition: pass / revise / cannot verify
```

Automated collisions are **hints**: filled-component outlines, inversion circles, text with diacritical marks and symbol internals can generate false positives. Conversely, actual net/pin mismatches may generate zero PDF-audit warnings. Never claim the score came from a completely automated model-independent judge.
