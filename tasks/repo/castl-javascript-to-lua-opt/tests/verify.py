#!/usr/bin/env python3
import hashlib, json, os, shutil, subprocess, sys, tempfile, time
from contextlib import ExitStack

"""Measuring a speedup that is not the machine's mood.

Timing two programs and dividing is wrong on a shared machine. A ratio from one pair of stopwatch
readings carries the machine's state as much as the code's: a neighbouring job, a frequency change,
a cold cache on whichever ran first. So a single ratio is not evidence, and this module's job is to
turn many readings into one number that is.

Five things make it evidence, and each answers a specific way the naive measurement lies:

    INTERLEAVED       reference and candidate timed alternately in one run, so a machine that slows
                      down halfway through slows both rather than whichever went second.
    ORDER ALTERNATED  the one that runs first pays for a cold cache, so who goes first alternates.
    INPUT POLICY      supplied by the caller and reported by the delivered evaluator; no claim
                      that repeated held-out inputs prevent memoisation.
    NOISE FLOOR       calibrated HERE, on this machine, in this run, by timing the reference against
                      ITSELF -- a comparison whose true answer is exactly 1.0, so whatever spread
                      appears is this machine's noise and nothing else. Never a constant: a number
                      measured on the authoring host describes a machine nobody is graded on.
    LOWER BOUND       the bootstrapped confidence interval's lower bound is what gets reported, not
                      the median. Being 95% sure of at least 1.4x is a claim; a median of 1.4x with
                      this much spread is not.

And the worst shape counts, not the average: a candidate that tuned one convenient size has not made
the subject faster.

A GAIN INSIDE THE NOISE IS REPORTED AS EXACTLY 1.0. Not as itself with a warning, and not as a
failure -- as 1.0, the neutral value, because that is what the measurement actually established.
Scoring is downstream of this and must not have to re-litigate what counts as noise; by the time a
ratio leaves this module it is a finding.
"""


import math
import statistics
from dataclasses import dataclass, field
from typing import Callable

# How many paired samples per shape. Below about ten the bootstrap has too little to resample and
# its interval is as unstable as the thing it is measuring.
SAMPLES_PER_SHAPE = 12
WARMUP_PAIRS = 2
PROTOCOL_VERSION = "paired-worst-v1"

# Resamples drawn to build the interval. Cheap -- it is arithmetic on numbers already collected --
# so this is set high enough that the bound does not wobble between runs on identical data.
BOOTSTRAP_DRAWS = 2000

# The interval's coverage. 0.95 means the reported bound is the 5th percentile of resampled medians.
CONFIDENCE = 0.95


@dataclass(frozen=True)
class SpeedResult:
    """What a timing pass concluded, with the evidence for it."""

    speedup: float                      # THE number a score uses; exactly 1.0 when within noise
    median: float                       # what a naive measurement would have reported
    noise_floor: float                  # reference vs itself, upper bound; a gain must clear this
    shapes: dict = field(default_factory=dict)
    within_noise: bool = False          # the gain did not clear the floor and was reported as 1.0
    measured: float | None = None       # the raw worst-shape bound, kept only when it was rejected
    usable: bool = True                 # False means nothing was measured at all -- not "no gain"
    note: str = ""
    evidence: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        out = {"protocol": PROTOCOL_VERSION, "evidence": self.evidence,
               "speedup": round(self.speedup, 4), "median": round(self.median, 4),
               "noise_floor": round(self.noise_floor, 4), "within_noise": self.within_noise,
               "usable": self.usable,
               "shapes": {k: round(v, 4) for k, v in self.shapes.items()}, "note": self.note}
        if self.measured is not None:
            out["measured"] = round(self.measured, 4)
        return out


def _bootstrap_lower_bound(ratios: list[float], *, draws: int = BOOTSTRAP_DRAWS,
                           confidence: float = CONFIDENCE, seed: int = 0) -> float:
    """The lower bound of the confidence interval on the median ratio.

    Seeded, because a gate whose verdict changes between identical runs is not a gate. The seed is
    fixed rather than drawn from the clock for the same reason the rest of this pipeline pins
    everything it can.
    """
    if not ratios:
        return 0.0
    if len(ratios) == 1:
        return ratios[0]
    import random
    rng = random.Random(seed)
    n = len(ratios)
    medians = []
    for _ in range(draws):
        medians.append(statistics.median(rng.choice(ratios) for _ in range(n)))
    medians.sort()
    index = int((1.0 - confidence) * len(medians))
    return medians[min(index, len(medians) - 1)]


def _paired_ratios(reference: Callable[[object], float], candidate: Callable[[object], float],
                   draw_probe: Callable[[int], object], samples: int,
                   observations: list | None = None) -> list[float]:
    """Time the two alternately on the same fresh probe. -> one ratio per sample."""
    ratios = []
    for i in range(samples):
        probe = draw_probe(i)
        # Order alternates: whichever runs first pays for whatever the other then finds warm.
        if i % 2 == 0:
            t_ref, t_cand = reference(probe), candidate(probe)
        else:
            t_cand, t_ref = candidate(probe), reference(probe)
        if not all(math.isfinite(t) and t > 0 for t in (t_ref, t_cand)):
            raise ValueError("measurement must be finite and strictly positive")
        ratio = t_ref / t_cand
        if not math.isfinite(ratio) or ratio <= 0:
            raise ValueError("invalid cost ratio")
        ratios.append(ratio)
        if observations is not None:
            observations.append({"reference": t_ref, "candidate": t_cand,
                                 "reference_first": i % 2 == 0})
    return ratios


def measure(reference: Callable[[object], float], candidate: Callable[[object], float],
            draw_probe: Callable[[str, int], object], shapes: list[str], *,
            samples: int = SAMPLES_PER_SHAPE, warmups: int = WARMUP_PAIRS) -> SpeedResult:
    """-> the speedup a score may use, which is the worst shape's lower bound.

    `reference` and `candidate` each measure the COST of one probe and return it. Keeping the
    measurement inside the callables is what lets a compiled subject be measured fairly: it times
    its own work rather than being charged for process startup and transport, which would otherwise
    dominate exactly the quick subjects this pipeline has the most of.

    COST IS NOT NECESSARILY TIME, and that is why these are callables returning a float rather than
    a stopwatch this module owns. Wall-clock is the default and the noisiest choice available; a
    routine running in a closed simulator can report cycles, which are exact and identical across
    runs, and a CPU kernel can report instructions retired or allocations made. Everything below --
    interleaving, alternating order, the noise floor, the bootstrap, taking the worst shape -- is
    arithmetic on ratios and does not care which cost was measured.

    A cost that is exact makes most of this module redundant rather than wrong: the noise floor of a
    simulator's cycle count comes out at exactly 1.0, so the lower bound equals the median and
    nothing is discarded as noise. Paying for the statistics in that case is the price of one
    interface instead of two.
    """
    if not shapes:
        return SpeedResult(0.0, 0.0, 0.0, usable=False, note="no shape was given to time")

    if samples < 2 or warmups < 0:
        raise ValueError("at least two sample pairs and non-negative warmups are required")
    per_shape, floors, evidence, medians = {}, [], {}, {}
    for shape in shapes:
        record = {"warmup_pairs": warmups, "samples": [], "self_samples": []}
        evidence[shape] = record
        try:
            _paired_ratios(reference, candidate, lambda i: draw_probe(shape, i), warmups)
            ratios = _paired_ratios(reference, candidate,
                                    lambda i: draw_probe(shape, i + warmups), samples,
                                    record["samples"])
            self_ratios = _paired_ratios(reference, reference,
                                         lambda i: draw_probe(shape, i + warmups), samples,
                                         record["self_samples"])
        except Exception as exc:
            return SpeedResult(0.0, 0.0, 0.0, usable=False, evidence=evidence,
                               note="timing failed on %r: %s" % (shape, exc))
        lower = _bootstrap_lower_bound(ratios)
        upper = 1.0 / _bootstrap_lower_bound([1.0 / r for r in ratios])
        self_lower = _bootstrap_lower_bound(self_ratios)
        self_upper = 1.0 / _bootstrap_lower_bound([1.0 / r for r in self_ratios])
        noise = max(1.0, self_upper, 1.0 / self_lower)
        # Uncertain differences are neutral; an established slowdown must never become a gain.
        adjusted = lower if lower > noise else (upper if upper < 1.0 / noise else 1.0)
        per_shape[shape] = adjusted
        medians[shape] = statistics.median(ratios)
        floors.append(noise)
        record.update(lower=lower, upper=upper, noise_floor=noise, speedup=adjusted)

    worst_shape = min(per_shape, key=lambda s: per_shape[s])
    speedup = per_shape[worst_shape]
    noise = max(floors) if floors else 1.0
    if speedup == 1.0:
        # REPORTED AS 1.0, not as the raw ratio. `speedup` is the field a score is computed from, so
        # leaving 1.03x in it and setting a flag would mean every downstream caller has to remember
        # to re-check the flag -- and the one that forgets pays for noise. The measured value is
        # kept in `measured` for a reader who wants to see what was rejected.
        return SpeedResult(1.0, statistics.median(medians.values()), noise, per_shape,
                           within_noise=True, measured=medians[worst_shape], evidence=evidence,
                           note=("the measured gain (%.3fx on the worst shape, %r) does not clear "
                                 "this machine's own noise (%.3fx); reported as 1.0x, which is what "
                                 "was actually established" % (speedup, worst_shape, noise)))
    return SpeedResult(speedup, statistics.median(medians.values()), noise, per_shape,
                       evidence=evidence, note="worst shape %r of %d" % (worst_shape, len(per_shape)))


def standalone_source() -> str:
    """Embed this exact protocol in emitted verifiers without a runtime FRF dependency."""
    from pathlib import Path
    return Path(__file__).read_text(encoding="utf-8").replace(
        "", "")

"""Stable filesystem observations, including file contents and link targets."""
import hashlib
import os
import stat


def tree_lines(root, exclude=()):
    lines = []
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in exclude)
        for name in sorted(dirs + files):
            path = os.path.join(base, name)
            relative = os.path.relpath(path, root)
            if any(part in exclude for part in relative.split(os.sep)):
                continue
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                value = "link " + os.readlink(path)
            elif stat.S_ISDIR(info.st_mode):
                value = "directory"
            elif stat.S_ISREG(info.st_mode):
                digest = hashlib.sha256()
                # Do not follow a link swapped in after lstat, or block on a special file.
                descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(descriptor, "rb") as handle:
                    opened = os.fstat(handle.fileno())
                    if not stat.S_ISREG(opened.st_mode):
                        raise ValueError("file type changed during observation")
                    for block in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(block)
                value = "file %s %d %s" % (
                    "x" if opened.st_mode & 0o111 else "-", opened.st_size, digest.hexdigest())
            else:
                value = "special %o" % stat.S_IFMT(info.st_mode)
            # JSON quoting makes filenames containing newlines unambiguous to line masking.
            import json
            lines.append(json.dumps([relative, value], ensure_ascii=True, separators=(",", ":")))
    return sorted(lines)


def standalone_source():
    from pathlib import Path
    return Path(__file__).read_text(encoding="utf-8")

"""Minimum evidence required for a process scenario to measure useful execution.

This excludes control queries and proven failed execution. It is a necessary check, not a
proof of repository-wide coverage or performance significance.
"""
import hashlib


_CONTROL = {"--help", "-h", "--version", "-V", "help", "version"}


def command_family(scenario, input_path=None):
    words = []
    for arg in scenario['steps'][0].get('argv', [])[1:3]:
        if (arg == input_path or arg.startswith('-') or arg.isdigit()
                or any(mark in arg for mark in ('/', '.', ' '))):
            break
        words.append(arg)
    return ' '.join(words) or 'direct-input'


def control_step(step):
    args = step.get("argv") or []
    if not args or args[0] != "{PROGRAM}":
        return False
    options = args[1:args.index("--")] if "--" in args else args[1:]
    return options == ["-v"] or any(arg in _CONTROL for arg in options)


def output_signature(expectation):
    channels = [expectation.get(name, {}) for name in ("exit_code", "stdout", "stderr")]
    if not all(rule.get("graded") and not rule.get("masked") for rule in channels):
        return None
    if not any(rule.get("line_count", 0) > 0 for rule in channels[1:]):
        return None
    return tuple((rule.get("digest"), rule.get("line_count")) for rule in channels)


def control_output_signatures(scenarios, expectations):
    """Stable explicit help/version output identifies disguised control queries too."""
    signatures = set()
    for scenario in scenarios:
        rules = expectations.get(scenario["probe_id"], [])
        for index, step in enumerate(scenario.get("steps", [])):
            if index < len(rules) and control_step(step):
                signature = output_signature(rules[index])
                if signature is not None:
                    signatures.add(signature)
    return signatures


def timing_steps(scenario):
    """Direct subject steps with workload input; shell wrappers require separate evidence."""
    selected = []
    for index, step in enumerate(scenario.get("steps", ())):
        args = step.get("argv") or []
        if not args or args[0] != "{PROGRAM}":
            continue
        if control_step(step):
            continue
        if len(args) > 1 or step.get("stdin") or scenario.get("fixture"):
            selected.append(index)
    return selected


def eligible_timing_steps(scenario, expectations, controls=()):
    """Require stable success on a workload step, not merely printed error text."""
    zero = "sha256:" + hashlib.sha256(b"0").hexdigest()
    selected = []
    for index in timing_steps(scenario):
        if index >= len(expectations):
            continue
        if output_signature(expectations[index]) in controls:
            continue
        rule = expectations[index].get("exit_code", {})
        if (rule.get("graded") and rule.get("digest") == zero
                and rule.get("line_count") == 1 and not rule.get("masked")):
            selected.append(index)
    return selected


def standalone_source():
    from pathlib import Path
    return Path(__file__).read_text(encoding="utf-8")

"""Bounded, deadline-aware subprocess pipe transport for one-shot and JSON-lines subjects."""
import os
import selectors
import subprocess
import time


class OutputLimitExceeded(RuntimeError):
    pass


class PipeTransport:
    def __init__(self, process, *, output_limit=64 * 1024 * 1024):
        self.process = process
        self.output_limit = output_limit
        self.pending = bytearray()
        self.stderr_tail = bytearray()
        self.stderr_output = bytearray()
        self.readers = {process.stdout.fileno(): 'stdout', process.stderr.fileno(): 'stderr'}
        for stream in (process.stdin, process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)

    def exchange(self, payload, *, timeout, line=False):
        data = payload.encode('utf-8') if isinstance(payload, str) else (payload or b'')
        if line and self.pending.strip():
            raise RuntimeError('subject emitted an unsolicited response')
        deadline = time.monotonic() + timeout
        offset = 0
        output = bytearray(self.pending)
        received = len(output)
        self.stderr_output.clear()
        self.pending.clear()
        with selectors.DefaultSelector() as poll:
            for descriptor, channel in self.readers.items():
                poll.register(descriptor, selectors.EVENT_READ, channel)
            if data and not self.process.stdin.closed:
                poll.register(self.process.stdin.fileno(), selectors.EVENT_WRITE, 'stdin')
            elif not line and not self.process.stdin.closed:
                self.process.stdin.close()
            while poll.get_map():
                if line and offset == len(data) and b'\n' in output:
                    answer, _, rest = output.partition(b'\n')
                    self.pending.extend(rest)
                    return answer.decode('utf-8')
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(self.process.args, timeout)
                for key, _ in poll.select(remaining):
                    if key.data == 'stdin':
                        try:
                            offset += os.write(key.fd, data[offset:offset + 4096])
                        except BrokenPipeError:
                            if line:
                                raise RuntimeError('subject closed input before receiving the request')
                            offset = len(data)
                        if offset == len(data):
                            poll.unregister(key.fd)
                            if not line:
                                self.process.stdin.close()
                        continue
                    block = os.read(key.fd, 65536)
                    if not block:
                        poll.unregister(key.fd)
                        self.readers.pop(key.fd, None)
                        continue
                    received += len(block)
                    if received > self.output_limit:
                        raise OutputLimitExceeded('subject output exceeds %d bytes' % self.output_limit)
                    if key.data == 'stdout':
                        output.extend(block)
                    else:
                        if not line:
                            self.stderr_output.extend(block)
                        self.stderr_tail.extend(block)
                        if len(self.stderr_tail) > 8192:
                            del self.stderr_tail[:-8192]
            if line:
                if offset == len(data) and b'\n' in output:
                    answer, _, rest = output.partition(b'\n')
                    self.pending.extend(rest)
                    return answer.decode('utf-8')
                raise RuntimeError('subject exited without a complete response')
            # Keep the exited leader unreaped until its process group has been cleaned up.
            while os.waitid(os.P_PID, self.process.pid, os.WEXITED | os.WNOWAIT | os.WNOHANG) is None:
                if time.monotonic() >= deadline:
                    raise subprocess.TimeoutExpired(self.process.args, timeout)
                time.sleep(0.001)
            return output.decode('utf-8', 'surrogateescape')


def bounded_run(argv, *, cwd=None, env=None, input=None, timeout=300, output_limit=64 * 1024 * 1024,
                spawn=None, stop=None):
    process = (spawn() if spawn is not None else subprocess.Popen(
        argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True))
    transport = PipeTransport(process, output_limit=output_limit)
    finished = False
    try:
        out = transport.exchange(input, timeout=timeout)
        err = transport.stderr_output.decode('utf-8', 'surrogateescape')
        finished = True
    finally:
        if stop is not None:
            stop(finished)
        else:
            import signal
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=5)
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                stream.close()
            except OSError:
                pass
    return subprocess.CompletedProcess(argv, process.returncode,
                                       out.replace('\r\n', '\n').replace('\r', '\n'),
                                       err.replace('\r\n', '\n').replace('\r', '\n'))


def standalone_source():
    from pathlib import Path
    return Path(__file__).read_text(encoding='utf-8')

"""Observe actual kernel exec events from a privileged process outside the subject root."""
import ctypes
import errno
import json
import os
import resource
import signal
import subprocess
import time
from pathlib import Path


class AuditedProcess:
    """Pipe-process interface used by the existing bounded transport."""
    def __init__(self, pid, argv, stdin, stdout, stderr, audit_path):
        self.pid, self.args, self.audit_path = pid, argv, audit_path
        self.stdin = os.fdopen(stdin, 'wb', buffering=0)
        self.stdout = os.fdopen(stdout, 'rb', buffering=0)
        self.stderr = os.fdopen(stderr, 'rb', buffering=0)
        self.returncode = None
        self.pidfd = os.pidfd_open(pid)

    def poll(self):
        if self.returncode is None:
            found, status = os.waitpid(self.pid, os.WNOHANG)
            if found:
                self.returncode = os.waitstatus_to_exitcode(status)
                os.close(self.pidfd)
                self.pidfd = None
        return self.returncode

    @property
    def subject_pid(self):
        with open(self.audit_path) as handle:
            event = json.loads(handle.readline(4096))
        if event.get('event') != 'spawn':
            raise RuntimeError('execution observer did not identify its subject')
        return event['pid']

    def wait(self, timeout=None):
        deadline = time.monotonic() + timeout if timeout is not None else float('inf')
        while self.poll() is None:
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(self.args, timeout)
            time.sleep(0.001)
        return self.returncode

    def send_signal(self, number):
        if self.pidfd is not None:
            try:
                signal.pidfd_send_signal(self.pidfd, number)
            except ProcessLookupError:
                pass

    def kill(self):
        self.send_signal(signal.SIGKILL)

    def terminate(self):
        self.send_signal(signal.SIGTERM)


def _supervise(root, argv, cwd, environment, streams, audit_path, allowed):
    libc = ctypes.CDLL(None, use_errno=True)
    libc.ptrace.restype = ctypes.c_long
    live = set()
    main_status = None
    denied = False
    event_count = 0

    def ptrace(request, pid, address=0, data=0):
        result = libc.ptrace(request, pid, ctypes.c_void_p(address), ctypes.c_void_p(data))
        if result < 0:
            raise OSError(ctypes.get_errno(), 'execution observer ptrace operation failed')
        return result

    with open(audit_path, 'w', buffering=1) as log:
        def write(event):
            log.write(json.dumps(event, separators=(',', ':')) + '\n')
        try:
            libc.prctl(36, 1, 0, 0, 0)
            ready_read, ready_write = os.pipe()
            main = os.fork()
            if main == 0:
                try:
                    os.close(ready_write)
                    if os.read(ready_read, 1) != b'1':
                        os._exit(126)
                    for target, source in enumerate(streams):
                        os.dup2(source, target)
                    os.closerange(3, 1048576)
                    root.traceable = True
                    root._enter(cwd)
                    os.execvpe(argv[0], argv, environment)
                except BaseException:
                    os._exit(126)
            live.add(main)
            write({'event': 'spawn', 'pid': main})
            os.close(ready_read)
            try:
                ptrace(0x4206, main, data=(1 << 20) | 2 | 4 | 8 | 16)
                os.write(ready_write, b'1')
            finally:
                os.close(ready_write)
            while live:
                pid, status = os.waitpid(-1, 0x40000000)
                if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                    live.discard(pid)
                    if pid == main:
                        main_status = os.waitstatus_to_exitcode(status)
                    continue
                event, number = status >> 16, os.WSTOPSIG(status)
                if event in (1, 2, 3):
                    child = ctypes.c_ulong()
                    ptrace(0x4201, pid, data=ctypes.addressof(child))
                    live.add(child.value)
                    if len(live) > 2048:
                        raise RuntimeError('execution observer process limit exceeded')
                elif event == 4:
                    previous_tid = ctypes.c_ulong()
                    ptrace(0x4201, pid, data=ctypes.addressof(previous_tid))
                    if previous_tid.value and previous_tid.value != pid:
                        live.discard(previous_tid.value)
                        live.add(pid)
                    event_count += 1
                    if event_count > 10000:
                        raise RuntimeError('execution observer event limit exceeded')
                    old_gid, old_uid = libc.setfsgid(root.uid), libc.setfsuid(root.uid)
                    try:
                        name = os.readlink('/proc/%d/exe' % pid)
                        info = os.stat('/proc/%d/exe' % pid)
                    finally:
                        libc.setfsuid(old_uid)
                        libc.setfsgid(old_gid)
                    accepted = allowed is None or (info.st_dev, info.st_ino) in allowed
                    write({'event': 'exec', 'pid': pid, 'path': name.replace(str(root.path), ''),
                           'device': info.st_dev, 'inode': info.st_ino, 'allowed': accepted})
                    if not accepted:
                        denied = True
                        for child in live:
                            try:
                                os.kill(child, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                        continue
                if event == 128 and number in (signal.SIGSTOP, signal.SIGTSTP, signal.SIGTTIN, signal.SIGTTOU):
                    ptrace(0x4208, pid)
                else:
                    try:
                        ptrace(7, pid, data=0 if event else number)
                    except OSError as error:
                        if error.errno != errno.ESRCH:
                            raise
            write({'event': 'complete', 'main_status': main_status, 'denied': denied})
            return 126 if denied else (main_status if main_status is not None else 126)
        except BaseException as error:
            write({'event': 'failed', 'error_type': type(error).__name__})
            for pid in live:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            return 126


def start_audited_process(root, argv, cwd, environment, audit_path, allowed):
    parent_pid = os.getpid()
    stdin_read, stdin_write = os.pipe()
    stdout_read, stdout_write = os.pipe()
    stderr_read, stderr_write = os.pipe()
    all_fds = (stdin_read, stdin_write, stdout_read, stdout_write, stderr_read, stderr_write)
    try:
        pid = os.fork()
    except BaseException:
        for descriptor in all_fds:
            os.close(descriptor)
        raise
    if pid == 0:
        try:
            os.setsid()
            libc = ctypes.CDLL(None, use_errno=True)
            if libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent_pid:
                os._exit(126)
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            keep = {0, 1, 2, stdin_read, stdout_write, stderr_write}
            for item in Path('/proc/self/fd').iterdir():
                descriptor = int(item.name)
                if descriptor not in keep:
                    try:
                        os.close(descriptor)
                    except OSError:
                        pass
            result = _supervise(root, argv, cwd, environment, (stdin_read, stdout_write, stderr_write),
                                audit_path, allowed)
            if result < 0:
                if -result not in (signal.SIGKILL, signal.SIGSTOP):
                    signal.signal(-result, signal.SIG_DFL)
                os.kill(os.getpid(), -result)
            os._exit(result)
        except BaseException:
            os._exit(126)
    for descriptor in (stdin_read, stdout_write, stderr_write):
        os.close(descriptor)
    return AuditedProcess(pid, argv, stdin_write, stdout_read, stderr_read, audit_path)


def standalone_source():
    return Path(__file__).read_text()

"""Filesystem-confined subject processes managed by a trusted Linux verifier.

Requires a root verifier inside a resource-limited container. This primitive does not certify
the caller's timing protocol, target-language build, or output/descendant lifecycle management.
"""

import ctypes
import json
import errno
import os
import resource
import signal
import shutil
import stat
import subprocess
import tempfile
import tarfile
import threading
import time
from pathlib import Path


RUNTIME_PATHS = ('usr', 'opt', 'bin', 'sbin', 'lib', 'lib64', 'etc/alternatives',
                 'etc/ld.so.cache', 'etc/ld.so.conf', 'etc/ld.so.conf.d',
                 'etc/nsswitch.conf', 'etc/localtime', 'etc/ssl/certs')
_RESERVED_UIDS = set()
_UID_LOCK = threading.Lock()
ISOLATION_CHECKS = ('distinct_users', 'unconfined_control_readable', 'outside_read_denied', 'network_denied',
                    'reference_signal_denied', 'idle_side_stopped', 'idle_side_resumed',
                    'probe_processes_removed')


def extract_fixture(path, destination, *, max_members=10000, max_bytes=64 * 1024 * 1024):
    """Extract bounded data archives without version-specific extractall safety defaults."""
    root = Path(destination)
    total = 0
    links = []
    with tarfile.open(path) as archive:
        for count, member in enumerate(archive, 1):
            name = Path(member.name)
            if count > max_members or name.is_absolute() or '..' in name.parts:
                raise ValueError('unsafe or oversized fixture archive')
            if not (member.isdir() or member.isfile() or member.issym() or member.islnk()):
                raise ValueError('special files are not allowed in fixtures')
            total += member.size
            if total > max_bytes or member.size < 0:
                raise ValueError('fixture data exceeds its byte budget')
            if member.isdir():
                workspace_directory(root, str(name))
                continue
            workspace_directory(root, str(name.parent))
            target = root / name
            if member.issym() or member.islnk():
                link = Path(member.linkname)
                resolved = Path(os.path.normpath(str(name.parent / link if member.issym() else link)))
                if link.is_absolute() or '..' in resolved.parts:
                    raise ValueError('fixture link leaves its workspace')
                links.append((target, member.linkname, root / resolved, member.issym()))
                continue
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, 'wb') as output, archive.extractfile(member) as source:
                shutil.copyfileobj(source, output, 1024 * 1024)
                os.fchmod(output.fileno(), member.mode & 0o777)
        # Links are created only after all writes, so no archive member is written through a link.
        for target, _, resolved, symbolic in links:
            if not symbolic:
                workspace_directory(root, str(resolved.relative_to(root).parent))
                if not resolved.is_file() or resolved.is_symlink():
                    raise ValueError('fixture hardlink has no regular target')
                os.link(resolved, target, follow_symlinks=False)
        for target, link, _, symbolic in links:
            if symbolic:
                target.symlink_to(link)


def workspace_directory(workspace, relative, uid=None):
    """Privileged preparation must not follow a subject-created directory symlink."""
    relative = Path(os.path.normpath(relative))
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('working directory leaves the scenario workspace')
    current = Path(workspace)
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('workspace preparation cannot traverse a symlink')
        if not current.exists():
            current.mkdir()
            if uid is not None:
                os.chown(current, uid, uid)
        elif not current.is_dir():
            raise ValueError('working directory is not a directory')
    return str(current)


def _processes_for(uid, *, include_zombies=False):
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            lines = (path / 'status').read_text().splitlines()
        except (OSError, UnicodeError):
            continue
        values = {key: value.strip() for key, _, value in (line.partition(':') for line in lines)}
        if (str(uid) in values.get('Uid', '').split()[:3]
                and (include_zombies or not values.get('State', '').startswith('Z'))):
            yield int(path.name)


def _copy_runtime(source, target):
    """Only root-owned, non-writable runtime files may share inodes with the verifier.

    A FILE THAT FAILS EITHER TEST IS COPIED, NOT REFUSED. The danger is the shared inode: a file
    something else can still write to must not be the same inode the verifier reads, because the
    owner could change it after the check. Copying breaks the share, and the copy this process makes
    is root-owned and stripped of group and other write -- which is the property the check is
    protecting, reached by a different route.

    REFUSING A NON-ROOT OWNER OUTRIGHT COST EVERY JAVASCRIPT AND TYPESCRIPT TASK. The official node
    image ships `/opt/yarn-v*` owned by uid 1000, so `untrusted runtime file owner: /opt/yarn-v...`
    ended the replay for 24 candidates in one production run -- 21 typescript and 3 javascript, and
    it was the single reason those two languages produced nothing at all while python produced 33.
    The file is a stock part of a pinned public image, not something a candidate put there, and it
    is read by the verifier rather than executed on its behalf.
    """
    info = os.stat(source, follow_symlinks=False)
    if info.st_uid != 0 or info.st_mode & 0o022:
        shutil.copy2(source, target, follow_symlinks=False)
        os.chmod(target, stat.S_IMODE(info.st_mode) & ~0o022)
        if info.st_uid != 0:
            # The copy belongs to this process; say so explicitly rather than inheriting whatever
            # `copy2` left, so the verifier's tree is uniformly root-owned.
            os.chown(target, 0, 0, follow_symlinks=False)
        return str(target)
    try:
        os.link(source, target, follow_symlinks=False)
    except OSError as error:
        if error.errno != errno.EXDEV:
            raise
        shutil.copy2(source, target, follow_symlinks=False)
    return str(target)


def _own_tree(root, uid):
    for directory, dirs, files in os.walk(root, followlinks=False):
        os.chown(directory, uid, uid)
        for name in dirs + files:
            os.chown(os.path.join(directory, name), uid, uid, follow_symlinks=False)


class Root:
    """A private root and workspace. Source symlinks remain symlinks inside the new root."""

    def __init__(self, source, *, uid, runtime_paths=RUNTIME_PATHS, runtime_base='/', runtime_environment=None):
        if os.geteuid() != 0:
            raise PermissionError('subject confinement requires a root verifier')
        if uid <= 0:
            raise ValueError('the subject uid must be unprivileged')
        if not (Path('/.dockerenv').exists() or Path('/run/.containerenv').exists()):
            raise RuntimeError('subject roots must be managed inside a Linux container')
        for relative in runtime_paths:
            if Path(relative).is_absolute() or '..' in Path(relative).parts:
                raise ValueError('runtime paths must stay within the new root')
        if not hasattr(os, 'pidfd_open') or not hasattr(signal, 'pidfd_send_signal'):
            raise RuntimeError('pidfd support is required for subject cleanup')
        self.uid = uid
        self.runtime_environment = dict(runtime_environment or {})
        base = Path(runtime_base)
        if not base.is_absolute() or base.is_symlink() or not base.is_dir():
            raise ValueError('runtime base must be an absolute directory')
        with _UID_LOCK:
            if uid in _RESERVED_UIDS or next(_processes_for(uid), None) is not None:
                raise ValueError('subject uid is already in use')
            _RESERVED_UIDS.add(uid)
        try:
            self.room = Path(tempfile.mkdtemp(prefix='frf-isolated-'))
            self.path = self.room / 'root'
            self.path.mkdir(mode=0o755)
        except BaseException:
            with _UID_LOCK:
                _RESERVED_UIDS.discard(uid)
            if hasattr(self, 'room'):
                shutil.rmtree(self.room, ignore_errors=True)
            raise
        self.closed = False
        self.processes = []
        self.execution_audit = None
        self.execution_logs = []
        try:
            self._libc = ctypes.CDLL(None, use_errno=True)
            self._libc.syscall.restype = ctypes.c_long
            if self._libc.prctl(36, 1, 0, 0, 0) != 0:
                raise OSError(ctypes.get_errno(), 'child subreaper setup failed')
            for relative in runtime_paths:
                source_path = base / relative
                target = self.path / relative
                if not source_path.exists() and not source_path.is_symlink():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                if source_path.is_symlink():
                    target.symlink_to(os.readlink(source_path))
                elif source_path.is_dir():
                    shutil.copytree(source_path, target, symlinks=True, copy_function=_copy_runtime)
                    for directory, _dirs, _files in os.walk(target, followlinks=False):
                        info = os.stat(directory, follow_symlinks=False)
                        os.chmod(directory, stat.S_IMODE(info.st_mode) & ~0o022)
                else:
                    if relative == 'etc/ld.so.cache':
                        shutil.copy2(source_path, target)
                    else:
                        _copy_runtime(source_path, target)
            # Multi-stage images can add shared libraries after their base cache was built.
            # Keep this cache private and rebuild it without modifying shared library symlinks.
            linker = shutil.which('ldconfig')
            if linker is None:
                raise RuntimeError('ldconfig is required to prepare the confined runtime')
            configured = subprocess.run([linker, '-r', str(self.path), '-X'],
                                        capture_output=True, text=True, timeout=60)
            if configured.returncode != 0:
                raise RuntimeError('confined runtime linker configuration failed: ' + configured.stderr[-500:])
            shutil.copytree(source, self.path / 'app', symlinks=True)
            _own_tree(self.path / 'app', uid)
            for name in ('tmp', 'workspace', 'home/subject', 'dev/shm'):
                directory = self.path / name
                directory.mkdir(parents=True, exist_ok=True)
                os.chown(directory, uid, uid)
            etc = self.path / 'etc'
            etc.mkdir(exist_ok=True)
            (etc / 'passwd').write_text('subject:x:%d:%d::/home/subject:/bin/sh\n' % (uid, uid))
            (etc / 'group').write_text('subject:x:%d:\n' % uid)
            for name, minor in (('null', 3), ('zero', 5), ('random', 8), ('urandom', 9)):
                device = self.path / 'dev' / name
                os.mknod(device, stat.S_IFCHR | 0o666, os.makedev(1, minor))
                os.chmod(device, 0o666)
            self._seccomp = ctypes.CDLL('libseccomp.so.2', use_errno=True)
            self._seccomp.seccomp_init.argtypes = [ctypes.c_uint32]
            self._seccomp.seccomp_init.restype = ctypes.c_void_p
            self._seccomp.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
            self._seccomp.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                                     ctypes.c_int, ctypes.c_uint]
            self._seccomp.seccomp_load.argtypes = [ctypes.c_void_p]
            self._seccomp.seccomp_release.argtypes = [ctypes.c_void_p]
        except BaseException:
            self.close()
            raise

    def prepare(self, fixture_dir=None):
        """Prepare one invocation outside the measured interval."""
        if self.closed:
            raise RuntimeError('subject root is closed')
        workspace = self.path / 'workspace'
        shutil.rmtree(workspace)
        if fixture_dir:
            shutil.copytree(fixture_dir, workspace, symlinks=True)
        else:
            workspace.mkdir()
        _own_tree(workspace, self.uid)

    def audit_execution(self, paths=None):
        """Observe actual executable inodes and optionally restrict their allowlist."""
        if self.closed or self.execution_audit is not None:
            raise RuntimeError('execution observer cannot replace an active policy')
        allowed = None
        if paths is not None:
            allowed = set()
            for name in paths:
                relative = Path(name)
                if not relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('approved executable must be inside its subject root')
                path = self.path / str(relative).lstrip('/')
                if not path.resolve().is_relative_to(self.path.resolve()):
                    raise ValueError('approved executable escapes its subject root')
                info = path.stat()
                if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
                    raise ValueError('approved executable must be immutable and root owned')
                allowed.add((info.st_dev, info.st_ino))
            if not allowed:
                raise ValueError('execution observer requires an approved entry point')
        self.execution_audit = {'allowed': allowed, 'paths': None if paths is None else list(paths)}

    def execution_report(self):
        events = []
        complete = bool(self.execution_logs)
        denied = False
        for path in self.execution_logs:
            if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
                complete = False
                continue
            try:
                records = [json.loads(line) for line in path.read_text().splitlines()]
            except (OSError, ValueError):
                complete = False
                continue
            complete = complete and bool(records) and records[-1].get('event') == 'complete'
            denied = denied or any(record.get('allowed') is False or record.get('denied') is True
                                   for record in records)
            events.extend(record for record in records if record.get('event') == 'exec')
        return {'enabled': self.execution_audit is not None, 'complete': complete, 'denied': denied,
                'enforced': self.execution_audit is not None and self.execution_audit['allowed'] is not None,
                'events': events}

    def _enter(self, cwd):
        os.chroot(self.path)
        os.chdir(cwd)
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_NPROC, (512, 512))
        resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024))
        resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024 * 1024, 64 * 1024 * 1024))
        os.setgroups([])
        os.setgid(self.uid)
        os.setuid(self.uid)
        if self._libc.prctl(38, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), 'no_new_privs failed')
        if getattr(self, 'traceable', False) and self._libc.prctl(4, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), 'execution audit visibility failed')
        context = self._seccomp.seccomp_init(0x7fff0000)
        if not context:
            raise OSError('seccomp initialization failed')
        try:
            # Anonymous socket pairs only connect a process to its own descendants;
            # Rust uses them when spawning compiler/worker processes. Creating sockets
            # that can connect to an external or reference endpoint remains forbidden.
            for name in (b'socket', b'ptrace', b'process_vm_readv', b'process_vm_writev',
                         b'unshare', b'setns', b'mount', b'umount2', b'pivot_root', b'chroot',
                         b'bpf', b'userfaultfd', b'io_uring_setup', b'keyctl', b'add_key', b'request_key',
                         b'perf_event_open', b'open_by_handle_at', b'pidfd_getfd', b'shmget', b'shmat',
                         b'msgget', b'msgsnd', b'msgrcv', b'semget', b'semop', b'semtimedop'):
                syscall = self._seccomp.seccomp_syscall_resolve_name(name)
                if syscall >= 0 and self._seccomp.seccomp_rule_add(context, 0x00050001, syscall, 0) != 0:
                    raise OSError('seccomp rule installation failed')
            if self._seccomp.seccomp_load(context) != 0:
                raise OSError('seccomp loading failed')
        finally:
            self._seccomp.seccomp_release(context)

    def spawn(self, argv, *, cwd='/workspace', environment=None):
        if self.closed:
            raise RuntimeError('subject root is closed')
        if not cwd.startswith('/'):
            raise ValueError('subject cwd must be absolute inside its root')
        env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': '/home/subject',
               'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC'}
        env.update(environment or {})
        env.update(self.runtime_environment)
        env['HOME'] = '/home/subject'
        if self.execution_audit is not None:
            path = self.room / ('execution-%d.jsonl' % len(self.execution_logs))
            self.execution_logs.append(path)
            process = start_audited_process(self, argv, cwd, env, path, self.execution_audit['allowed'])
            self.processes.append(process)
            return process
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, env=env, close_fds=True,
                                   start_new_session=True, preexec_fn=lambda: self._enter(cwd))
        self.processes.append(process)
        return process

    def _signal(self, pid, number):
        try:
            descriptor = os.pidfd_open(pid)
        except ProcessLookupError:
            return
        try:
            status = Path('/proc/%d/status' % pid).read_text()
            uid_line = next(line for line in status.splitlines() if line.startswith('Uid:'))
            if str(self.uid) in uid_line.split()[1:4]:
                signal.pidfd_send_signal(descriptor, number)
        except (ProcessLookupError, FileNotFoundError):
            pass
        finally:
            os.close(descriptor)

    def run(self, argv, *, cwd='/workspace', environment=None, input=None, timeout=300):
        self.resume()
        return bounded_run(argv, input=input, timeout=timeout,
                           spawn=lambda: self.spawn(argv, cwd=cwd, environment=environment),
                           stop=lambda finished: self.pause() if finished else self.stop())

    def pause(self):
        if self.closed:
            raise RuntimeError('subject root is closed')
        deadline = time.monotonic() + 5
        while True:
            for pid in _processes_for(self.uid):
                self._signal(pid, signal.SIGSTOP)
            stopped = True
            for pid in _processes_for(self.uid):
                try:
                    lines = Path('/proc/%d/status' % pid).read_text().splitlines()
                except FileNotFoundError:
                    continue
                state = next(line for line in lines if line.startswith('State:')).split()[1]
                stopped = stopped and state in ('T', 't')
            if stopped:
                return
            if time.monotonic() >= deadline:
                raise RuntimeError('untimed subject did not stop')
            time.sleep(0.005)

    def resume(self):
        if self.closed:
            raise RuntimeError('subject root is closed')
        for pid in _processes_for(self.uid):
            self._signal(pid, signal.SIGCONT)

    def stop(self):
        if not self.closed:
            deadline = time.monotonic() + 5
            while True:
                pids = list(_processes_for(self.uid))
                if not pids:
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError('subject processes survived cleanup; terminate its container')
                for pid in pids:
                    self._signal(pid, signal.SIGKILL)
                time.sleep(0.01)
            for process in self.processes:
                process.wait(timeout=5)
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None:
                        try:
                            stream.close()
                        except OSError:
                            pass
            for pid in _processes_for(self.uid, include_zombies=True):
                try:
                    os.waitpid(pid, os.WNOHANG)
                except ChildProcessError:
                    pass
            self.processes.clear()

    def close(self):
        if not self.closed:
            self.stop()
            shutil.rmtree(self.room, ignore_errors=True)
            with _UID_LOCK:
                _RESERVED_UIDS.discard(self.uid)
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def standalone_source():
    return (execution_source() + '\n' + Path(__file__).read_text(encoding='utf-8')
            .replace('from __future__ import annotations\n', '')
            .replace('from .transport import bounded_run\n', '')
            .replace('from .exec_audit import start_audited_process\n', '')
            .replace('    from .exec_audit import standalone_source as execution_source\n', ''))


def verify_pair(reference, candidate):
    """Check the exact roots used for grading; all probes finish before task execution starts."""
    if reference.uid == candidate.uid or reference.path == candidate.path:
        raise RuntimeError('reference and candidate do not have distinct roots and users')
    descriptor, marker_name = tempfile.mkstemp(prefix='frf-isolation-control-')
    marker = Path(marker_name)
    secret = 'private-' + os.urandom(24).hex()
    with os.fdopen(descriptor, 'w') as handle:
        handle.write(secret)
        os.fchmod(handle.fileno(), 0o644)
    heartbeat = reference.path / 'workspace/heartbeat'
    code = ("import pathlib,time,os; p=pathlib.Path('/workspace/heartbeat'); i=0\n"
            "while True:\n i+=1; p.write_text(str(i)); time.sleep(0.02)\n")
    reference.prepare()
    candidate.prepare()
    try:
        control = bounded_run(['python3', '-c', 'import pathlib,sys;print(pathlib.Path(sys.argv[1]).read_text())',
                               str(marker)], timeout=10,
                              spawn=lambda: subprocess.Popen(
                                  ['python3', '-c', 'import pathlib,sys;print(pathlib.Path(sys.argv[1]).read_text())',
                                   str(marker)], user=candidate.uid, group=candidate.uid, extra_groups=[],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  start_new_session=True))
        if control.returncode != 0 or control.stdout.strip() != secret:
            raise RuntimeError('unconfined control could not read the isolation marker')
        holding = reference.spawn(['python3', '-c', code])
        deadline = time.monotonic() + 5
        while not heartbeat.exists() or not heartbeat.read_text():
            if holding.poll() is not None:
                raise RuntimeError('reference isolation control exited %s: %s' %
                                   (holding.returncode, holding.stderr.read(4096)))
            if time.monotonic() > deadline:
                raise RuntimeError('reference isolation control timed out')
            time.sleep(0.01)
        reference.pause()
        count = heartbeat.read_text()
        time.sleep(0.05)
        stopped = heartbeat.read_text() == count
        attack = '''import json,os,pathlib,socket,sys
result={'uid':os.getuid()}
try:
 pathlib.Path(sys.argv[1]).read_bytes(); result['outside_read_denied']=False
except FileNotFoundError:
 result['outside_read_denied']=True
try:
 socket.socket(socket.AF_INET,socket.SOCK_STREAM); result['network_denied']=False
except PermissionError:
 result['network_denied']=True
try:
 os.kill(int(sys.argv[2]),0); result['reference_signal_denied']=False
except PermissionError:
 result['reference_signal_denied']=True
print(json.dumps(result))
'''
        reference_pid = getattr(holding, 'subject_pid', holding.pid)
        done = candidate.run(['python3', '-c', attack, str(marker), str(reference_pid)], timeout=10)
        if done.returncode != 0:
            raise RuntimeError('candidate isolation control failed: ' + done.stderr[-500:])
        checks = json.loads(done.stdout)
        status = Path('/proc/%d/status' % reference_pid).read_text().splitlines()
        reference_uid = next(line for line in status if line.startswith('Uid:')).split()[1]
        reference.resume()
        deadline = time.monotonic() + 5
        while not heartbeat.read_text() or heartbeat.read_text() == count:
            if holding.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError('reference control did not resume')
            time.sleep(0.01)
        checks.update(distinct_users=checks.pop('uid') == candidate.uid and int(reference_uid) == reference.uid,
                      unconfined_control_readable=True,
                      idle_side_stopped=stopped, idle_side_resumed=True)
    finally:
        candidate.stop()
        reference.stop()
        marker.unlink(missing_ok=True)
    checks['probe_processes_removed'] = not (
        list(_processes_for(reference.uid, include_zombies=True)) or
        list(_processes_for(candidate.uid, include_zombies=True)))
    if any(checks.get(name) is not True for name in ISOLATION_CHECKS):
        raise RuntimeError('subject isolation check failed: ' + json.dumps(checks))
    reference.prepare()
    candidate.prepare()
    return {'checks': checks, 'enforced': True}

"""Trusted target-language builds inside an existing confined candidate root."""
import hashlib
import os
import shutil
import stat
import tomllib
from pathlib import Path


TARGETS = {
    'rust': {'tool': 'cargo', 'entry': 'src/main.rs', 'manifest': 'Cargo.toml'},
    'go': {'tool': 'go', 'entry': 'main.go', 'manifest': 'go.mod'},
    'cpp': {'tool': 'c++', 'entry': 'main.cpp', 'manifest': None},
}


class TargetBuildError(RuntimeError):
    pass


def target_plan(language):
    language = str(language).lower()
    if language not in TARGETS:
        raise ValueError('target language lacks a verified build adapter: ' + language)
    return dict(TARGETS[language], language=language)


def _validate_inputs(directory):
    for parent, directories, files in os.walk(directory, followlinks=False):
        for name in directories + files:
            path = Path(parent) / name
            if path.is_symlink() and not path.resolve().is_relative_to(directory.resolve()):
                raise TargetBuildError('target build input links outside the implementation directory')
            if not path.is_symlink() and not (path.is_file() or path.is_dir()):
                raise TargetBuildError('unsupported target build input type')


def _own(directory, uid):
    for parent, directories, files in os.walk(directory, followlinks=False):
        os.chown(parent, uid, uid)
        for name in directories + files:
            os.chown(Path(parent) / name, uid, uid, follow_symlinks=False)


def _digest(path):
    result = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def build_target(root, language, *, reference_binaries=(), timeout=600):
    """Build only implementation/, stop all build processes, and seal the selected ELF.

    Runtime execution restrictions are a separate step. This function never treats a
    successful compiler invocation as proof of functional correctness or non-delegation.
    """
    plan = target_plan(language)
    app = root.path / 'app'
    implementation = app / 'implementation'
    if implementation.is_symlink() or not implementation.is_dir():
        raise TargetBuildError('the target implementation directory is missing or linked')
    _validate_inputs(implementation)
    for name in (plan['entry'], plan['manifest']):
        if name and not (implementation / name).is_file():
            raise TargetBuildError('required target build input is missing: ' + name)
    compiler = shutil.which(plan['tool'])
    if plan['language'] == 'rust':
        rustup_home = Path(os.environ.get('RUSTUP_HOME', '/usr/local/rustup'))
        settings = rustup_home / 'settings.toml'
        if not settings.is_file():
            raise TargetBuildError('the image does not identify its installed Rust toolchain')
        installed = tomllib.loads(settings.read_text()).get('default_toolchain', '')
        if not installed or '/' in installed or installed in ('.', '..'):
            raise TargetBuildError('invalid installed Rust toolchain identity')
        compiler = str(rustup_home / 'toolchains' / installed / 'bin/cargo')
    if not compiler:
        raise TargetBuildError('target compiler is unavailable: ' + plan['tool'])
    compiler_info = os.stat(compiler)
    if compiler_info.st_uid != 0:
        raise TargetBuildError('target compiler is not immutable trusted runtime content')
    confined_compiler = root.path / compiler.lstrip('/')
    if not confined_compiler.exists():
        raise TargetBuildError('target compiler is absent from the confined runtime')
    confined_info = confined_compiler.stat()
    if confined_info.st_uid != 0 or confined_info.st_mode & 0o022:
        raise TargetBuildError('target compiler was not sealed in the confined runtime')

    original = root.room / 'workspace-before-target-build'
    work = root.path / '.target-build'
    sealed = root.path / '.target'
    if original.exists() or work.exists() or sealed.exists():
        raise TargetBuildError('target build directories must be fresh')
    root.stop()
    if root.execution_audit is not None or root.execution_logs:
        raise TargetBuildError('target build requires a fresh execution-audit context')
    app.rename(original)
    try:
        shutil.copytree(original / 'implementation', app, symlinks=True)
        _own(app, root.uid)
        work.mkdir(mode=0o755)
        os.chown(work, root.uid, root.uid)
        environment = {'PATH': os.environ.get('PATH', '/usr/local/bin:/usr/bin:/bin')}
        preparation = []
        if plan['language'] == 'rust':
            cargo_home = root.path / 'home/subject/.cargo'
            cargo_home.mkdir()
            os.chown(cargo_home, root.uid, root.uid)
            registry = root.path / 'usr/local/cargo/registry'
            if registry.is_dir():
                (cargo_home / 'registry').symlink_to('/usr/local/cargo/registry')
            environment.update(CARGO_HOME='/home/subject/.cargo',
                               RUSTUP_HOME=os.environ.get('RUSTUP_HOME', '/usr/local/rustup'),
                               RUSTC=str(Path(compiler).with_name('rustc')),
                               RUSTDOC=str(Path(compiler).with_name('rustdoc')),
                               LD_LIBRARY_PATH=str(Path(compiler).parent.parent / 'lib'),
                               CARGO_ENCODED_RUSTFLAGS='--sysroot\x1f' + str(Path(compiler).parent.parent)
                               + '\x1f-C\x1flink-arg=-fuse-ld=bfd',
                               RUSTC_WRAPPER='', RUSTC_WORKSPACE_WRAPPER='')
            argv = [compiler, 'build', '--offline', '--release', '--manifest-path', '/app/Cargo.toml',
                    '--target-dir', '/.target-build', '--bin', 'submission']
            output = work / 'release/submission'
        elif plan['language'] == 'go':
            environment.update(GOTOOLCHAIN='local', GOWORK='off', GOPROXY='off', GOSUMDB='off',
                               GOFLAGS='', GOENV='off', GOCACHE='/.target-build/cache',
                               GOROOT=str(Path(compiler).resolve().parent.parent), GOTELEMETRY='off')
            argv = [compiler, 'build', '-o', '/.target-build/program', '/app']
            output = work / 'program'
        else:
            sources = sorted(path for path in app.rglob('*') if path.suffix in ('.cpp', '.cc', '.cxx')
                             and not any(part in ('tests', 'test') for part in path.relative_to(app).parts))
            if not sources:
                raise TargetBuildError('the target project contains no C++ translation units')
            objects = []
            for index, source in enumerate(sorted(app.rglob('*.c'))):
                object_file = '/.target-build/c-%d.o' % index
                preparation.append([compiler, '-x', 'c', '-std=c11', '-O3', '-I/app', '-c',
                                    '/app/' + source.relative_to(app).as_posix(), '-o', object_file])
                objects.append(object_file)
            argv = [compiler, '-std=c++20', '-O3', '-pthread', '-I/app',
                    *('/app/' + path.relative_to(app).as_posix() for path in sources),
                    *objects,
                    '-o', '/.target-build/program']
            output = work / 'program'
        try:
            root.audit_execution()
            for command in preparation:
                prepared = root.run(command, cwd='/.target-build', environment=environment, timeout=timeout)
                root.stop()
                if prepared.returncode != 0:
                    raise TargetBuildError('target adapter build failed: ' + prepared.stderr[-1500:])
            completed = root.run(argv, cwd='/app' if plan['language'] == 'go' else '/.target-build',
                                 environment=environment, timeout=timeout)
        finally:
            root.stop()
        execution = root.execution_report()
        if not execution['complete'] or execution['denied']:
            raise TargetBuildError('target compiler execution audit did not complete')
        executable = str(confined_compiler.resolve()).removeprefix(str(root.path))
        if not any(event['path'] == executable for event in execution['events']):
            raise TargetBuildError('the trusted target compiler was not executed')
        if completed.returncode != 0:
            raise TargetBuildError('target build failed: ' + completed.stderr[-1500:])
        if output.is_symlink() or not output.is_file():
            raise TargetBuildError('target build did not produce a regular executable')
        with output.open('rb') as handle:
            if handle.read(4) != b'\x7fELF':
                raise TargetBuildError('target build did not produce a native ELF executable')
        digest = _digest(output)
        if any(Path(path).is_file() and _digest(Path(path)) == digest for path in reference_binaries):
            raise TargetBuildError('target output is a copied reference binary')
        sealed.mkdir(mode=0o755)
        artifact = sealed / 'program'
        shutil.copyfile(output, artifact)
        artifact.chmod(0o555)
        info = artifact.stat()
        if info.st_uid != 0 or not stat.S_ISREG(info.st_mode):
            raise TargetBuildError('target artifact could not be sealed')
        return {'language': plan['language'], 'build_argv': argv, 'sha256': digest,
                'compiler_sha256': _digest(confined_compiler),
                'build_execution': execution,
                'preparation_argv': preparation,
                'entry_argv': ['/.target/program'], 'build_exit_code': completed.returncode,
                'runtime_enforced': False}
    finally:
        root.stop()
        root.execution_audit = None
        root.execution_logs.clear()
        if app.exists():
            shutil.rmtree(app)
        original.rename(app)


def standalone_source():
    return Path(__file__).read_text()

def reference_context(tests):
    """Read trusted emitted runtime configuration; never accept candidate paths."""
    tests = Path(tests)
    declaration = tests / 'reference-runtime.json'
    if not declaration.exists():
        return str(tests / 'reference'), '/', {}
    data = json.loads(declaration.read_text())
    expected = {'root': '/reference-runtime', 'workspace': '/reference-runtime/app',
                'environment': '/reference-runtime/runtime-environment.json'}
    if data != expected:
        raise ValueError('invalid reference runtime declaration')
    base = Path(data['root'])
    workspace = Path(data['workspace'])
    config = Path(data['environment'])
    if base.is_symlink() or workspace.is_symlink() or config.is_symlink():
        raise ValueError('reference runtime paths must not be linked')
    if not (workspace / 'run.sh').is_file() or not config.is_file():
        raise RuntimeError('the verifier image does not contain the declared reference runtime')
    environment = json.loads(config.read_text())
    if not isinstance(environment, dict) or any(not isinstance(key, str) or not isinstance(value, str)
                                               for key, value in environment.items()):
        raise ValueError('invalid reference runtime environment')
    return str(workspace), str(base), environment

USE_CONFINEMENT = True
ACTIVE_ROOTS = []
PENDING_REWARD = None
ISOLATION_REPORT = None
VERIFIER_SHA256 = hashlib.sha256(open(__file__, 'rb').read()).hexdigest()
TIMING_REPORT = {}
TIMED_EXPECTATIONS = {}
CONTROL_OUTPUTS = set()
TARGET_BUILD_REPORT = None
TARGET_SCOPE = None

WORKSPACE_TOKEN = "<workspace>"

# THE ENVIRONMENT THE REFERENCE WAS OBSERVED IN, written in rather than read from this machine.
# Injected from `observe/process/runner.SUBJECT_ENV`, which is the one declaration the freeze uses
# too -- a copy here would drift, and a drift between these two is invisible: it grades a submission
# on reproducing output the reference only produced under different surroundings.
SUBJECT_ENV = {'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8', 'TZ': 'UTC', 'TERM': 'dumb', 'COLUMNS': '80', 'LINES': '24', 'NO_COLOR': '1', 'CLICOLOR': '0', 'CLICOLOR_FORCE': '0', 'FORCE_COLOR': '0', 'PYTHONIOENCODING': 'utf-8'}
INHERITED_ENV = ('PATH', 'HOME')

def digest_text(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8", "surrogateescape")).hexdigest()

def stream_digest(text, masked=()):
    lines = text.splitlines()
    kept = ["\x00" if i in set(masked) else line for i, line in enumerate(lines)]
    return digest_text("\n".join(kept)), len(lines)

def run_scenario(scenario, program, fixtures_dir, exclude, costs=None):
    root = tempfile.mkdtemp(prefix="frf-scenario-")
    workspace = os.path.join(root, "workspace")
    os.makedirs(workspace, exist_ok=True)
    os.chmod(root, 0o755)
    os.chmod(workspace, 0o755)
    out = []
    try:
        fixture = scenario.get("fixture")
        if fixture and fixtures_dir:
            extract_fixture(os.path.join(fixtures_dir, fixture), workspace)
        confined = isinstance(program, Root)
        if confined:
            for other in ACTIVE_ROOTS:
                if other is not program:
                    other.pause()
            program.stop()
            program.prepare(workspace)
            workspace = str(program.path / 'workspace')
        environment = {}
        for _name in INHERITED_ENV:
            _value = os.environ.get(_name)
            if _value:
                environment[_name] = _value
        environment.update(SUBJECT_ENV)
        environment.update(scenario.get("environment") or {})
        for step in scenario["steps"]:
            cwd = workspace_directory(workspace, step.get('cwd', '.'), program.uid if confined else None)
            args = step["argv"]
            for _token in args:
                _t = str(_token)
                if not _t or _t.startswith("-") or "/" not in _t:
                    continue
                _p = os.path.dirname(os.path.normpath(os.path.join(workspace, _t)))
                if os.path.commonpath([os.path.abspath(_p), os.path.abspath(workspace)]) ==                         os.path.abspath(workspace):
                    try:
                        workspace_directory(workspace, os.path.relpath(_p, workspace),
                                            program.uid if confined else None)
                    except OSError:
                        pass
            if args and args[0] == "{PROGRAM}":
                argv = (getattr(program, 'entry_argv', ["/app/run.sh"]) if confined else list(program)) + list(args[1:])
            else:
                joined = ' '.join(getattr(program, 'entry_argv', ["/app/run.sh"])) if confined else " ".join(program)
                argv = [str(part).replace("{PROGRAM}", joined) for part in args]
            try:
                started = time.perf_counter()
                if confined:
                    inner_cwd = '/workspace/' + os.path.relpath(cwd, workspace)
                    done = program.run(argv, cwd=inner_cwd, environment=environment,
                                       input=step.get("stdin"), timeout=300)
                else:
                    done = bounded_run(argv, cwd=cwd, env=environment,
                                       input=step.get("stdin"), timeout=300)
                if costs is not None:
                    costs.append(time.perf_counter() - started)
                code, stdout, stderr = done.returncode, done.stdout, done.stderr
            except subprocess.TimeoutExpired as exc:
                if costs is not None:
                    raise
                code, stdout, stderr = -1, exc.stdout or "", (exc.stderr or "") + "\\n[timed out]"
            except OSError as exc:
                if costs is not None:
                    raise
                code, stdout, stderr = 127, "", "could not execute: %s" % exc
            stdout = stdout.replace(workspace, WORKSPACE_TOKEN)
            stderr = stderr.replace(workspace, WORKSPACE_TOKEN)
            if confined:
                stdout = stdout.replace('/workspace', WORKSPACE_TOKEN)
                stderr = stderr.replace('/workspace', WORKSPACE_TOKEN)
            tree = "\n".join(tree_lines(workspace, exclude))
            out.append({"exit_code": code, "stdout": stdout, "stderr": stderr, "tree": tree})
        return out
    finally:
        if isinstance(program, Root):
            program.stop()
        shutil.rmtree(root, ignore_errors=True)

def time_scenario(scenario, program, fixtures_dir, exclude):
    """Command wall time including process launch, excluding fixture and observation work."""
    expected = TIMED_EXPECTATIONS.get(scenario["probe_id"])
    if not expected:
        raise ValueError("timed workload has no frozen correctness evidence")
    selected = eligible_timing_steps(scenario, expected, CONTROL_OUTPUTS)
    if not selected:
        raise ValueError("help/version/error-only or unproven workload cannot be timed")
    costs = []
    actuals = run_scenario(scenario, program, fixtures_dir, exclude, costs=costs)
    if len(actuals) != len(expected):
        raise ValueError("timed workload step count changed")
    for actual, exp in zip(actuals, expected):
        for channel in ("exit_code", "stdout", "stderr", "tree"):
            rule = exp[channel]
            if not rule.get("graded", True):
                continue
            value = str(actual[channel]) if channel == "exit_code" else actual[channel]
            digest, count = stream_digest(value, rule.get("masked") or ())
            if digest != rule["digest"] or count != rule["line_count"]:
                raise ValueError("timed workload behavior differs from frozen reference")
    return sum(costs[index] for index in selected)

def measure_speed(scenarios, timed_ids, submission_prog, reference_prog, fixtures, exclude):
    """Use the same auditable protocol as function and package tasks."""
    global TIMING_REPORT
    result = measure(
        lambda scenario: time_scenario(scenario, reference_prog, fixtures, exclude),
        lambda scenario: time_scenario(scenario, submission_prog, fixtures, exclude),
        lambda shape, i: scenarios[shape], list(timed_ids))
    TIMING_REPORT = result.to_json()
    TIMING_REPORT["cost_boundary"] = "command wall time including launch; fixture preparation excluded"
    TIMING_REPORT["input_policy"] = "fixed held-out scenarios; fresh filesystem per invocation"
    return result.speedup, result.note

def score(passed, total, speedup):
    if total == 0:
        return 0.0
    correctness = passed / total
    if correctness < 1.0:
        return 0.5 * correctness
    return 0.5 + 0.5 * speedup

def main():
    reward = os.environ.get('REWARD_PATH')
    if reward and os.path.lexists(reward):
        os.unlink(reward)
    with ExitStack() as contexts:
        try:
            status = evaluate(contexts)
        finally:
            if PENDING_REWARD is not None and TARGET_SCOPE:
                fields = PENDING_REWARD[0]
                fields['verification_scope'] = TARGET_SCOPE
                fields['target_build'] = TARGET_BUILD_REPORT
                if TARGET_BUILD_REPORT is not None:
                    reference_execution = ACTIVE_ROOTS[0].execution_report()
                    candidate_execution = ACTIVE_ROOTS[1].execution_report()
                    fields['target_execution'] = candidate_execution
                    fields['reference_execution'] = reference_execution
                    enforced = candidate_execution['complete'] and not candidate_execution['denied'] and candidate_execution['enforced']
                    TARGET_BUILD_REPORT['runtime_enforced'] = enforced
                    if not enforced or fields.get('timing_valid') and not reference_execution['complete']:
                        fields.update(reward=0.0, correct=False, timing_valid=False, speedup=0.0,
                                      note='target execution policy was violated or execution evidence is incomplete')
                        status = 1
            ACTIVE_ROOTS.clear()
    if PENDING_REWARD is not None:
        fields, path = PENDING_REWARD
        with open(path, 'w') as handle:
            json.dump(fields, handle)
    return status

def save_reward(fields, path):
    global PENDING_REWARD
    fields['isolation'] = ISOLATION_REPORT
    fields['verifier_sha256'] = VERIFIER_SHA256
    PENDING_REWARD = fields, path

def evaluate(contexts):
    global TIMED_EXPECTATIONS, CONTROL_OUTPUTS, ISOLATION_REPORT
    global TARGET_BUILD_REPORT, TARGET_SCOPE
    root = os.path.dirname(__file__)
    scenarios = {}
    for line in open(os.path.join(root, "scenarios.jsonl")):
        item = json.loads(line)
        scenarios[item["probe_id"]] = item
    expected = json.load(open(os.path.join(root, "expectations.json")))
    timed_list = json.load(open(os.path.join(root, "timed.json")))
    timing_key = os.path.join(root, "timed_expectations.json")
    if os.path.exists(timing_key):
        TIMED_EXPECTATIONS = json.load(open(timing_key))
    CONTROL_OUTPUTS = control_output_signatures(
        list(scenarios.values()), dict(expected, **TIMED_EXPECTATIONS))

    passed = total = 0
    mismatches = []
    fixtures = os.path.join(root, "fixtures")
    environment = json.load(open(os.path.join(root, "environment.json")))
    exclude = tuple(environment.get("exclude") or ())
    target = environment.get('target_language')

    reference = os.path.join(root, "reference", "run.sh")
    submission = os.path.join(os.environ.get("SUBMISSION_ROOT", "/app"), "run.sh")
    replay = target and os.path.abspath(os.path.dirname(submission)) == os.path.abspath(os.path.dirname(reference))
    reference_workspace, reference_base, reference_environment = reference_context(root)
    if reference_base != '/':
        reference = os.path.join(reference_workspace, 'run.sh')
        if replay:
            submission = reference
    if target:
        TARGET_SCOPE = 'reference-self-replay' if replay else 'target-submission'

    if not target and not os.path.exists(submission):
        reward = os.environ.get("REWARD_PATH")
        if reward:
            # BY STEP, matching the loop above: a step is one point when any channel of it is graded.
            total = sum(1 for values in expected.values() for value in values
                        if any(value[name].get('graded', True)
                               for name in ('exit_code', 'stdout', 'stderr', 'tree')
                               if name in value))
            save_reward({"reward": 0.0, "correct": False, "correctness_passed": 0,
                      "correctness_total": total, "speedup": 0.0,
                      "note": "no run.sh in the submission"}, reward)
        return 1
    if target and not USE_CONFINEMENT:
        raise RuntimeError('target-language evaluation requires confinement')

    # ONLY ROOT CAN DROP TO NOBODY, AND ONLY ROOT NEEDS TO. `setpriv --reuid` changes the user id,
    # which an unprivileged process may not do: run as `nobody` it fails with
    #
    #     setpriv: setgroups failed: Operation not permitted
    #
    # and exits 127 -- identically, on every scenario. The image already declares `USER nobody`, so
    # the isolation this wrapper exists to provide is in force before the verifier starts; asking
    # for it again is what breaks it.
    #
    # Two isolation mechanisms met and collided. Before the image dropped its user, the verifier ran
    # as root and setpriv worked. Afterwards it could not, and the effect was invisible in the
    # obvious place: stdout and the file tree still matched perfectly, because the program that
    # never ran wrote nothing and touched nothing, while exit code and stderr failed on every one of
    # 47 scenarios. In aggregate: 47 of 75 in-image refusals at precisely 50%, 19 at precisely 25%.
    if USE_CONFINEMENT:
        reference_prog = contexts.enter_context(Root(os.path.dirname(reference), uid=50002,
            runtime_base=reference_base, runtime_environment=reference_environment))
        submission_prog = contexts.enter_context(Root(os.path.dirname(submission), uid=50001,
            runtime_base=reference_base if replay else '/',
            runtime_environment=reference_environment if replay else None))
        ACTIVE_ROOTS.extend([reference_prog, submission_prog])
        ISOLATION_REPORT = verify_pair(reference_prog, submission_prog)
        if target and environment.get('reference_argv'):
            reference_prog.entry_argv = list(environment['reference_argv'])
            if replay:
                submission_prog.entry_argv = list(environment['reference_argv'])
        if target and not replay:
            try:
                known = [Path(os.path.dirname(reference)) / name for name in ('program', 'serve.bin')]
                TARGET_BUILD_REPORT = build_target(submission_prog, target, reference_binaries=known)
                submission_prog.entry_argv = TARGET_BUILD_REPORT['entry_argv']
                submission_prog.audit_execution(submission_prog.entry_argv + environment.get('target_helpers', []))
                reference_prog.audit_execution()
            except Exception as error:
                # BY STEP, matching the loop below. See the note there.
                total = sum(1 for values in expected.values() for value in values
                            if any(value[name].get('graded', True)
                                   for name in ('exit_code', 'stdout', 'stderr', 'tree')
                                   if name in value))
                reward = os.environ.get('REWARD_PATH')
                if reward:
                    save_reward({'reward': 0.0, 'correct': False, 'correctness_passed': 0,
                                 'correctness_total': total, 'speedup': 0.0,
                                 'note': 'target-language build refused: ' + str(error)[:1500]}, reward)
                return 1
    elif environment.get("isolated") and shutil.which("setpriv") and os.geteuid() == 0:
        reference_prog = ["setpriv", "--reuid", "nobody", "--regid", "nogroup", "--clear-groups", "--", reference]
        submission_prog = ["setpriv", "--reuid", "nobody", "--regid", "nogroup", "--clear-groups", "--", submission]
    else:
        reference_prog = [reference]
        submission_prog = [submission]

    # Verification never rewrites frozen expectations, even if legacy refresh flags are set.

    for pid, steps in expected.items():
        scenario = scenarios[pid]
        try:
            actuals = run_scenario(scenario, submission_prog, fixtures, exclude)
        except (subprocess.TimeoutExpired, OutputLimitExceeded) as exc:
            # BY STEP, matching the loop above: a step is one point when any channel of it is graded.
            total = sum(1 for values in expected.values() for value in values
                        if any(value[name].get('graded', True)
                               for name in ('exit_code', 'stdout', 'stderr', 'tree')
                               if name in value))
            reward = os.environ.get('REWARD_PATH')
            if reward:
                save_reward({'reward': score(passed, total, 0.0), 'correct': False,
                             'correctness_passed': passed, 'correctness_total': total,
                             'speedup': 0.0, 'note': str(exc)}, reward)
            return 1
        for index, exp in enumerate(steps):
            actual = actuals[index] if index < len(actuals) else {"exit_code": 127, "stdout": "", "stderr": "", "tree": ""}
            # ONE POINT PER STEP, EVERY GRADED CHANNEL MUST MATCH. Four channels of one step are not
            # four independent opportunities to be wrong: they are one behaviour observed four ways,
            # and for a read-only command three of them (exit 0, empty stderr, unchanged tree) are
            # the same fact repeated once per scenario. Paid per channel, a submission that does
            # nothing collected them on every step -- measured at 68% on a 105-scenario corpus, which
            # `0.5 * correctness` turns into a third of full marks for doing nothing.
            graded_here = matched_here = 0
            for channel in ("exit_code", "stdout", "stderr", "tree"):
                rule = exp[channel]
                if not rule.get("graded", True):
                    continue
                graded_here += 1
                value = str(actual[channel]) if channel == "exit_code" else actual[channel]
                actual_digest, line_count = stream_digest(value, rule.get("masked") or ())
                matches = (line_count == int(rule.get("line_count", 0)) and
                           actual_digest == rule.get("digest"))
                matched_here += bool(matches)
                if not matches and len(mismatches) < 8:
                    mismatches.append({'probe_id': pid, 'step': index, 'channel': channel,
                                       'actual': str(value)[:2000], 'actual_digest': actual_digest,
                                       'expected_digest': rule.get('digest')})
            if graded_here:
                total += 1
                passed += 1 if matched_here == graded_here else 0

    reward_path = os.environ.get("REWARD_PATH")

    if passed < total or total == 0:
        if reward_path:
            save_reward({"reward": score(passed, total, 0.0), "correct": False,
                      "correctness_passed": passed, "correctness_total": total, "speedup": 0.0,
                      "mismatches": mismatches,
                      "note": "not every graded observation matched the reference"}, reward_path)
        return 0 if passed > 0 else 1

    speedup, note = measure_speed(scenarios, timed_list, submission_prog, reference_prog, fixtures, exclude)

    if reward_path:
        save_reward({"reward": score(passed, total, speedup) if TIMING_REPORT.get("usable") else 0.0,
                  "timing": TIMING_REPORT, "timing_valid": bool(TIMING_REPORT.get("usable")), "correct": True,
                  "correctness_passed": passed, "correctness_total": total,
                  "speedup": round(speedup, 4), "note": note}, reward_path)
    return 0 if TIMING_REPORT.get("usable") else 1

if __name__ == "__main__":
    raise SystemExit(main())
