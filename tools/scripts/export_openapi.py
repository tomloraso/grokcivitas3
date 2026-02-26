"""Export backend OpenAPI schema to web contract path.

Run from repo root:
  uv run --project apps/backend python tools/scripts/export_openapi.py
"""

from pathlib import Path
import json

from bootstrap_app.api.main import app


def main() -> None:
    schema = app.openapi()
    out = Path("apps/web/src/api/openapi.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
