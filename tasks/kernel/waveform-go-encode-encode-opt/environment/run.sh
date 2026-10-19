#!/usr/bin/env bash
# Serve the subject over the wire the verifier speaks. Replace the implementation,
# not this file: the verifier starts it exactly as written.
set -euo pipefail
cd "$(dirname "$0")"
env GOSUMDB=off GOFLAGS=-mod=mod GOTOOLCHAIN=auto go build -o ./serve.bin ./serve.go ./bridge.go ./subject.go >/dev/null
exec ./serve.bin
