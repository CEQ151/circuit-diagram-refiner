# Circuit-specific review checklists

## Digital combinational

- Gate type, fan-in, bubble placement and output inversion consistent with Boolean expressions.
- All MUX data inputs and select bits connected and ordered by specified binary weight.
- Combinational outputs do not inadvertently require storage; avoid unexplained unconnected pins.
- For named outputs, check signal path logic against equations/truth table when given.

## Sequential logic

- Clock pin triangle / edge, reset/clear/set polarity, asynchronous vs synchronous semantics exact.
- D/Q/Qbar links, feedback networks and enables correctly separated.
- No hidden bus if bit-by-bit wires were requested; data index labels visible.
- Distinct clock distribution and feedback lanes; explicit junctions when one net fans out.

## Analog and mixed-signal

- Correct element type and value/unit; power rails, reference ground and measurement polarity accurate.
- Op-amp inverting (`-`) versus noninverting (`+`) inputs must be unmistakable; feedback returns to intended pin.
- Capacitor and inductor connections, device orientation, resistor taps and current arrows consistent.
- Distinguish ground from earth/chassis when relevant; no implicit shorts between supply rails.
- For transistors/diodes, use accepted symbols with proper emitter/base/collector or drain/gate/source, and arrow direction where applicable.
- Keep component designators distinct from values. Exact numerical values, tolerances and DC/AC annotations matter.

## Power and complex mixed systems

- Distinguish power path, signal path and protective earth when present.
- Keep isolation boundaries / domains visible; do not invent a common ground across galvanic isolation.
- Connector pin numbers, transformer polarity dots, switches and device orientation must be verified.
- When a manufacturer-specific pinout is required, do not invent it: obtain the actual datasheet before declaring the drawing electrically correct.

## General electrical correctness

A drawing is not an electrical rule check (ERC), SPICE verification or HDL simulation. If behavior matters, ask the agent to run an independent simulation when tools are available. Do not infer real-world electrical safety from schematic readability.
