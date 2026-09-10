#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=engineering-graph python -m sync.sync --repo-root . "$@"
