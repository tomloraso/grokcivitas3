from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

SCRIPT_PATH = (
    Path(__file__).resolve().parents[4] / "tools" / "scripts" / "verify_source_contracts_runtime.py"
)


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verify_source_contracts_runtime", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        msg = f"Unable to load script module from {SCRIPT_PATH}"
        raise RuntimeError(msg)

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_verify_source_contracts_runtime_passes_against_repo_samples() -> None:
    module = _load_script_module()

    outcome = module.verify_source_contracts_runtime()

    assert outcome.ok
    assert outcome.issues == []
