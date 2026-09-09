from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def export_openapi(output: Path) -> None:
    from app.core.config import Settings
    from app.main import create_app

    # Contract generation uses declared defaults and must not depend on local runtime secrets or overrides.
    settings = Settings.model_construct()
    schema = create_app(settings).openapi()
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(schema, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f"{output.name}.", suffix=".tmp", dir=output.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, output)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the single Backend OpenAPI contract")
    parser.add_argument("--output", type=Path, default=BACKEND_ROOT.parents[1] / "openapi.json")
    args = parser.parse_args()
    export_openapi(args.output)


if __name__ == "__main__":
    main()
