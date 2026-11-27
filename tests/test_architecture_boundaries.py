import ast
from pathlib import Path


def _owner_context(rel_parts: tuple[str, ...]) -> tuple[str, str | None] | None:
    """Return ('module', mod_name) or ('shared', None) for governed paths, else None."""
    if len(rel_parts) >= 3 and rel_parts[0] == "modules":
        return ("module", rel_parts[1])
    if len(rel_parts) >= 2 and rel_parts[0] == "shared":
        return ("shared", None)
    return None


def _is_forbidden_target(
    target: tuple[str, ...], owner_kind: str, owner_module: str | None
) -> bool:
    if len(target) < 2 or target[0] != "lumi":
        return False
    if owner_kind == "shared":
        return target[1] in {"modules", "controller"}
    if owner_kind == "module":
        if target[1] == "controller":
            return True
        if target[1] == "modules" and len(target) >= 3 and target[2] != owner_module:
            return True
    return False


def _resolve_import_from_base(
    node: ast.ImportFrom, pkg_parts: tuple[str, ...]
) -> tuple[str, ...] | None:
    mod_parts = tuple(node.module.split(".")) if node.module else ()
    if node.level == 0:
        return mod_parts
    up = node.level - 1
    if up > len(pkg_parts):
        return None
    ancestors = pkg_parts[: len(pkg_parts) - up]
    return ancestors + mod_parts


def _iter_forbidden_targets(
    node: ast.AST,
    pkg_parts: tuple[str, ...],
    owner_kind: str,
    owner_module: str | None,
) -> list[str]:
    if isinstance(node, ast.Import):
        return [
            alias.name
            for alias in node.names
            if _is_forbidden_target(tuple(alias.name.split(".")), owner_kind, owner_module)
        ]

    if isinstance(node, ast.ImportFrom):
        base = _resolve_import_from_base(node, pkg_parts)
        if base is None:
            return []
        if _is_forbidden_target(base, owner_kind, owner_module):
            return [".".join(base)]
        return [
            ".".join(base + (alias.name,))
            for alias in node.names
            if alias.name != "*"
            and _is_forbidden_target(base + (alias.name,), owner_kind, owner_module)
        ]

    return []


def find_boundary_violations(src_root: Path) -> list[str]:
    """Return formatted import-boundary violations found under a lumi package root."""
    violations: list[str] = []
    for py_file in sorted(src_root.rglob("*.py")):
        rel = py_file.relative_to(src_root)
        context = _owner_context(rel.parts)
        if context is None:
            continue
        owner_kind, owner_module = context
        pkg_parts = ("lumi", *rel.parts[:-1])
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            for target in _iter_forbidden_targets(node, pkg_parts, owner_kind, owner_module):
                violations.append(f"{rel.as_posix()}:{node.lineno}: forbidden import '{target}'")
    return violations


def test_repo_has_zero_architecture_boundary_violations():
    src_root = Path(__file__).resolve().parents[1] / "src" / "lumi"
    assert find_boundary_violations(src_root) == []


def test_detector_flags_cross_module_and_shared_violations(tmp_path: Path):
    (tmp_path / "modules" / "audio").mkdir(parents=True)
    (tmp_path / "modules" / "speech").mkdir(parents=True)
    (tmp_path / "shared").mkdir(parents=True)

    (tmp_path / "modules" / "audio" / "bad.py").write_text(
        "from lumi.modules.speech import speech_to_text\n", encoding="utf-8"
    )
    (tmp_path / "shared" / "leak.py").write_text(
        "import lumi.controller.robot_controller\n", encoding="utf-8"
    )

    violations = find_boundary_violations(tmp_path)
    assert len(violations) == 2


def test_detector_flags_relative_and_package_level_violations_only(tmp_path: Path):
    (tmp_path / "modules" / "audio").mkdir(parents=True)
    (tmp_path / "modules" / "speech").mkdir(parents=True)
    (tmp_path / "modules" / "face").mkdir(parents=True)
    (tmp_path / "shared").mkdir(parents=True)

    (tmp_path / "modules" / "audio" / "mixed.py").write_text(
        (
            "from . import local_helper\n"
            "from lumi.modules.audio import capture\n"
            "from lumi.shared import AudioData\n"
            "from ..speech import stt\n"
            "from ...controller import ctrl\n"
            "from lumi.modules import speech\n"
            "import lumi.modules.face\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "shared" / "relative_leak.py").write_text(
        "from .. import modules\nfrom lumi import controller\n",
        encoding="utf-8",
    )

    violations = find_boundary_violations(tmp_path)
    assert len(violations) == 6
