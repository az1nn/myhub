#!/usr/bin/env bash
set -euo pipefail

INTEGRATION="${1:-opencode}"

if ! command -v specify >/dev/null 2>&1; then
  echo "Spec Kit CLI ('specify') is not installed."
  echo "Install specify-cli using the official Spec Kit installation instructions."
  exit 1
fi

echo "Initializing Spec Kit with integration: ${INTEGRATION}"
specify init --here --force --integration "${INTEGRATION}"

echo
echo "Review the generated diff, especially .specify/memory/constitution.md."
echo "The MyHub-authored constitution is canonical and must not be silently replaced."
