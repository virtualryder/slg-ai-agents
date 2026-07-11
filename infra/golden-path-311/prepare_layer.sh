#!/usr/bin/env bash
# Pre-stage the shared Lambda layer BEFORE `sam build`. Run from this folder.
# Populates layer/python/ with the dependency-free platform_core + governance +
# agent core, so `sam build` needs no `make` and no repo-relative paths (works
# identically on Linux, macOS, Windows, and CI). Mirrors the hcls/hpp pattern.
set -euo pipefail
cd "$(dirname "$0")"
REPO="../.."
rm -rf layer/python
mkdir -p layer/python
cp -r "$REPO/platform_core/slg_agent_platform" layer/python/
cp -r "$REPO/governance" layer/python/
cp "$REPO/aws-native-reference/01-resident-services-311/core.py" layer/python/
echo "layer staged: $(du -sh layer/python 2>/dev/null | cut -f1)"
