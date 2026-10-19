#!/usr/bin/env bash
# Serve the subject over the wire the verifier speaks. Replace the implementation,
# not this file: the verifier starts it exactly as written.
set -euo pipefail
cd "$(dirname "$0")"
c++ -std=c++17 -O2 -x c -c ./serve.c -o ./serve.o >/dev/null
c++ -std=c++17 -O2 -o ./serve.bin ./serve.o ./subject.cpp >/dev/null
exec ./serve.bin
