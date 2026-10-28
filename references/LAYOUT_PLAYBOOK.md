# Graph layout and routing playbook

## First represent nets, not lines

Represent a schematic as a bipartite graph: components/pins and nets. A wire is a *visual representation of a net*; a net can have multiple endpoints. Split a net into segments only when drawing. Source/sink directions matter for signal flow but are not necessarily the direction of current.

## Layout strategy

1. Rank functional blocks: inputs -> preprocessing -> combinational logic -> state/output (or analog blocks according to signal path).
2. Order within each stage to minimize net crossings. Treat reset/clock/supplies as global special-purpose nets.
3. Reserve orthogonal routing tracks above, below and between blocks. Keep loopbacks and clocks on dedicated lanes.
4. Assign grid coordinates, then reconcile pin-level routing without moving component internals.
5. Add labels only once routes are stable, but reserve approximate label footprint in step 3.

## Routing constraints

- Use mostly horizontal / vertical segments; prefer a small fixed number of bends.
- Do not overlay independent nets on the same line; physical superposition is ambiguous.
- At a branch point, show a filled junction dot; at an unrelated crossing, prefer moving one wire to avoid crossing altogether; if unavoidable, use the circuit convention clearly and consistently.
- Prefer explicit connector/port labels to unnecessarily long wires across a large diagram. However, labels must uniquely define which points share a net.
- No wire may visually connect two pins just because it brushes the symbol perimeter; use explicit anchors.
- Do not automatically join wires at two independent 90-degree bends if they share an accidental coordinate.

## Spacing guidelines (heuristic, not formal standards)

- Keep >= 3 mm separation for parallel signal runs when possible.
- Keep >= 2 mm between ink of labels and unrelated wires at target print scale.
- Around dense digital gates, leave at least a glyph-height of whitespace before unrelated symbols.
- Prefer 0.8–1.2 cm grid pitch in medium figures; increase for long labels or power-device symbols.
- Use text `\small`/`\normalsize` conservatively; after final PDF scaling, do not shrink below the publication's required readable size.

## Signal naming

- Consistent names: `CLK`, `RESET_n`, `Q_0`, `D_0`, `V_{IN}`, `V_{OUT}`, `GND`.
- Overbars or `_n` for active-low, not visually ambiguous apostrophes unless matching the source notation.
- Bit ordering explicit. A four-wire drawing must not be silently replaced with a bus when the user requests individual signals.

## When the circuit is too dense

Option 1: enlarge page/landscape, regroup and reroute. Option 2: use hierarchical modules or named off-page connectors with exact net names, **only if functional representation permits**. Option 3: external graph layout for rough node placement, then manually route pin-aware TikZ edges. Do not treat an automatic graph embedding as proof of correct schematic layout.
