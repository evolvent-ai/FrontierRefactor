FROM debian:bookworm-slim@sha256:88200866dfff7ea7f5cbcb6ec7c8a701889efe6fe859fe64d6990e4b07ea4171

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
    g++ \
    libc6-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

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
