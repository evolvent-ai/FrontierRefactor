#!/usr/bin/env bash
# Serve the subject over the wire the verifier speaks. Replace the implementation,
# not this file: the verifier starts it exactly as written.
set -euo pipefail
cd "$(dirname "$0")"
javac -d . ./Serve.java ./Subject.java >/dev/null
exec java -cp . Serve
