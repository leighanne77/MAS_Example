"""The export is generated, never edited — a drift gate.

`wheeler_creek_output.html` is committed so a reader can see the output without running
anything. That convenience creates the classic drift risk: the artifact gets hand-edited,
the code moves on, and the repository shows an output its own example can no longer
produce. This test is the contract that closes the gap: the committed file must be
byte-identical to what the example regenerates.

If it fails, regenerate (`PYTHONPATH=src python examples/wheeler_creek.py`) and commit the
result. Never edit the HTML directly — an export you can edit is an export you can quietly
falsify, which is the exact failure mode this repository exists to make impossible.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_committed_export_regenerates_byte_identical(tmp_path, capsys):
    spec = importlib.util.spec_from_file_location(
        "wheeler_creek", ROOT / "examples" / "wheeler_creek.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    committed = mod.OUT.read_bytes()
    mod.OUT = tmp_path / "regenerated.html"
    mod.main()

    assert mod.OUT.read_bytes() == committed, (
        "examples/wheeler_creek_output.html no longer matches what the example produces — "
        "regenerate it (PYTHONPATH=src python examples/wheeler_creek.py) and commit that; "
        "never edit the export by hand")
