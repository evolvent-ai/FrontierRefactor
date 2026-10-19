#!/bin/sh
set -eu
cd /app
mkdir -p build
cargo build --offline --release --manifest-path implementation/Cargo.toml --target-dir /app/build --bin submission
