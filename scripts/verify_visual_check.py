"""Negative browser proof: clipping and overflow must not be reported as passes."""
import json
from pathlib import Path
import tempfile

from anidiagram.visual_check import visual_check

with tempfile.TemporaryDirectory() as temporary:
    source = Path(temporary) / "overflow.html"
    source.write_text('<!doctype html><html><style>body{margin:0}#stage{width:400px;height:400px;overflow:hidden}</style>'
                      '<div id="stage"><svg xmlns="http://www.w3.org/2000/svg" width="2000" height="1200"><rect width="2000" height="1200" fill="red"/></svg></div></html>')
    result = visual_check(source, viewports="1440x900")
    receipt = json.loads(Path(result["receipt"]).read_text())
    assert result["status"] == "failed", receipt
    assert all(not check["stage_content_contained"] for check in receipt["checks"]), receipt
    assert receipt["visual_review"] == "pending"
    print(json.dumps({"ok": True, "clipped_diagram_rejected": True, "captures": result["captures"]}))
