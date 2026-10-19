FROM node:22-bookworm-slim@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5 AS source-runtime

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

# Python is required for verify.py
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install typescript toolchain
RUN npm install -g --force typescript@5.6.3 pnpm@9.12.3 yarn@1.22.22 bun@1.1.38

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
RUN sh -c 'tsc --target ES2022 --module commonjs --skipLibCheck --allowJs $(find . -name '"'"'*.ts'"'"' -not -path '"'"'./node_modules/*'"'"' -not -name '"'"'*.d.ts'"'"' 2>/dev/null) ./subject.cts || tsc --target ES2022 --module commonjs --skipLibCheck ./subject.cts'
RUN python3 -c 'from pathlib import Path; p=Path("/app/run.sh"); p.write_text('"'"'#!/bin/sh\nunset ENV BASH_ENV\nexec node --experimental-specifier-resolution=node /app/serve.cjs subject.cjs entry "$@"\n'"'"'); p.chmod(0o755)'
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

# Node is a build dependency of real projects in every language
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm \
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
