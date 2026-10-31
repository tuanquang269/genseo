#!/bin/bash
# Print one python3 that can import numpy and PIL.
# Palette tests call landing_palette.extract(), which imports numpy.
# On this Mac, PATH python3 is a shim without numpy; /usr/bin/python3 has it.
# On a Linux checkout whose python3 already has both, that interpreter wins.
# Bash 3.2. GENSEO_PYTHON is tried first when it is set and works.
set -u

try_py() {
  [ -n "${1:-}" ] || return 1
  [ -x "$1" ] || return 1
  "$1" -c 'import numpy, PIL' >/dev/null 2>&1 || return 1
  printf '%s\n' "$1"
  return 0
}

if [ -n "${GENSEO_PYTHON:-}" ]; then
  if try_py "$GENSEO_PYTHON"; then
    exit 0
  fi
fi

path_py=$(command -v python3 2>/dev/null || true)
if try_py "$path_py"; then
  exit 0
fi
if try_py /usr/bin/python3; then
  exit 0
fi
if try_py /usr/local/bin/python3; then
  exit 0
fi

printf '%s\n' "python_bin: no interpreter can import numpy and PIL (tried GENSEO_PYTHON, PATH python3, /usr/bin/python3, /usr/local/bin/python3)" >&2
exit 1
