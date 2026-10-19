#!/bin/sh
set -eu
/app/build.sh
exec /app/build/submission "$@"
