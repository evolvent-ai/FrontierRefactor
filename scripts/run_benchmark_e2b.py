#!/usr/bin/env python3
"""Run FrontierRefactor tasks concurrently on E2B: one sandbox per (model, task, repetition).

Each sandbox is a Docker-in-Docker E2B template (see scripts/e2b-dind/). Inside it the runner
installs Harbor and runs the task with the `frf_e2b_dind:E2BDinDEnvironment` backend. The local
machine only schedules jobs and collects results.

Why DinD rather than Harbor's built-in backends:

  `-e e2b` executes commands directly in the microVM without containers. The verifier needs
  root/mount/chroot to isolate the submission, which an E2B sandbox does not provide.

  `-e docker` inside the sandbox rejects every `no-network` task, because Harbor's egress probe
  looks for an nftables kernel feature that the Firecracker kernel does not build.

  `-e frf_e2b_dind:E2BDinDEnvironment` works: it declares no-network support so Harbor accepts
  the tasks, without requiring the nftables egress sidecar. Network isolation during grading is
  enforced by each task's verifier, which runs the submission without network access.

Usage:

    python3 scripts/run_benchmark_e2b.py tasks/ --agent claude-code --model claude-opus-5 \\
        --ak reasoning_effort=high --repeat 3 --concurrency 16

Credentials are read from the process environment and, if present, from a `.env` file in the
repository root. E2B_API_KEY and E2B_DIND_TEMPLATE are required; agent credentials
(ANTHROPIC_API_KEY, OPENAI_API_KEY, ...) are forwarded into the sandbox.
"""
import argparse
import json
import os
import shlex
import shutil
import sys
import tarfile
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

HARBOR_SPEC = "harbor==0.22.0"
BACKEND = "frf_e2b_dind:E2BDinDEnvironment"
SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPTS)

# Agent credentials forwarded from the process environment into each sandbox.
FORWARDED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL",
                 "OPENAI_API_KEY", "OPENAI_BASE_URL")

_print_lock = threading.Lock()


def say(message: str) -> None:
    with _print_lock:
        print(message, flush=True)


def read_env(path: str) -> dict:
    found = {}
    if os.path.isfile(path):
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                found[key.strip()] = value.strip()
    return found


def run(sandbox, command: str, seconds: int):
    """Run a shell command in the sandbox and always return its output.

    E2B raises on a non-zero exit code, and the exception often carries an empty stdout.
    Appending `|| true` keeps the exit code zero so the diagnostic output is never lost;
    success is decided by markers in the output instead.
    """
    return sandbox.commands.run("{ %s ; } 2>&1 || true" % command,
                                timeout=seconds, request_timeout=seconds)


def find_tasks(release: str) -> list:
    """-> [(scale, name, path)]. Accepts either `tasks/` or `tasks/<scale>/`.

    A task is a directory containing task.toml.
    """
    found = []
    for entry in sorted(os.listdir(release)):
        path = os.path.join(release, entry)
        if not os.path.isdir(path):
            continue
        if os.path.isfile(os.path.join(path, "task.toml")):
            # `release` is itself a scale directory
            found.append((os.path.basename(release.rstrip("/")), entry, path))
            continue
        for sub in sorted(os.listdir(path)):
            here = os.path.join(path, sub)
            if os.path.isfile(os.path.join(here, "task.toml")):
                found.append((entry, sub, here))
    return found


def slug(text: str) -> str:
    """Model id -> safe directory name: `gpt-5.6-sol` -> `gpt-5_6-sol`."""
    return "".join(c if (c.isalnum() or c in "-_") else "_" for c in (text or "none"))


def harvest(job: dict, settings: dict) -> dict:
    """Copy the whole Harbor jobs tree back to the local machine. -> summary dict.

    A harvest failure does not change the task outcome (that is Harbor's verdict); it is only
    recorded. The output path includes model, task and repetition so that runs never overwrite
    each other, and the cell is cleared first so that re-running it is idempotent.

    Layout: <harvest_dir>/<model>/<scale>/<task>/rep<n>/jobs/check/<trial>/
    """
    sandbox = job["sandbox"]
    out = os.path.join(settings["harvest_dir"], slug(job["model"]), job["scale"],
                       job["task"], "rep%d" % job["rep"])
    if os.path.isdir(out):
        shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out, exist_ok=True)
    report = {"ok": False, "bytes": 0, "path": out}

    # Excluded: what can be rebuilt from the task itself (.git, node_modules, cargo target/,
    # vendored gems). Edited source files are always kept.
    packed = run(sandbox,
                 "cd /home/user && tar czf /home/user/harvest.tar.gz "
                 "--exclude='*/node_modules' --exclude='*/.git' "
                 "--exclude='*/target/debug' --exclude='*/target/release' "
                 "--exclude='*/vendor/bundle' "
                 "jobs 2>/dev/null; "
                 "wc -c < /home/user/harvest.tar.gz 2>/dev/null || echo 0", 900)
    try:
        size = int((packed.stdout or "0").split()[-1])
    except (ValueError, IndexError):
        size = 0
    if size <= 0:
        report["detail"] = "nothing to pack: " + " ".join((packed.stdout or "").split())[-160:]
        return report

    # Large archives are read back in chunks: a single transfer of hundreds of MB times out.
    CHUNK = 32 * 1024 * 1024
    blob = b""
    try:
        if size <= CHUNK:
            blob = sandbox.files.read("/home/user/harvest.tar.gz", format="bytes")
        else:
            run(sandbox, "cd /home/user && split -b %d harvest.tar.gz part- && ls part-*"
                % CHUNK, 600)
            listing = run(sandbox, "cd /home/user && ls part-* 2>/dev/null", 180)
            for part in sorted((listing.stdout or "").split()):
                for attempt in range(3):
                    try:
                        blob += sandbox.files.read("/home/user/" + part, format="bytes")
                        break
                    except Exception:                     # noqa: BLE001 -- transport only
                        if attempt == 2:
                            raise
                        time.sleep(5 * (attempt + 1))
    except Exception as exc:                              # noqa: BLE001
        report["detail"] = "read failed: " + str(exc)[:200]
        return report

    archive = os.path.join(out, "jobs.tar.gz")
    with open(archive, "wb") as handle:
        handle.write(blob)
    try:
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(out)
        os.unlink(archive)
    except Exception as exc:                              # noqa: BLE001
        report["detail"] = "unpack failed (archive kept): " + str(exc)[:200]
        report["bytes"] = len(blob)
        return report

    report.update(ok=True, bytes=len(blob))
    report["acts"] = count_acts(out)
    return report


def harvest_hit_api_error(rep_dir) -> bool:
    """Did the agent terminate on a model-API error?

    Matches a non-zero `"api_error_status"` value. Matching the field name alone would be
    wrong: the key is always present and is null on a normal exit.
    """
    if not rep_dir:
        return False
    import glob as _glob
    import re as _re
    pat = _re.compile(r'"api_error_status"\s*:\s*[1-9]')
    for name in ("claude-code.txt", "codex.txt"):
        for path in _glob.glob(os.path.join(rep_dir, "jobs", "check", "*", "agent", name)):
            try:
                with open(path, encoding="utf-8", errors="replace") as handle:
                    if pat.search(handle.read()):
                        return True
            except OSError:
                continue
    return False


def count_acts(rep_dir: str):
    """Number of agent actions in the harvested trajectory. -> int, or None if unreadable.

    Counted at run time because an agent that cannot reach its model exits with zero actions,
    and for in-place tasks the untouched starting code already passes the verifier -- such a
    run would otherwise look like a success.
    """
    import glob as _glob
    traj = _glob.glob(os.path.join(rep_dir, "jobs", "check", "*", "agent",
                                   "trajectory.json"))
    if not traj:
        return None
    try:
        with open(traj[0], encoding="utf-8") as handle:
            steps = json.load(handle).get("steps") or []
        return sum(1 for s in steps if s.get("source") == "agent")
    except Exception:                                    # noqa: BLE001
        return None


class ModelGate:
    """Per-model cap on concurrently running jobs, plus a circuit breaker.

    Model API rate limits are usually per model, so the total concurrency is spread across
    models instead of letting one model take every slot. After `dead_after` consecutive invalid
    runs of a model (zero actions or API error), no further sandboxes are created for it and
    its remaining jobs are reported as skipped.
    """

    def __init__(self, per_model: int, dead_after: int = 0) -> None:
        self._limit = max(1, per_model)
        self._lock = threading.Condition()
        self._busy: dict[str, int] = {}
        self._dead_after = dead_after
        self._streak: dict[str, int] = {}
        self.dead: dict[str, int] = {}

    def acquire(self, model: str) -> None:
        with self._lock:
            while self._busy.get(model, 0) >= self._limit:
                self._lock.wait()
            self._busy[model] = self._busy.get(model, 0) + 1

    def release(self, model: str) -> None:
        with self._lock:
            self._busy[model] = max(0, self._busy.get(model, 0) - 1)
            self._lock.notify_all()

    def record(self, model: str, ok: bool) -> None:
        if not self._dead_after:
            return
        with self._lock:
            if ok:
                self._streak[model] = 0
                return
            self._streak[model] = self._streak.get(model, 0) + 1
            if (self._streak[model] >= self._dead_after
                    and model not in self.dead):
                self.dead[model] = self._streak[model]

    def is_dead(self, model: str) -> bool:
        with self._lock:
            return model in self.dead


def interleave(jobs: list) -> list:
    """Round-robin jobs over (model, scale) so any prefix of the queue covers all of them.

    Within a bucket, repetition comes first: all tasks run once before any runs a second time.
    """
    from collections import defaultdict
    buckets = defaultdict(list)
    for job in jobs:
        buckets[(job["model"], job.get("scale", ""))].append(job)
    for key in buckets:
        buckets[key].sort(key=lambda j: (j.get("rep", 1), j.get("task", "")))
    order, out = sorted(buckets), []
    while any(buckets[k] for k in order):
        for key in order:
            if buckets[key]:
                out.append(buckets[key].pop(0))
    return out


class TaskPacker:
    """Pack each task once and share the tarball across all models and repetitions.

    Packing is the only heavy local work (package/repo trees are hundreds of MB), so its
    concurrency is limited separately from the sandbox concurrency.
    """

    def __init__(self, scratch_dir: str, limit: int) -> None:
        self._dir = scratch_dir
        self._sem = threading.Semaphore(max(1, limit))
        self._lock = threading.Lock()
        self._cache: dict = {}
        self._locks: dict = {}
        self.packed = 0
        self.reused = 0

    def _task_lock(self, key: str):
        with self._lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]

    def get(self, task_dir: str, arcname: str) -> str:
        """-> path of the local tarball."""
        with self._task_lock(task_dir):
            hit = self._cache.get(task_dir)
            if hit and os.path.isfile(hit):
                with self._lock:
                    self.reused += 1
                return hit
            with self._sem:
                fd, archive = tempfile.mkstemp(suffix=".tar.gz", dir=self._dir)
                os.close(fd)
                with tarfile.open(archive, "w:gz") as tar:
                    tar.add(task_dir, arcname=arcname)
            self._cache[task_dir] = archive
            with self._lock:
                self.packed += 1
            return archive

    def cleanup(self) -> None:
        with self._lock:
            for path in self._cache.values():
                try:
                    os.unlink(path)
                except OSError:
                    pass
            self._cache.clear()


def one_task(job: dict, settings: dict) -> dict:
    from e2b import Sandbox

    scale, name, task_dir = job["scale"], job["task"], job["path"]
    model, rep = job["model"], job["rep"]
    record = {"task": name, "scale": scale, "model": model, "rep": rep,
              "ok": False, "stage": "gate", "seconds": 0}
    began = time.time()
    sandbox = None
    gate = settings["gate"]
    if gate.is_dead(model):
        record["stage"] = "skipped-dead-model"
        record["detail"] = "model circuit breaker open (consecutive invalid runs); not executed"
        record["skipped"] = True
        return record
    # Wait for the model slot before creating the sandbox: sandbox lifetime starts at creation.
    gate.acquire(model)
    record["queued"] = int(time.time() - began)
    try:
        record["stage"] = "create"
        # Creation is retried with growing, de-synchronised backoff: under a burst of
        # concurrent creations the E2B API occasionally returns transient 502s.
        ATTEMPTS = 6
        for attempt in range(ATTEMPTS):
            try:
                sandbox = Sandbox.create(
                    template=settings["template"], api_key=settings["key"],
                    timeout=settings["lifetime"],
                    envs={
                        "DEBIAN_FRONTEND": "noninteractive",
                        **{k: v for k, v in settings["agent_env"].items() if v},
                    })
                break
            except Exception as exc:                  # noqa: BLE001 -- transport only
                if attempt == ATTEMPTS - 1:
                    record["detail"] = ("create failed x%d: " % ATTEMPTS) + str(exc)[:200]
                    raise
                record["create_retries"] = attempt + 1
                time.sleep(15 * (attempt + 1)
                           + (threading.get_ident() % 11))
        record["stage"] = "docker"
        ready = run(sandbox,
                    "for i in $(seq 1 90); do docker info >/dev/null 2>&1 && break; sleep 2; done; "
                    "docker info >/dev/null 2>&1 && echo up || echo down", 300)
        if "up" not in (ready.stdout or ""):
            record["detail"] = "docker daemon never came up"
            return record

        record["stage"] = "upload"
        # Package/repo tasks are hundreds of MB, which times out a single files.write. The
        # tarball is streamed from disk in chunks and reassembled inside the sandbox.
        archive = settings["packer"].get(task_dir, name)
        size = os.path.getsize(archive)
        CHUNK = 16 * 1024 * 1024
        nparts = max(1, -(-size // CHUNK))
        with open(archive, "rb") as source:
            for index in range(nparts):
                blob = source.read(CHUNK)
                suffix = "" if nparts == 1 else "%03d" % index
                for attempt in range(4):
                    try:
                        sandbox.files.write("/home/user/task.tar.gz" + suffix, blob)
                        break
                    except Exception as exc:      # noqa: BLE001 -- transport only
                        if attempt == 3:
                            record["detail"] = ("upload failed after 4 tries (part %r, %d MB): %s"
                                                % (suffix, len(blob) // 1048576, str(exc)[:160]))
                            return record
                        time.sleep(5 * (attempt + 1))
                blob = None

        if nparts > 1:
            done = run(sandbox, "cd /home/user && cat task.tar.gz[0-9]* > task.tar.gz "
                                "&& rm -f task.tar.gz[0-9]* && echo JOINED", 600)
            if "JOINED" not in (done.stdout or ""):
                record["detail"] = "chunk reassembly failed: " + (done.stdout or "")[-200:]
                return record

        # Free the sandbox disk before the task images are built: repo-scale tasks that copy a
        # full toolchain into the verifier image can otherwise run out of space mid-build.
        run(sandbox, "docker system prune -af --volumes >/dev/null 2>&1; "
                     "docker builder prune -af >/dev/null 2>&1; true", 300)
        # The custom backend is the module that `harbor run -e` imports, so it ships with the task.
        with open(os.path.join(SCRIPTS, "frf_e2b_dind.py"), "rb") as handle:
            sandbox.files.write("/home/user/frf_e2b_dind.py", handle.read())
        done = run(sandbox, "cd /home/user && tar xzf task.tar.gz && rm task.tar.gz && echo UNPACKED", 900)
        if "UNPACKED" not in (done.stdout or ""):
            record["detail"] = (done.stdout or "")[-400:]
            return record

        record["stage"] = "install"
        # Written as a script file (not one long command) so that `exit` ends only the script.
        # Downloads of uv and of Harbor from PyPI are retried against transient network errors.
        script = (
            "#!/bin/bash\n"
            "set -u\n"
            "UV=$HOME/.local/bin/uv\n"
            "for i in 1 2 3 4; do\n"
            "  [ -x \"$UV\" ] && break\n"
            "  if command -v uv >/dev/null 2>&1; then UV=$(command -v uv); break; fi\n"
            "  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1\n"
            "  [ -x \"$UV\" ] || sleep $((i * 15))\n"
            "done\n"
            "if [ ! -x \"$UV\" ]; then echo NO_UV; exit 0; fi\n"
            "\"$UV\" venv --python 3.12 /home/user/hb 2>&1 | tail -1\n"
            "export UV_HTTP_TIMEOUT=120\n"
            "for i in 1 2 3 4; do\n"
            "  \"$UV\" pip install --python /home/user/hb/bin/python --quiet '%s' 2>&1 | tail -3\n"
            "  [ -x /home/user/hb/bin/harbor ] && break\n"
            "  sleep $((i * 15))\n"
            "done\n"
            "[ -x /home/user/hb/bin/harbor ] && echo HARBOR_READY\n"
        ) % HARBOR_SPEC
        sandbox.files.write("/home/user/install.sh", script.encode())
        done = run(sandbox, "bash /home/user/install.sh", 1800)
        if "HARBOR_READY" not in (done.stdout or ""):
            record["detail"] = "harbor not installed: " + " ".join((done.stdout or "").split())[-320:]
            return record

        record["stage"] = "harbor-run"
        extra = settings["agent_args"]
        if model:
            extra += " --model %s" % model
        done = run(sandbox,
                   "cd /home/user && PYTHONPATH=/home/user /home/user/hb/bin/harbor run "
                   "-p %s -e %s %s -o /home/user/jobs --job-name check -q 2>&1 | tail -30"
                   % (name, BACKEND, extra), settings["run_timeout"])
        flat = " ".join((done.stdout or "").split())
        # Any of these means the build did not take the expected path.
        for mark in ("benchmark-runtime", "SOLVER_IMAGE", "pull access denied",
                     "is not supported by", "subject roots must be managed"):
            if mark in flat:
                record["detail"] = "%r: %s" % (mark, flat[-300:])
                return record

        got = run(sandbox, "cat /home/user/jobs/check/result.json 2>/dev/null", 180)
        try:
            payload = json.loads(got.stdout or "{}")
        except ValueError:
            payload = {}
        stats = payload.get("stats") or {}
        record["stats"] = {k: stats.get(k) for k in
                           ("n_completed_trials", "n_errored_trials")}
        record["evals"] = stats.get("evals") or {}
        record["detail"] = flat[-300:]
        record["ok"] = (stats.get("n_errored_trials") == 0
                        and (stats.get("n_completed_trials") or 0) >= 1)
        if not record["ok"]:
            # Harbor's stdout only shows an exception-type table; the message is in the trial dir.
            trace = run(sandbox,
                        "tail -6 /home/user/jobs/check/*/exception.txt 2>/dev/null | tail -4",
                        180)
            record["trace"] = " ".join((trace.stdout or "").split())[-500:]

        record["stage"] = "harvest"
        # Everything the run produced (agent trajectory, submitted /app, verifier output with
        # timing evidence) exists only inside the sandbox, so it is copied back before the
        # sandbox is killed in `finally`.
        job["sandbox"] = sandbox
        record["harvest"] = harvest(job, settings)
        # A zero-action run is not a valid attempt even if the verifier rewarded it.
        record["acts"] = record["harvest"].get("acts")
        if record["acts"] == 0:
            record["ok"] = False
            record["stage"] = "zero-action"
            record["detail"] = ("agent took zero actions (model likely unreachable); "
                                "the verifier still scored it, but this is not a valid run")
        # Likewise a run cut short by a model-API error.
        elif harvest_hit_api_error(record["harvest"].get("path")):
            record["ok"] = False
            record["stage"] = "api-error"
            record["detail"] = "agent terminated on a model-API error; not a valid run"
        gate.record(model, record["ok"])
        return record
    except Exception as exc:                          # noqa: BLE001 -- one task must not end the batch
        record["detail"] = str(exc)[:300]
        return record
    finally:
        record["seconds"] = int(time.time() - began)
        if sandbox is not None:
            # Retried: a sandbox that is not killed stays alive (and billed) until its lifetime ends.
            for attempt in range(3):
                try:
                    sandbox.kill()
                    break
                except Exception:                     # noqa: BLE001 -- transport only
                    if attempt == 2:
                        record["leaked_sandbox"] = getattr(sandbox, "sandbox_id", "?")
                        say("  [!] could not kill sandbox, it will live until its lifetime ends: %s"
                            % record["leaked_sandbox"])
                    else:
                        time.sleep(3 * (attempt + 1))
        # Released only after the sandbox is gone, so concurrency never exceeds the cap.
        gate.release(model)


def sweep(api_key: str, known_leaks: list) -> None:
    """Kill the sandboxes this run failed to kill. Only those -- never other sandboxes on the key."""
    if not known_leaks:
        return
    try:
        from e2b import Sandbox
    except Exception:                                     # noqa: BLE001
        return
    killed = []
    for sid in known_leaks:
        try:
            Sandbox.connect(sid, api_key=api_key).kill()
            killed.append(sid)
        except Exception:                                 # noqa: BLE001
            pass
    stuck = [s for s in known_leaks if s not in killed]
    say("  final sweep: killed %d/%d leaked sandboxes" % (len(killed), len(known_leaks)))
    if stuck:
        say("  [!] still alive, kill manually: %s" % ", ".join(stuck[:5]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("release", help="tasks/ directory, or one scale directory under it")
    parser.add_argument("--concurrency", type=int, default=8,
                        help="total number of sandboxes alive at once")
    parser.add_argument("--agent", default="nop",
                        help="Harbor agent, e.g. claude-code or codex (default nop: pipeline check only)")
    parser.add_argument("--model", action="append", default=[],
                        help="model id, repeatable; each model runs every selected task")
    parser.add_argument("--per-model", type=int, default=0,
                        help="cap on concurrent jobs per model (default: ceil(concurrency / #models))")
    parser.add_argument("--pack-concurrency", type=int, default=8,
                        help="cap on tasks being packed locally at once")
    parser.add_argument("--repeat", type=int, default=1,
                        help="repetitions per task per model")
    parser.add_argument("--dead-after", type=int, default=8,
                        help="stop creating sandboxes for a model after this many consecutive "
                             "invalid runs (0 = never)")
    parser.add_argument("--ak", "--agent-kwarg", action="append", default=[], dest="agent_kwargs",
                        metavar="key=value", help="extra Harbor agent kwarg, repeatable")
    parser.add_argument("--ae", "--agent-env", action="append", default=[], dest="agent_env",
                        metavar="KEY=VALUE", help="extra environment variable for the agent, repeatable")
    parser.add_argument("--only", action="append", default=[],
                        help="run only these tasks, `name` or `scale/name`, repeatable")
    parser.add_argument("--scale", action="append", default=[],
                        help="run only these scales, repeatable")
    parser.add_argument("--limit", type=int, default=0, help="run only the first N tasks")
    parser.add_argument("--run-timeout", type=int, default=21600,
                        help="seconds allowed for `harbor run` (agent + verifier)")
    parser.add_argument("--lifetime", type=int, default=25200, help="sandbox lifetime in seconds")
    parser.add_argument("--json", default="frf-run.json", help="run report")
    parser.add_argument("--harvest-dir", default="frf-harvest",
                        help="where each run's jobs tree is copied back")
    parser.add_argument("--scratch-dir", default=".scratch",
                        help="local directory for task tarballs")
    args = parser.parse_args()

    env = read_env(os.path.join(ROOT, ".env"))
    key = os.environ.get("E2B_API_KEY") or env.get("E2B_API_KEY")
    template = os.environ.get("E2B_DIND_TEMPLATE") or env.get("E2B_DIND_TEMPLATE")
    if env.get("E2B_API_URL") and not os.environ.get("E2B_API_URL"):
        os.environ["E2B_API_URL"] = env["E2B_API_URL"]
    if not key or not template:
        print("E2B_API_KEY and E2B_DIND_TEMPLATE are required (environment or .env); "
              "see scripts/create_dind_template.py for the template")
        return 2

    tasks = []
    for scale, name, path in find_tasks(args.release):
        if args.only and name not in args.only and ("%s/%s" % (scale, name)) not in args.only:
            continue
        if args.scale and scale not in args.scale:
            continue
        tasks.append((scale, name, path))
    if args.limit:
        tasks = tasks[:args.limit]
    if not tasks:
        print("no tasks selected")
        return 2

    models = args.model or [""]
    jobs = interleave([{"scale": s, "task": n, "path": p, "model": m, "rep": r}
                       for m in models
                       for s, n, p in tasks
                       for r in range(1, args.repeat + 1)])

    agent_args = "-a %s" % args.agent
    for kv in args.agent_kwargs:
        agent_args += " --ak %s" % shlex.quote(kv)
    for kv in args.agent_env:
        agent_args += " --ae %s" % shlex.quote(kv)

    # Agent credentials go into the sandbox: everything in .env except E2B_* and GITHUB_* keys, plus
    # the known agent variables from the process environment. E2B credentials stay local.
    agent_env: dict[str, str] = {
        k: v for k, v in env.items()
        if not k.startswith("E2B_") and not k.startswith("GITHUB_") and v
    }
    for name in FORWARDED_ENV:
        if os.environ.get(name):
            agent_env[name] = os.environ[name]

    scratch_dir = os.path.abspath(args.scratch_dir)
    os.makedirs(scratch_dir, exist_ok=True)
    harvest_dir = os.path.abspath(args.harvest_dir)
    os.makedirs(harvest_dir, exist_ok=True)

    per_model = args.per_model or max(1, -(-args.concurrency // len(models)))
    packer = TaskPacker(scratch_dir, args.pack_concurrency)
    settings = {"key": key, "template": template, "agent_args": agent_args,
                "agent_env": agent_env, "scratch_dir": scratch_dir,
                "harvest_dir": harvest_dir, "packer": packer,
                "gate": ModelGate(per_model, dead_after=args.dead_after),
                "run_timeout": args.run_timeout, "lifetime": args.lifetime}

    say("  %d tasks x %d models x %d reps = %d jobs"
        % (len(tasks), len(models), args.repeat, len(jobs)))
    say("  concurrency %d, per model %d, packing %d, agent=%s"
        % (args.concurrency, per_model, args.pack_concurrency, args.agent))
    say("  models: " + ", ".join(m or "(default)" for m in models))
    say("  harvest dir: " + harvest_dir)
    began = time.time()
    results = []
    announced: set = set()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(one_task, job, settings) for job in jobs]
        for future in as_completed(futures):
            record = future.result()
            results.append(record)
            got = (record.get("harvest") or {}).get("ok")
            acts = record.get("acts")
            say("  [%4d/%4d] %-4s %-14s %-40s %5ds %s%s%s"
                % (len(results), len(jobs), "ok" if record["ok"] else "FAIL",
                   (record.get("model") or "-")[:14],
                   ("%s/%s#%s" % (record.get("scale", "?"), record["task"],
                                  record.get("rep", 1)))[:40],
                   record["seconds"],
                   "" if acts is None else "%d acts " % acts,
                   "" if got or record.get("skipped") else "[not harvested] ",
                   "" if record["ok"] else (record.get("trace") or record.get("detail", ""))[:60]))
            for model in sorted(settings["gate"].dead):
                if model not in announced:
                    announced.add(model)
                    say("  [!!] %s: %d consecutive invalid runs, circuit breaker open -- "
                        "remaining jobs for it are skipped. Check quota / API access."
                        % (model, settings["gate"].dead[model]))
            # Write the report as we go (atomically) so an interrupted batch still has one.
            if len(results) % 10 == 0 or len(results) == len(jobs):
                tmp = args.json + ".partial"
                try:
                    with open(tmp, "w", encoding="utf-8") as handle:
                        json.dump(results, handle, indent=2, ensure_ascii=False)
                    os.replace(tmp, args.json)
                except OSError as exc:            # noqa: BLE001
                    say("  [!] could not write partial report: %s" % str(exc)[:80])

    good = sum(1 for r in results if r["ok"])
    kept = sum(1 for r in results if (r.get("harvest") or {}).get("ok"))
    zero = sum(1 for r in results if r.get("acts") == 0)
    skipped = sum(1 for r in results if r.get("skipped"))
    packer.cleanup()
    sweep(key, [r["leaked_sandbox"] for r in results if r.get("leaked_sandbox")])
    say("\n  %d/%d ok, %d/%d harvested, %d min"
        % (good, len(results), kept, len(results), (time.time() - began) / 60))
    if zero or skipped:
        say("  [!] %d zero-action runs, %d skipped by the circuit breaker -- not valid runs"
            % (zero, skipped))
    if len(models) > 1:
        for model in models:
            mine = [r for r in results if r.get("model") == model]
            if mine:
                say("    %-22s %d/%d ok, median %ds"
                    % (model or "(default)", sum(1 for r in mine if r["ok"]), len(mine),
                       sorted(r["seconds"] for r in mine)[len(mine) // 2]))
    with open(args.json, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)
    say("  report: " + args.json)
    say("  raw results: " + harvest_dir)
    return 0 if good == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
