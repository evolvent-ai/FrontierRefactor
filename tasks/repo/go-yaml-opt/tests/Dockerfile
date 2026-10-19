FROM golang:1.26-bookworm@sha256:9fdc884aacc3bec89b20ffc69f4bb369c78210e3e4f600387b5128b12c199f81

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
