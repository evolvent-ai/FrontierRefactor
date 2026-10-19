FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Docker CE (daemon + CLI) on Ubuntu — avoids Alpine package conflicts
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg lsb-release \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
       | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
       https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
       > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin \
    && docker compose version \
    && rm -rf /var/lib/apt/lists/*

# Python 3.12, because harbor requires >=3.12 while Ubuntu 22.04 ships 3.10. In a 3.10 sandbox
# `pip install harbor` fails with `from versions: none`, which reads as "PyPI has no such
# package" rather than "this interpreter is too old".
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       python3.12 python3.12-venv python3-pip git \
    && rm -rf /var/lib/apt/lists/*

# Entrypoint: start dockerd and wait until it answers, rather than sleeping a fixed time --
# dockerd takes longer to come up in a cold sandbox than in a warm one.
RUN printf '%s\n' \
    '#!/bin/bash' \
    'dockerd >/var/log/dockerd.log 2>&1 &' \
    'for _ in $(seq 1 60); do' \
    '    docker info >/dev/null 2>&1 && break' \
    '    sleep 1' \
    'done' \
    'exec "$@"' \
    > /usr/local/bin/entrypoint.sh \
    && chmod +x /usr/local/bin/entrypoint.sh \
    && head -1 /usr/local/bin/entrypoint.sh | grep -q '^#!/bin/bash$'

# E2B executes as uid 1000, not as root, and dockerd's socket is root-owned. Putting the user in
# the docker group (and starting dockerd with --group docker) gives it access to the socket
# without sudo; the daemon still runs as root.
RUN groupadd -f docker \
    && (id -u user >/dev/null 2>&1 || useradd -m -u 1000 -G docker user) \
    && usermod -aG docker user \
    && sed -i 's|^dockerd |dockerd --group docker |' /usr/local/bin/entrypoint.sh

# Mask /proc/config.gz in the sandbox's own mount namespace.
#
# Harbor's docker backend accepts a `no-network` task only if a probe finds nftables support in
# the kernel config (CONFIG_NFT_FIB_INET), which the Firecracker kernel does not build. The probe
# runs inside a container, which mounts its own /proc, so this mask does not change its result:
# the frf_e2b_dind backend (scripts/frf_e2b_dind.py) is what makes Harbor accept the tasks. The
# line is kept so the template matches the one the paper results were produced on.
RUN sed -i 's|^dockerd |mount --bind /dev/null /proc/config.gz 2>/dev/null \|\| true\ndockerd |' \
    /usr/local/bin/entrypoint.sh \
    && grep -q 'config.gz' /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

WORKDIR /workspace
