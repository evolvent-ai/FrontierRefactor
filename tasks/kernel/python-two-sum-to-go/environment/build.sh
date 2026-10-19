#!/bin/sh
set -eu
cd /app
mkdir -p build
cd /app/implementation && GOTOOLCHAIN=local GOPROXY=off go build -o /app/build/submission .
