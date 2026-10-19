#!/usr/bin/env bash
# Serve the subject over the wire the verifier speaks. Replace the implementation,
# not this file: the verifier starts it exactly as written.
set -euo pipefail
cd "$(dirname "$0")"
tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts >/dev/null
exec node --experimental-specifier-resolution=node ./serve.cjs subject.js getLines
