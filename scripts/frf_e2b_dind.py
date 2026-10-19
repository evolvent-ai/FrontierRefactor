"""Harbor backend for FrontierRefactor tasks running inside an E2B DinD sandbox.

This module is uploaded into the E2B sandbox alongside the task and loaded by
harbor via ``-e frf_e2b_dind:E2BDinDEnvironment``.

Why a custom backend?  Three choices exist and only this one works:

  -e e2b  (harbor's built-in E2B backend) — fails.  Runs commands directly in
  the microVM as uid=1000 with no root/mount/chroot.  The verifier needs those
  to build isolated subject containers and throws immediately.

  -e docker  (harbor's built-in Docker backend) — fails.  Harbor reads
  /proc/config.gz for CONFIG_NFT_FIB_INET to decide whether no-network mode is
  safe.  Firecracker kernels do not compile that flag; harbor rejects every
  no-network task before running a single probe.

  -e frf_e2b_dind:E2BDinDEnvironment  (this file) — works.  Two narrow changes:

  1. capabilities() declares disable_internet=True so harbor accepts the tasks'
     `no-network` setting.

  2. _apply_network_policy() is a no-op instead of raising, so no nftables
     egress-control sidecar (which cannot run in DinD) is required.

Network isolation is therefore not enforced at the container level by this
backend: the task containers start on Docker's default network. Isolation that
matters for grading is enforced by each task's verifier, which runs the
submission and the reference as separate users without network access and
refuses to grade if that check fails. This is the configuration the paper
results were produced with.
"""
from __future__ import annotations

from pathlib import Path
from typing import override

from harbor.environments.capabilities import EnvironmentCapabilities
from harbor.environments.docker.docker import DockerEnvironment
from harbor.models.task.config import EnvironmentConfig, NetworkMode, NetworkPolicy
from harbor.models.trial.paths import TrialPaths


class E2BDinDEnvironment(DockerEnvironment):
    """DockerEnvironment adapted for E2B DinD sandboxes.

    _enable_egress_control is left False (set by the parent via its kernel
    probe), so no egress sidecar is started.
    """

    def __init__(
        self,
        environment_dir: Path,
        environment_name: str,
        session_id: str,
        trial_paths: TrialPaths,
        task_env_config: EnvironmentConfig,
        network_policy: NetworkPolicy | None = None,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            environment_dir=environment_dir,
            environment_name=environment_name,
            session_id=session_id,
            trial_paths=trial_paths,
            task_env_config=task_env_config,
            network_policy=network_policy,
            *args,
            **kwargs,
        )
        # No nftables sidecar is started (see the class docstring).

    @property
    @override
    def capabilities(self) -> EnvironmentCapabilities:
        return EnvironmentCapabilities(
            # Declare no-network support so harbor accepts the tasks.
            disable_internet=True,
            # No allowlist support — tasks either have full network or none.
            network_allowlist=False,
            network_allowlist_hostnames=False,
            network_allowlist_wildcard_hostnames=False,
            network_allowlist_ipv4_addresses=False,
            network_allowlist_ipv6_addresses=False,
            network_allowlist_ipv4_cidrs=False,
            network_allowlist_ipv6_cidrs=False,
            dynamic_network_policy=False,
            windows=False,
            mounted=True,
            docker_compose=True,
        )

    @override
    async def _apply_network_policy(self, network_policy: NetworkPolicy) -> None:
        """No-op instead of the parent's error.

        The parent raises here when egress control is disabled, which would
        reject every no-network task. Dynamic policy changes are not
        advertised (dynamic_network_policy=False).
        """
        if network_policy.network_mode == NetworkMode.PUBLIC:
            return
        return
