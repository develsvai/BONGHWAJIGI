#!/usr/bin/env bash
# User-space, CPU-only ELMFIRE synthetic research probe. No service changes.
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec "${ELMFIRE_BOOTSTRAP_PYTHON:-python3}" "$SCRIPT_DIR/elmfire_probe.py" "$@"
