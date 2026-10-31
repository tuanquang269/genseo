#!/bin/bash
# Launchd stderr is append-only. genseo_errlog_begin trims it once per process
# when stderr is that file, and leaves every other destination alone.
# No launchd, no network, no Shopify.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER="$ROOT/scripts/genseo_errlog.sh"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/genseo-errlog.XXXXXX")" || exit 1
trap 'rm -rf "$WORK"' EXIT
PASS=0
FAIL=0

ok() { PASS=$((PASS + 1)); printf '  ok   %s\n' "$*"; }
bad() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n' "$*"; }

bash -n "$HELPER" && ok "bash -n helper" || bad "bash -n helper"

echo "1. a launchd stderr file is archived, then starts with this run's header"
err="$WORK/launchd-daily.err.log"
printf '%s\n' 'block: command not found' 'the: command not found' >"$err"
(
  # shellcheck source=../scripts/genseo_errlog.sh
  . "$HELPER"
  genseo_errlog_begin "$err"
) 2>>"$err"
if head -n 1 "$err" | grep -q 'launchd stderr for this run'; then
  ok "live file starts with the header"
else
  bad "live file did not start with the header"
  sed 's/^/    | /' "$err"
fi
if grep -q 'command not found' "$err"; then
  bad "stale command-not-found stayed in the live file"
else
  ok "stale command-not-found left the live file"
fi
if grep -q 'block: command not found' "$err.prev" && grep -q 'the: command not found' "$err.prev"; then
  ok "previous bytes are in .prev"
else
  bad "previous bytes were not archived"
fi

echo "2. a second call in the same process does not wipe this run"
err2="$WORK/same-run.err.log"
printf '%s\n' 'OLD' >"$err2"
(
  # shellcheck source=../scripts/genseo_errlog.sh
  . "$HELPER"
  genseo_errlog_begin "$err2"
  printf '%s\n' 'STILL-HERE' >>"$err2"
  genseo_errlog_begin "$err2"
) 2>>"$err2"
if grep -q 'STILL-HERE' "$err2" && head -n 1 "$err2" | grep -q 'launchd stderr for this run'; then
  ok "second call left this run's bytes"
else
  bad "second call wiped this run"
  sed 's/^/    | /' "$err2"
fi

echo "3. stderr pointed at another file does not touch the launchd log"
err3="$WORK/untouched.err.log"
printf '%s\n' 'KEEP-ME' >"$err3"
before=$(cksum "$err3")
(
  # shellcheck source=../scripts/genseo_errlog.sh
  . "$HELPER"
  genseo_errlog_begin "$err3"
) 2>"$WORK/other.err"
if [ "$(cksum "$err3")" = "$before" ] && [ ! -e "$err3.prev" ]; then
  ok "a different stderr left the launchd file alone"
else
  bad "a different stderr rewrote the launchd file"
fi

echo "4. a file over 1MB keeps the head and the tail in .prev"
big="$WORK/big.err.log"
python3 -c 'import sys; p=sys.argv[1]; open(p,"wb").write(b"H"*80000 + b"M"*2000000 + b"T"*80000)' "$big"
(
  # shellcheck source=../scripts/genseo_errlog.sh
  . "$HELPER"
  genseo_errlog_begin "$big"
) 2>>"$big"
if grep -q 'middle trimmed' "$big.prev" \
  && python3 -c 'import sys; d=open(sys.argv[1],"rb").read(); raise SystemExit(0 if d.startswith(b"H"*80) and d.endswith(b"T"*80) else 1)' "$big.prev"; then
  ok "oversized archive kept the head and the tail"
else
  bad "oversized archive was not trimmed"
fi
if head -n 1 "$big" | grep -q 'launchd stderr for this run' && ! grep -q 'MMMM' "$big"; then
  ok "oversized live file is only this run"
else
  bad "oversized live file still holds the old middle"
fi

echo "5. both wrappers rotate before the stable copy, skipping comments"
order_before() {
  local file=$1 early=$2 late=$3 label=$4
  if awk -v early="$early" -v late="$late" '
    /^[[:space:]]*#/ { next }
    index($0, early) && !e { e=NR }
    index($0, late) && !l { l=NR }
    END { exit !(e && l && e < l) }
  ' "$file"; then
    ok "$label"
  else
    bad "$label"
  fi
}
order_before "$ROOT/deploy/grokbot-genseo-daily.sh" "genseo_errlog_begin" "genseo_exec_stable_copy grokbot-genseo-daily" "article errlog is before the stable copy"
order_before "$ROOT/scripts/run_landing_daily.sh" "genseo_errlog_begin" "genseo_exec_stable_copy run_landing_daily" "landing errlog is before the stable copy"

printf '\n%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]
