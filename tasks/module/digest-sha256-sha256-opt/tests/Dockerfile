FROM node:22-bookworm-slim@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5

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

# Build context is this directory (`environment/`), which contains the
# solver's workspace only. `tests/` is a sibling of this context, never
# inside it, so no verifier, reference or expectation file can be copied
# by the line below. `.dockerignore` beside this file refuses them again.

# Verifier image: this build context is `tests/`, which holds verify.py, the
# frozen expectations and the reference implementation.  It deliberately does
# NOT build the subject -- the verifier only needs a runtime able to execute
# verify.py.  Dependency installs belong in environment/Dockerfile, whose
# context has the manifests; running them here fails with ENOENT because
# tests/ has no package.json / requirements.txt / Cargo.toml.
USER root
COPY . /tests/
RUN chown -R nobody:nogroup /tests /logs/verifier /home/candidate
USER nobody
WORKDIR /app
