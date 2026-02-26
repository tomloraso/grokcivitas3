from __future__ import annotations

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "bootstrap_app"


FORBIDDEN_PREFIXES: dict[str, tuple[str, ...]] = {
    "domain": (
        "bootstrap_app.application",
        "bootstrap_app.adapters",
        "bootstrap_app.api",
        "bootstrap_app.cli",
    ),
    "application": ("bootstrap_app.adapters",),
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_import_boundaries() -> None:
    violations: list[str] = []
    for layer, prefixes in FORBIDDEN_PREFIXES.items():
        layer_path = SRC_ROOT / layer
        for py_file in layer_path.rglob("*.py"):
            for imported in _imports(py_file):
                if imported.startswith(prefixes):
                    violations.append(f"{py_file}: forbidden import {imported}")

    assert not violations, "\n".join(violations)
