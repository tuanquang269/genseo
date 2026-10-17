#!/bin/bash
# Trim the launchd StandardErrorPath once per process.
#
# launchd opens logs/launchd-daily.err.log and logs/launchd-landing.err.log
# with O_APPEND and never truncates them. A fixed parse error
# ("block" / "the": command not found) stayed at the top of the article
# file, and perl warnings from genseo_group_timeout.sh sat at the bottom,
# so a later run looked like it still had those failures.
#
# genseo_errlog_begin PATH compares stderr's inode to PATH. When they match,
# the previous bytes are copied to PATH.prev (the middle is trimmed if the
# file is over 1 MB) and fd 2 is truncated. The caller then writes a
# timestamp header. A terminal, a pipe, or a test redirect that is not PATH
# is left alone.
#
# GENSEO_ERRLOG_ROTATED=1 is exported on the first call. A fast-forward
# re-exec keeps that variable, so this run's header is not wiped.
#
# Sourced by the daily wrappers. Do not enable set -e here.

genseo_errlog_begin() {
  local path py rc
  path=${1:-}
  py=${PY:-/usr/bin/python3}
  if [ -z "$path" ]; then
    return 0
  fi
  if [ "${GENSEO_ERRLOG_ROTATED:-}" = 1 ]; then
    return 0
  fi
  export GENSEO_ERRLOG_ROTATED=1
  if [ ! -f "$path" ]; then
    return 0
  fi
  "$py" - "$path" <<'PY'
import os, sys
path = sys.argv[1]
try:
    err = os.fstat(2)
    target = os.stat(path)
except OSError:
    sys.exit(2)
if not os.path.isfile(path):
    sys.exit(2)
if (err.st_dev, err.st_ino) != (target.st_dev, target.st_ino):
    sys.exit(2)
prev = path + ".prev"
if target.st_size > 0:
    try:
        if target.st_size <= 1000000:
            with open(path, "rb") as src, open(prev, "wb") as dst:
                dst.write(src.read())
        else:
            with open(path, "rb") as src:
                head = src.read(80000)
                src.seek(max(0, target.st_size - 80000))
                tail = src.read()
            with open(prev, "wb") as dst:
                dst.write(head)
                dst.write(b"\n--- genseo_errlog: middle trimmed ---\n")
                dst.write(tail)
    except OSError:
        pass
try:
    os.ftruncate(2, 0)
except OSError:
    sys.exit(1)
sys.exit(0)
PY
  rc=$?
  if [ "$rc" -eq 0 ]; then
    printf '%s\n' "[$(date '+%F %T')] --- launchd stderr for this run; previous contents are in ${path##*/}.prev ---" >&2
  fi
  return 0
}
