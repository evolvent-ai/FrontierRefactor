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

# Install javascript toolchain
RUN npm install -g --force typescript@5.6.3 pnpm@9.12.3 yarn@1.22.22 bun@1.1.38

RUN mkdir -p /app /logs/verifier

WORKDIR /app

RUN mkdir -p /home/candidate \
    && chown -R nobody:nogroup /app /home/candidate
ENV HOME=/home/candidate
# nobody's default shell is /usr/sbin/nologin, which makes tmux sessions exit immediately;
# agents that need an interactive shell depend on a real one.
USER root
RUN usermod -s /bin/bash nobody
USER nobody

USER root
COPY . /app
# This project pins 2017-era dependencies (acorn 3.0.2, babel-core 6.23.1, …)
# whose peer-dependency metadata npm 10+ rejects by default, failing with
# exit code 254.  --legacy-peer-deps restores the npm 6 resolution rules the
# lockfile was written under.
RUN npm install --legacy-peer-deps
RUN chown -R nobody:nogroup /app /logs/verifier /home/candidate
USER nobody
