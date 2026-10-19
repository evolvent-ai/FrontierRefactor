FROM eclipse-temurin:21-jdk-jammy@sha256:ce5767b7222312d42395f5bab033cd91f09e44032a2f21bdfd7b5b912dbe1e77

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
    maven \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=${JAVA_HOME}/bin:${PATH}

# Python is required for verify.py
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Node is a build dependency of real projects in every language
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# Install java toolchain
RUN python3 -m pip install --no-cache-dir tomli

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
