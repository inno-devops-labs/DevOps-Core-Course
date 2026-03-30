#!/usr/bin/env bash
# Repack common-lib for Helm subcharts without macOS AppleDouble files (._*),
# which cause: "chart illegally contains content outside the base directory".
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export COPYFILE_DISABLE=1
xattr -cr common-lib 2>/dev/null || true
find common-lib -name '._*' -delete 2>/dev/null || true
find common-lib -name '.DS_Store' -delete 2>/dev/null || true

OUT="devops-info-service/charts/common-lib-0.1.0.tgz"
rm -f "$OUT" app2-nginx/charts/common-lib-0.1.0.tgz
# GNU/BSD: avoid resource forks in the archive
if tar --help 2>&1 | grep -q no-xattrs; then
  tar --no-xattrs --exclude='.DS_Store' --exclude='._*' -czf "$OUT" common-lib
else
  tar --exclude='.DS_Store' --exclude='._*' -czf "$OUT" common-lib
fi
cp "$OUT" app2-nginx/charts/

echo "OK: $OUT"
shasum -a 256 "$OUT"
echo "If digest changed, update digest lines in devops-info-service/Chart.lock and app2-nginx/Chart.lock"
