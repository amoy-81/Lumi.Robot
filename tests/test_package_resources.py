import json
import subprocess
import sys
import zipfile
from importlib import resources
from pathlib import Path


def test_predefined_json_resources_load_independent_of_cwd(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data_pkg = resources.files("lumi.modules.conversation.providers.predefined.data")

    intents = json.loads((data_pkg / "intents.json").read_text(encoding="utf-8"))
    responses = json.loads((data_pkg / "responses.json").read_text(encoding="utf-8"))

    assert isinstance(intents, dict) and "intents" in intents
    assert isinstance(responses, dict) and "responses" in responses


def test_wheel_includes_predefined_json_resources(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            str(repo_root),
            "--no-deps",
            "--no-build-isolation",
            "-w",
            str(tmp_path),
        ],
        check=True,
    )
    wheels = list(tmp_path.glob("lumi_robot-*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as zf:
        names = set(zf.namelist())
    assert "lumi/modules/conversation/providers/predefined/data/intents.json" in names
    assert "lumi/modules/conversation/providers/predefined/data/responses.json" in names
