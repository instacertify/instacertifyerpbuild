#!/usr/bin/env bash
# Install InstaCertify app into an existing frappe-bench (ERPNext v16).
set -euo pipefail

SITE="${1:-}"
if [[ -z "${SITE}" ]]; then
  echo "Usage: $0 <site-name>"
  exit 1
fi

APP_SRC="$(cd "$(dirname "$0")/.." && pwd)"
BENCH_ROOT="${BENCH_ROOT:-$(pwd)}"

if [[ ! -f "${BENCH_ROOT}/sites/apps.txt" ]]; then
  echo "Run this from your frappe-bench directory (or set BENCH_ROOT)."
  exit 1
fi

if [[ ! -d "${BENCH_ROOT}/apps/instacertify" ]]; then
  ln -s "${APP_SRC}" "${BENCH_ROOT}/apps/instacertify" || cp -a "${APP_SRC}" "${BENCH_ROOT}/apps/instacertify"
fi

grep -qx "instacertify" "${BENCH_ROOT}/sites/apps.txt" || echo "instacertify" >> "${BENCH_ROOT}/sites/apps.txt"

bench pip install -r "${BENCH_ROOT}/apps/instacertify/requirements.txt"
bench --site "${SITE}" install-app instacertify || true
bench --site "${SITE}" migrate
bench build --app instacertify
bench --site "${SITE}" clear-cache

echo "InstaCertify installed on ${SITE}. Open /app/ic-dashboard"
