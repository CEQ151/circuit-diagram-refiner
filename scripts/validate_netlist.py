#!/usr/bin/env python3
"""Validate a simple pin-to-net JSON manifest; NOT an ERC or source/layout checker."""
import argparse
import json
from pathlib import Path
import sys


def validate(doc):
    errors, warnings = [], []
    if not isinstance(doc, dict):
        return ["Root must be a JSON object"], []
    if doc.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    components, ports, nets = doc.get("components"), doc.get("ports"), doc.get("nets")
    if not isinstance(components, list) or not isinstance(ports, list) or not isinstance(nets, list):
        return errors + ["components, ports and nets must be arrays"], warnings
    compmap, portmap, no_connect = {}, {}, set()
    for c in components:
        if not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c["id"]:
            errors.append("Each component needs nonempty string 'id'")
            continue
        cid, pins = c["id"], c.get("pins")
        if cid in compmap:
            errors.append(f"Duplicate component ID: {cid}")
        if "." in cid or cid == "PORT":
            errors.append(f"Component ID cannot contain '.' or be PORT: {cid}")
        if not isinstance(pins, list) or not pins or not all(isinstance(p, str) and p and "." not in p for p in pins):
            errors.append(f"Component {cid} needs a nonempty list of pin names")
            continue
        if len(set(pins)) != len(pins):
            errors.append(f"Duplicate pin in {cid}")
        compmap[cid] = set(pins)
        excluded = c.get("no_connect", [])
        if not isinstance(excluded, list) or any(not isinstance(x, str) or x not in pins for x in excluded):
            errors.append(f"Component {cid} no_connect must list its defined pin names")
        else:
            no_connect.update(f"{cid}.{name}" for name in excluded)
    for port in ports:
        if not isinstance(port, dict) or not isinstance(port.get("name"), str) or not port["name"]:
            errors.append("Each port needs nonempty string 'name'")
            continue
        name = port["name"]
        if name in portmap:
            errors.append(f"Duplicate port: {name}")
        if "." in name:
            errors.append(f"Port name cannot contain '.': {name}")
        if port.get("direction") not in ("in", "out", "inout", "passive", "power"):
            errors.append(f"Invalid port direction for {name}")
        portmap[name] = port.get("direction")
    assigned, net_names = {}, set()
    for net in nets:
        if not isinstance(net, dict) or not isinstance(net.get("name"), str) or not net["name"]:
            errors.append("Each net needs nonempty string 'name'")
            continue
        name, pins = net["name"], net.get("pins")
        if name in net_names:
            errors.append(f"Duplicate net: {name}")
        net_names.add(name)
        if not isinstance(pins, list) or not pins:
            errors.append(f"Net {name} needs a nonempty 'pins' array")
            continue
        if len(pins) == 1:
            warnings.append(f"Net {name} only has one endpoint")
        for p in pins:
            if not isinstance(p, str) or p.count(".") != 1:
                errors.append(f"Invalid endpoint {p!r} in {name}; expected component.pin or PORT.name")
                continue
            cid, pin = p.split(".")
            if cid == "PORT":
                if pin not in portmap:
                    errors.append(f"Unknown port endpoint: {p}")
            elif cid not in compmap or pin not in compmap[cid]:
                errors.append(f"Unknown component/pin endpoint: {p}")
            if p in no_connect:
                errors.append(f"Pin {p} is explicitly marked no_connect but also assigned to net {name}")
            if p in assigned:
                errors.append(f"Endpoint {p} appears multiple times: net {assigned[p]} and net {name}")
            assigned[p] = name
    for cid, pins in compmap.items():
        for pin in pins:
            key = f"{cid}.{pin}"
            if key not in assigned and key not in no_connect:
                warnings.append(f"Unconnected component pin: {key} (may be intentionally unused; declare in no_connect)")
    for name in portmap:
        if f"PORT.{name}" not in assigned:
            warnings.append(f"Unconnected external port: {name}")
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path)
    args = parser.parse_args()
    try:
        doc = json.loads(args.json_file.read_text(encoding="utf8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot read JSON: {exc}", file=sys.stderr)
        return 1
    errors, warnings = validate(doc)
    report = {"valid": not errors, "errors": errors, "warnings": warnings,
              "note": "This validator does NOT check actual circuit functionality or rendered connectivity."}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
