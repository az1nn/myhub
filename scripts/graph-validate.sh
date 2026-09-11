#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=engineering-graph python -m validate.validate --repo-root . "$@"
