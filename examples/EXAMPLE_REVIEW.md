# Reference preview QA (verified from rendered PNGs)

## logic.tex -> logic.pdf -> logic.png

- Circuit: positive-edge-triggered D flip-flop; output Q branches to a left-facing inverter; the inverter output feeds D. The Qbar pin is visibly unused.
- Netlist: see `../assets/netlist.example.json` (Q, D and CLK relationships; Qbar explicitly marked no-connect).
- Visual inspection: clock pin wedge visible, clock routing separated from feedback, inverter bubble visible, clear junction dot at the Q feedback branch, no accidental wire crossings or overlapping labels.
- Geometric audit: no text-to-text or text-to-wire candidates in reference compilation.

## analog.tex -> analog.pdf -> analog.png

- Circuit: grounded AC voltage source, series resistor, capacitor shunt to grounded return; output is measured across the capacitor relative to return ground (unloaded RC low-pass).
- Visual inspection: correct source-resistor-capacitor topology, distinct input and output labels, grounded return, capacitor shunt at explicit dot, no textual collisions or cropping.
- Geometric audit: no text-to-text or text-to-wire candidates in reference compilation.

## Limits

These examples demonstrate the working pipeline, **not automatic approval of other diagrams**. For a newly requested diagram, the host Agent must inspect its own newly rendered images, verify the stated problem/topology, and iterate as needed.
