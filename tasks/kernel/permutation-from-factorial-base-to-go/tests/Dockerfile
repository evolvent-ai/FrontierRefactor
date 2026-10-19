FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0 AS source-runtime

# Runtime dependencies (inlined from .runtime.Dockerfile)

RUN apt-get update && apt-get install -y --no-install-recommends \
    time \
    build-essential \
    curl \
    git \
    ca-certificates \
    pkg-config \
    libssl-dev \
    zlib1g-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libclang-dev \
    llvm-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app /logs/verifier

WORKDIR /app

RUN mkdir -p /home/candidate \
    && chown -R nobody:nogroup /app /home/candidate
ENV HOME=/home/candidate
USER nobody


# Application setup
USER root
COPY reference/ /app/
WORKDIR /app
RUN python3 -c 'from pathlib import Path; p=Path("/app/run.sh"); p.write_text('"'"'#!/bin/sh\nunset ENV BASH_ENV\nexec python3 /app/serve.py subject from_factorial_base "$@"\n'"'"'); p.chmod(0o755)'
RUN python3 -c 'import json,os; json.dump({k:os.environ[k] for k in ['"'"'PATH'"'"', '"'"'GOROOT'"'"', '"'"'GOPATH'"'"', '"'"'GOTOOLCHAIN'"'"', '"'"'CARGO_HOME'"'"', '"'"'RUSTUP_HOME'"'"', '"'"'JAVA_HOME'"'"', '"'"'LD_LIBRARY_PATH'"'"', '"'"'PYTHONPATH'"'"'] if k in os.environ},open("/runtime-environment.json","w"))'
# The solver's environment/Dockerfile, inlined so the verifier image gets the same toolchain.
FROM golang:1.26-bookworm@sha256:9fdc884aacc3bec89b20ffc69f4bb369c78210e3e4f600387b5128b12c199f81

# Runtime dependencies (inlined from .runtime.Dockerfile)

RUN apt-get update && apt-get install -y --no-install-recommends \
    time \
    build-essential \
    curl \
    git \
    ca-certificates \
    pkg-config \
    libssl-dev \
    zlib1g-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libclang-dev \
    llvm-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/*

ENV PATH=/usr/local/go/bin:${PATH}
ENV GOPATH=/go
ENV GOROOT=/usr/local/go
ENV GOTOOLCHAIN=auto

# Python is required for verify.py
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app /logs/verifier

WORKDIR /app

RUN mkdir -p /home/candidate \
    && chown -R nobody:nogroup /app /home/candidate
ENV HOME=/home/candidate
USER nobody


# Application setup
USER root
# Build context is this directory (`environment/`), the solver's workspace only. `tests/`
# is a sibling of this context and can never be copied by the line below.
# No `COPY . /app` here: in this image the build context is tests/, which holds the answers.
# Harbor mounts /app/implementation, so the directory must exist.
RUN mkdir -p /app/implementation
RUN chown -R nobody:nogroup /app
USER nobody
WORKDIR /app

# Build context is this directory (`environment/`), which contains the
# solver's workspace only. `tests/` is a sibling of this context, never
# inside it, so no verifier, reference or expectation file can be copied
# by the line below. `.dockerignore` beside this file refuses them again.
USER root
# No `COPY . /app` here: in this image the build context is tests/, which holds the answers.
# Harbor mounts /app/implementation, so the directory must exist.
RUN mkdir -p /app/implementation
RUN chown -R nobody:nogroup /app
USER nobody
USER root
COPY --from=source-runtime --chown=0:0 / /reference-runtime/
COPY . /tests/
WORKDIR /app
