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
# nobody's default shell is /usr/sbin/nologin, which makes tmux sessions exit immediately;
# agents that need an interactive shell depend on a real one.
USER root
RUN usermod -s /bin/bash nobody
USER nobody

USER root
COPY . /app
COPY .upstream-Dockerfile /app/Dockerfile
RUN go build -o './yamlfmt' ./cmd/yamlfmt
RUN chown -R nobody:nogroup /app /logs/verifier /home/candidate
USER nobody
