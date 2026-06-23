#!/usr/bin/env bash
# Package an agent's connector + native Lambdas WITH platform_core/governance vendored.
set -euo pipefail
AGENT="${1:?usage: build_lambdas.sh <agent-id>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/.build/$AGENT"; rm -rf "$BUILD"; mkdir -p "$BUILD"
cp -r "$ROOT/platform_core/slg_agent_platform" "$BUILD/"
cp -r "$ROOT/governance" "$BUILD/"
# WoG saga Lambdas also need the gov_platform package
if [ -d "$ROOT/gov_platform" ]; then cp -r "$ROOT/gov_platform" "$BUILD/"; fi
# flatten the agent lambdas (incl. _shared.py, aws_backends.py) to the zip root
cp -r "$ROOT/aws-native-reference/$AGENT/lambdas/." "$BUILD/"
cp -r "$ROOT/aws-native-reference/$AGENT/core.py" "$BUILD/" 2>/dev/null || true
( cd "$BUILD" && zip -qr "$ROOT/.build/$AGENT-lambdas.zip" . )
echo "built $ROOT/.build/$AGENT-lambdas.zip"
