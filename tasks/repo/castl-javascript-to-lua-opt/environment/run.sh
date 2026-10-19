#!/bin/sh
# The reference was observed with these unset; a subject started differently is measured differently.
unset ENV BASH_ENV
ulimit -u 512 2>/dev/null || true
FRF_RUN_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec node "$FRF_RUN_DIR/bin/castl.js" "$@"
