#!/bin/bash
# Copy deploy/grokbot-genseo-daily.sh to ~/bin/grokbot-genseo-daily.sh.
# launchd (07:30 and 14:47) runs that ~/bin copy. git pull does not update it.
#
# On each Mac, after pull:
#   bash ~/genseo/scripts/install_mac_daily_wrapper.sh
#
# GENSEO_HOME defaults to ~/genseo. Writes only $HOME/bin/grokbot-genseo-daily.sh.
# Does not start launchd, open a network session, or call Shopify.
#
# --dry-run prints the plan and helper status and writes nothing (any OS).
# Offline copy into a temp HOME: bash tests/test_install_mac_daily_wrapper.sh
# That test sets GENSEO_INSTALL_WRAPPER_TEST=1 so the copy can run off Darwin.
# GENSEO_INSTALL_WRAPPER_PRETEND_OS=Linux forces the Mac check to refuse (the test
# only). It cannot be set to Darwin to allow a write.
set -uo pipefail

DRY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    -h|--help)
      printf '%s\n' "usage: bash scripts/install_mac_daily_wrapper.sh [--dry-run]" \
        "GENSEO_HOME defaults to ~/genseo." \
        "Copies deploy/grokbot-genseo-daily.sh to ~/bin/grokbot-genseo-daily.sh." \
        "Does not start launchd."
      exit 0
      ;;
    *)
      printf 'unknown argument: %s\n' "$arg" >&2
      exit 2
      ;;
  esac
done

die() { printf '%s\n' "$*" >&2; exit 1; }

if [ -z "${HOME:-}" ]; then
  die "HOME is unset"
fi
GENSEO_HOME="${GENSEO_HOME:-$HOME/genseo}"
GENSEO_HOME="${GENSEO_HOME%/}"
SRC="$GENSEO_HOME/deploy/grokbot-genseo-daily.sh"
DEST_DIR="$HOME/bin"
DEST="$DEST_DIR/grokbot-genseo-daily.sh"
if [ ! -f "$SRC" ]; then
  die "missing source: $SRC
GENSEO_HOME must be the genseo checkout (default ~/genseo). On the Mac: cd ~/genseo && git pull, then re-run."
fi

missing=0
for rel in scripts/genseo_daily_lock.sh scripts/genseo_group_timeout.sh; do
  if [ -f "$GENSEO_HOME/$rel" ]; then
    printf 'helper %s: present\n' "$rel"
  else
    printf 'helper %s: MISSING\n' "$rel"
    missing=1
  fi
done

needs=0
if grep -q 'genseo_daily_lock.sh' "$SRC" || grep -q 'genseo_group_timeout.sh' "$SRC"; then
  needs=1
fi
if [ "$needs" = 1 ] && [ "$missing" = 1 ]; then
  die "wrapper requires scripts/genseo_daily_lock.sh and scripts/genseo_group_timeout.sh — git pull in $GENSEO_HOME, then re-run. Nothing was copied."
fi
if [ "$missing" = 1 ]; then
  printf '%s\n' "note: this wrapper does not require the daily.lock helpers. A wrapper that references them is not copied while either file is missing."
fi

on_mac=0
if [ "$(uname -s)" = "Darwin" ] && [ "${GENSEO_INSTALL_WRAPPER_PRETEND_OS:-}" != "Linux" ]; then
  on_mac=1
fi
test_mode=0
[ "${GENSEO_INSTALL_WRAPPER_TEST:-0}" = "1" ] && test_mode=1
if [ "$on_mac" != 1 ] && [ "$DRY" != 1 ] && [ "$test_mode" != 1 ]; then
  printf 'refusing: this installer writes ~/bin for launchd on a Mac (uname %s).\n' "$(uname -s)" >&2
  printf '%s\n' "It does not reach the Mac from here. On the Mac: bash ~/genseo/scripts/install_mac_daily_wrapper.sh" >&2
  exit 2
fi

printf 'source: %s\n' "$SRC"
printf 'dest: %s\n' "$DEST"
if [ "$DRY" = 1 ]; then
  printf '%s\n' "dry-run: yes" "executable: not written" "launchd: not started"
  exit 0
fi

if [ -L "$DEST" ]; then
  die "refusing to follow symlink: $DEST"
fi
if [ -e "$DEST" ] && [ ! -f "$DEST" ]; then
  die "dest exists and is not a file: $DEST"
fi

mkdir -p "$DEST_DIR" || die "could not create $DEST_DIR"
tmp=$(mktemp "$DEST_DIR/.grokbot-genseo-daily.XXXXXX") || die "could not stage in $DEST_DIR"
cleanup_tmp() { rm -f "$tmp"; }
trap cleanup_tmp EXIT
install -m 755 "$SRC" "$tmp" || die "copy failed: $SRC -> $DEST"
if [ ! -x "$tmp" ] || ! cmp -s "$SRC" "$tmp"; then
  die "staged copy failed checks"
fi
mv -f "$tmp" "$DEST" || die "could not replace $DEST"
trap - EXIT

if [ ! -x "$DEST" ] || ! cmp -s "$SRC" "$DEST"; then
  die "NOT executable or copy mismatch: $DEST"
fi
printf '%s\n' "executable: yes" "launchd: not started"
exit 0
