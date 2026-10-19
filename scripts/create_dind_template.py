#!/usr/bin/env python3
"""Build the E2B Docker-in-Docker template that run_benchmark_e2b.py runs tasks in.

Why DinD rather than running tasks directly in an E2B sandbox: the verifier isolates each
submission in its own container root, which needs root, mount and chroot. An E2B sandbox runs
as uid 1000 without them; inside DinD the verifier runs in a real container that has them.

    python3 scripts/create_dind_template.py [--alias frf-dind] [--cpus 8] [--memory 8192]

Requires E2B_API_KEY (environment or `.env` in the repository root). Put the printed template
ID into E2B_DIND_TEMPLATE.

The defaults (8 CPUs, 8192 MB) are the template the paper results were produced on; every task
declares 8 CPUs in its task.toml.
"""
import argparse
import asyncio
import os

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPTS)
DOCKERFILE = os.path.join(SCRIPTS, "e2b-dind", "Dockerfile")


def read_env(path: str) -> dict:
    found = {}
    if os.path.isfile(path):
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                found[key.strip()] = value.strip()
    return found


async def build(alias: str, cpus: int, memory: int, key: str) -> None:
    from e2b import AsyncTemplate, Template

    template = Template(file_context_path=os.path.dirname(DOCKERFILE)).from_dockerfile(
        dockerfile_content_or_path=DOCKERFILE,
    )
    seen = []

    def on_log(entry):
        text = str(getattr(entry, "message", entry)).rstrip()
        if text:
            seen.append(text)
            if len(seen) % 20 == 0 or "error" in text.lower():
                print("    " + text[:120], flush=True)

    print("  building %s (%d CPUs / %d MB) ..." % (alias, cpus, memory), flush=True)
    result = await AsyncTemplate.build(
        template=template,
        alias=alias,
        cpu_count=cpus,
        memory_mb=memory,
        on_build_logs=on_log,
        api_key=key,
    )
    print("  done:", result)
    template_id = getattr(result, "template_id", None) or getattr(result, "templateID", None)
    if template_id:
        print("\n  set this before running the benchmark:")
        print("    E2B_DIND_TEMPLATE=%s" % template_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--alias", default="frf-dind")
    parser.add_argument("--cpus", type=int, default=8)
    parser.add_argument("--memory", type=int, default=8192, help="MB")
    args = parser.parse_args()

    env = read_env(os.path.join(ROOT, ".env"))
    key = os.environ.get("E2B_API_KEY") or env.get("E2B_API_KEY")
    if env.get("E2B_API_URL") and not os.environ.get("E2B_API_URL"):
        os.environ["E2B_API_URL"] = env["E2B_API_URL"]
    if not key:
        print("E2B_API_KEY is required (environment or .env)")
        return 2
    if not os.path.isfile(DOCKERFILE):
        print("missing", DOCKERFILE)
        return 2

    asyncio.run(build(args.alias, args.cpus, args.memory, key))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
