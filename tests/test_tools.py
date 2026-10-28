"""Offline smoke/unit tests; run: python3 -m unittest discover -s tests -v"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
spec = importlib.util.spec_from_file_location("netlist_validator", SCRIPTS / "validate_netlist.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def run(*argv):
    return subprocess.run([sys.executable, *map(str, argv)], capture_output=True, text=True)


class NetlistTests(unittest.TestCase):
    def setUp(self):
        self.good = json.loads((ROOT / "assets/netlist.example.json").read_text())

    def test_valid_manifest(self):
        errors, warnings = validator.validate(self.good)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_duplicate_pin_on_multiple_nets_detected(self):
        self.good["nets"][0]["pins"].append("FF1.D")
        errors, _ = validator.validate(self.good)
        self.assertTrue(any("multiple times" in x for x in errors))

    def test_unknown_pin_detected(self):
        self.good["nets"][0]["pins"].append("FF1.INVALID")
        errors, _ = validator.validate(self.good)
        self.assertTrue(any("Unknown component/pin" in x for x in errors))


@unittest.skipUnless(shutil.which("pdflatex") and (shutil.which("pdftoppm") or importlib.util.find_spec("fitz")),
                     "LaTeX compiler or PDF renderer unavailable")
class RenderAndCycleTests(unittest.TestCase):
    def test_render_good_and_bad(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            good = run(SCRIPTS / "render.py", ROOT / "assets/logic.tex", "--out", base / "good")
            self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
            self.assertTrue((base / "good/logic.pdf").exists())
            self.assertTrue((base / "good/logic.png").exists())
            broken = base / "broken.tex"
            broken.write_text("\\documentclass{standalone}\\begin{document}\\undefinedbadcommand\\end{document}")
            fail = run(SCRIPTS / "render.py", broken, "--out", base / "bad")
            self.assertNotEqual(fail.returncode, 0)
            report = json.loads((base / "bad/render_report.json").read_text())
            self.assertFalse(report["success"])
            self.assertFalse((base / "bad/broken.pdf").exists())

    def test_cycle_fails_closed_then_accepts_with_explicit_review(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "circuit.tex"
            shutil.copy2(ROOT / "assets/analog.tex", source)
            workspace = base / "review-work"
            p = run(SCRIPTS / "cycle.py", "render", source, "--workspace", workspace)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertTrue((workspace / "round01/circuit.png").exists())
            reviews = json.loads((ROOT / "assets/review.template.json").read_text())
            bad_report = base / "first_review.json"
            bad_report.write_text(json.dumps(reviews))
            p = run(SCRIPTS / "cycle.py", "review", "--workspace", workspace, "--file", bad_report)
            self.assertEqual(p.returncode, 3, p.stderr)
            self.assertFalse((workspace / "final").exists())
            # Small cosmetic revision: source hash must correspond to new rendered revision.
            source.write_text(source.read_text() + "% second review pass\n")
            p = run(SCRIPTS / "cycle.py", "render", source, "--workspace", workspace)
            self.assertEqual(p.returncode, 0, p.stderr)
            reviews.update({key: True for key in ("topology_verified", "symbols_and_polarity_correct", "geometry_clear",
                                                   "labels_clear", "crop_clear", "visual_image_inspected")})
            reviews["scores"] = {"topology": 35, "routing": 25, "labels": 15, "readability": 15, "aesthetics": 10}
            reviews["issues"] = []
            reviews["notes"] = "Smoke test only; source is known canonical RC. Human/agent visual verification required in real deployment."
            good_report = base / "second_review.json"
            good_report.write_text(json.dumps(reviews))
            p = run(SCRIPTS / "cycle.py", "review", "--workspace", workspace, "--file", good_report)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertTrue((workspace / "final/circuit.tex").exists())
            self.assertTrue((workspace / "final/circuit.png").exists())
            state = json.loads((workspace / "review_state.json").read_text())
            self.assertEqual(state["accepted_round"], 2)

    def test_cycle_disallows_accepting_outdated_source(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "circuit.tex"
            shutil.copy2(ROOT / "assets/analog.tex", source)
            workspace = base / "review-work"
            self.assertEqual(run(SCRIPTS / "cycle.py", "render", source, "--workspace", workspace).returncode, 0)
            source.write_text(source.read_text() + "% source changed after build\n")
            report = base / "review.json"
            report.write_text((ROOT / "assets/review.template.json").read_text())
            bad = run(SCRIPTS / "cycle.py", "review", "--workspace", workspace, "--file", report)
            self.assertEqual(bad.returncode, 1)
            self.assertIn("Source changed", bad.stderr)


if __name__ == "__main__":
    unittest.main()
