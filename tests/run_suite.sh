#!/bin/bash
# Offline GenSeo suite. Shell tests, then unittest on an interpreter that
# has numpy and PIL. Does not pass --live, does not publish, and does not
# touch launchd, cron, or pmset.
#   bash tests/run_suite.sh
# Bash 3.2.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY=$("$ROOT/tests/python_bin.sh") || exit 1
printf 'python: %s\n' "$PY"

pass_files=0
fail_files=0
for t in "$ROOT"/tests/test_*.sh; do
  name=$(basename "$t")
  printf 'RUN %s\n' "$name"
  if bash "$t"; then
    pass_files=$((pass_files + 1))
  else
    fail_files=$((fail_files + 1))
  fi
done
printf 'SH_FILES pass=%s fail=%s\n' "$pass_files" "$fail_files"

printf 'RUN unittest %s\n' "$PY"
if "$PY" -m unittest discover -s "$ROOT/tests" -p 'test_*.py'; then
  printf 'PY_OK\n'
else
  fail_files=$((fail_files + 1))
  printf 'PY_FAIL\n'
fi

[ "$fail_files" -eq 0 ]
