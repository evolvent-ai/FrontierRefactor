#!/usr/bin/env python3
"""Grade a submission against expectations frozen from the reference.

Self-contained on purpose: this runs in a container holding the task and nothing else.

    correctness   every graded probe's answer must digest to what the reference reproduced
    speed         then, and only then, the submission is timed against the reference

Correctness UNLOCKS speed rather than being averaged with it. Short of complete, no amount of speed
helps; past it, there is no ceiling. A partial score is still reported, because a submission missing
three probes of sixty is worth repairing and a zero would not say so.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
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
                # WITH WHAT THE SUBJECT SAID BEFORE IT DIED. `stderr_tail` is collected a few
                # lines above precisely so that a failure can be explained, and then thrown away at
                # the one place that needed it -- so every such refusal read `subject exited without
                # a complete response` and named no cause.
                #
                # Measured over one night: 32 package emit refusals with exactly that sentence and
                # nothing else, which is the whole of what stands between this scale and its
                # twenty-five tasks.
                said = bytes(self.stderr_tail).decode('utf-8', 'replace').strip()
                raise RuntimeError('subject exited without a complete response'
                                   + (': ' + said[-600:] if said else ''))
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

"""Numerical comparison for JSON results, shared with standalone task evaluators."""
import math


def validate_numeric_policy(policy):
    if not isinstance(policy, dict) or policy.get('kind') != 'float-tolerance':
        raise ValueError('invalid numerical comparison policy')
    for key in ('rtol', 'atol'):
        value = policy.get(key)
        try:
            valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
        except OverflowError:
            valid = False
        if not valid:
            raise ValueError('numerical tolerances must be finite nonnegative numbers')
    if not isinstance(policy.get('equal_nan', True), bool):
        raise ValueError('equal_nan must be boolean')
    return policy


def compare_numeric(expected, actual, policy):
    """Floats use atol + rtol * abs(reference); structure and integer values stay exact."""
    validate_numeric_policy(policy)

    def compare(left, right, path):
        if type(left) is float:
            if type(right) not in (int, float):
                return False, path + ': floating-point value required'
            try:
                if math.isnan(left):
                    same = policy.get('equal_nan', True) and math.isnan(right)
                elif math.isinf(left):
                    same = left == right
                elif not math.isfinite(right):
                    same = False
                else:
                    allowed = policy['atol'] + policy['rtol'] * abs(left)
                    same = math.isfinite(allowed) and abs(left - right) <= allowed
            except (OverflowError, ValueError):
                same = False
            return (True, '') if same else (False, path + ': outside numerical contract')
        if type(left) is not type(right):
            return False, path + ': result type differs'
        if isinstance(left, dict):
            if left.keys() != right.keys():
                return False, path + ': result fields differ'
            pairs = ((left[key], right[key], path + '.' + str(key)) for key in left)
        elif isinstance(left, list):
            if len(left) != len(right):
                return False, path + ': result shape differs'
            pairs = ((a, b, path + '[' + str(i) + ']') for i, (a, b) in enumerate(zip(left, right)))
        else:
            return (True, '') if left == right else (False, path + ': exact result differs')
        for a, b, child in pairs:
            same, reason = compare(a, b, child)
            if not same:
                return same, reason
        return True, ''

    return compare(expected, actual, '$')


def numeric_policy_text(policy):
    validate_numeric_policy(policy)
    nan = 'NaN is accepted only at matching NaN positions.' if policy.get('equal_nan', True) else 'NaN results are not accepted.'
    return ('For each floating-point result, abs(candidate - reference) <= %.12g + %.12g * abs(reference). '
            'Integer values, booleans, strings, field names, and array shapes must match exactly. '
            'Infinities must match in sign and position. %s' % (policy['atol'], policy['rtol'], nan))


def source():
    from pathlib import Path
    return Path(__file__).read_text()

"""Trusted target-language builds inside an existing confined candidate root."""
import hashlib
import os
import shutil
import stat
# `tomllib` IS PYTHON 3.11+, AND THIS MODULE TRAVELS INTO THE DELIVERED VERIFIER. A task's image
# is whatever its language needs -- `rust:1.90-bookworm` carries python 3.9 -- so a bare import
# here makes `tests/verify.py` die on its first line, and the task is refused for a reason that has
# nothing to do with the code being graded.
#
# Measured: repo candidates refused at emit with `verifier produced no graded report:
# ModuleNotFoundError: No module named 'tomllib'`. `scales/repo.py` guards its own two uses the
# same way; this module was the one that did not.
try:
    import tomllib
except ModuleNotFoundError:                                  # pragma: no cover - old interpreters
    try:
        import tomli as tomllib                              # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None                                       # type: ignore[assignment]
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
        if tomllib is None:
            return ''                                        # no reader, so no claim about it
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
ROOTS = {}
ACTIVE_ROOT = None
PENDING_REPORT = None
ISOLATION_REPORT = None
VERIFIER_SHA256 = hashlib.sha256(open(__file__, 'rb').read()).hexdigest()
TIMING_REPORT = {}

# THE SAME INTEGER-RENDERING CEILING THE GENERATOR RAISES. A corpus may legitimately contain an
# integer wider than CPython's 4300-digit print limit -- the prompt asks for inputs large enough to
# time -- and this code has to render exactly those probes back onto the wire. Left at the default,
# a task that froze successfully would fail at grading time with
# `Exceeds the limit (4300) for integer string conversion`, which describes our interpreter rather
# than the submission.
try:
    sys.set_int_max_str_digits(200000)
except AttributeError:                                    # pragma: no cover -- Python < 3.11
    pass

CALL_TIMEOUT = 30.0

# THE FIRST CALL PAYS FOR THE IMPORT, and 30s is a budget for answering, not for starting. A package
# whose dependencies are vendored into the workspace imports them from a cold filesystem on its very
# first request -- numpy alone is tens of megabytes of extension modules -- while every later call
# is a warm round trip. Measured in the delivered image: `Command ['/app/run.sh'] timed out after
# 30.0 seconds` on a task whose freeze, in the build sandbox with a warm page cache, had answered
# every probe. Charged as `the submission stopped answering`, which is the one thing that had not
# happened.
FIRST_CALL_TIMEOUT = 180.0
TIMED_REPEATS = 200


def digest(ok, value, error):
    """The digest the factory froze with. MUST match `Observation.digest` byte for byte.

    All three fields, sorted keys, no whitespace, and the `sha256:` prefix. Every one of those is
    load-bearing and each was wrong in the first version of this file: digesting two fields instead
    of three, and dropping the prefix, produced a verifier that disagreed with every expectation it
    was given -- 0 of 57, on a package whose reference was byte-identical to the one frozen from.

    That is the duplication this file cannot avoid -- the container has no `frf` to import -- so the
    format is written out here deliberately and E7 is what keeps the two copies honest.
    """
    # Python minor versions changed the wording of this standard-library error. The operation
    # and failure class are identical, so freeze the stable semantic spelling rather than making
    # package replay depend on the interpreter used by the factory host.
    if isinstance(error, str) and error in {
            "ValueError: max() iterable argument is empty",
            "ValueError: max() arg is an empty sequence"}:
        error = "ValueError: max() arg is an empty sequence"
    if isinstance(error, str) and ("Cannot find module" in error or
                                   "module resolution failed" in error or
                                   "ERR_MODULE_NOT_FOUND" in error):
        error = "Error: module resolution failed"
    body = json.dumps({"ok": ok, "value": value, "error": error},
                      sort_keys=True, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


class Subject:
    """A subject held open across the corpus, spoken to in JSON lines."""

    def __init__(self, argv, cwd, role='candidate'):
        self.root = ROOTS.get(role)
        if self.root is not None:
            self.activate()
            command = [str(value).replace(os.path.abspath(cwd), '/app') for value in argv]
            self.proc = self.root.spawn(command, cwd='/app', environment={'PATH': os.environ.get('PATH', '')})
        else:
            self.proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         start_new_session=True)
        self.transport = PipeTransport(self.proc)
        self.next_id = 0

    def activate(self):
        global ACTIVE_ROOT
        if self.root is not None and ACTIVE_ROOT is not self.root:
            for other in ROOTS.values():
                if other is not self.root:
                    other.pause()
            self.root.resume()
            ACTIVE_ROOT = self.root

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        if self.root is not None:
            self.root.stop()
            return
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()

    def _exchange(self, payload):
        self.activate()
        budget = CALL_TIMEOUT if getattr(self, '_answered', False) else FIRST_CALL_TIMEOUT
        line = self.transport.exchange(json.dumps(payload) + "\n", timeout=budget, line=True)
        self._answered = True
        reply = json.loads(line)
        if not isinstance(reply, dict):
            raise RuntimeError("the subject returned a non-object JSON reply (%s)" %
                               type(reply).__name__)
        if reply.get("id") != payload.get("id"):
            raise RuntimeError("the submission returned a mismatched response id")
        return reply

    def call(self, args):
        self.next_id += 1
        reply = self._exchange({"id": self.next_id, "op": "run", "call": "entry", "args": args})
        return reply

    def time(self, args, repeats):
        """Seconds for `repeats` internal calls. -> (seconds, whether the subject accepted it).

        A REFUSAL IS NOT A TIMING FAILURE. The shim answers `ok: false` when the entry point raised,
        and on a subject with a guard clause that is most of its inputs -- so treating it as an error
        made every task whose held-out probes happened to be refused report "timing could not be
        completed" and silently score speedup 1.0. Refusing takes real time and is real behaviour;
        what matters is that both sides are asked the same thing and one of them is not being timed
        on a path the other never takes, which is why `accepted` travels with the number.
        """
        self.next_id += 1
        reply = self._exchange({"id": self.next_id, "op": "time", "call": "entry",
                                "args": args, "repeats": repeats})
        return float(reply.get("seconds") or 0.0), bool(reply.get("ok"))


def observed_digest(reply):
    """One reply -> the digest to compare.

    A REFUSAL IS AN ANSWER and digests as one: how a subject rejects bad input is behaviour a
    reimplementation has to reproduce, so `{"ok": false}` is compared rather than discarded.
    """
    if reply.get("ok"):
        return digest(True, reply.get("value"), "")
    return digest(False, None, reply.get("error", ""))


def matching_reply(reference, actual, policy):
    if policy and reference.get('ok') and actual.get('ok'):
        return compare_numeric(reference.get('value'), actual.get('value'), policy)[0]
    return observed_digest(reference) == observed_digest(actual)


def score(passed, total, speedup, compliant=True):
    """The published formula. Correctness unlocks speed; nothing is capped."""
    if not compliant:
        return 0.0
    if total <= 0:
        return 0.0
    correctness = passed / total
    if passed < total:
        return 0.5 * correctness
    return 0.5 + 0.5 * speedup


def main():
    global PENDING_REPORT, ACTIVE_ROOT
    with ExitStack() as contexts:
        try:
            status = evaluate(contexts)
        finally:
            ROOTS.clear()
            ACTIVE_ROOT = None
    if PENDING_REPORT is not None:
        path, fields = PENDING_REPORT
        with open(path, 'w') as handle:
            json.dump(fields, handle, indent=2)
        print(json.dumps(fields, indent=2))
    return status

def evaluate(contexts):
    global ISOLATION_REPORT
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", required=True)
    parser.add_argument("--workspace", default="/app")
    args = parser.parse_args()

    here = args.task_root
    reward_path = os.environ.get("REWARD_PATH", "/logs/verifier/reward_detail.json")
    os.makedirs(os.path.dirname(reward_path), exist_ok=True)
    if os.path.lexists(reward_path):
        os.unlink(reward_path)
    frozen = json.load(open(os.path.join(here, "expectations.json")))
    policy = frozen.get('numeric_policy')
    if policy or frozen.get('comparison') == 'envelope':
        validate_numeric_policy(policy)
    target = frozen.get('target_language')
    target_evidence = None
    target_replay = False

    def report(**fields):
        global PENDING_REPORT
        fields['isolation'] = ISOLATION_REPORT
        fields['verifier_sha256'] = VERIFIER_SHA256
        if target:
            fields['verification_scope'] = 'reference-self-replay' if target_replay else 'target-submission'
            fields['target_build'] = target_evidence
            if target_evidence is not None:
                execution = ROOTS['candidate'].execution_report()
                fields['target_execution'] = execution
                if execution['denied'] or not execution['complete']:
                    fields.update(reward=0.0, correct=False, timing_valid=False, speedup=0.0,
                                  note='target execution policy was violated or its evidence is incomplete')
                target_evidence['runtime_enforced'] = execution['enforced'] and execution['complete'] and not execution['denied']
                if fields.get('timing_valid'):
                    reference_execution = ROOTS['reference'].execution_report()
                    fields['reference_execution'] = reference_execution
                    if not reference_execution['complete']:
                        fields.update(reward=0.0, timing_valid=False, speedup=0.0,
                                      note='reference execution audit did not complete')
        PENDING_REPORT = (reward_path, fields)
        return 0 if fields.get("reward", 0) > 0 else 1

    # ABSOLUTE. `Popen` resolves argv[0] against the process's cwd, not against the `cwd` it is
    # given, so a relative path plus `cwd=` looks the path up twice and finds nothing -- reported as
    # "no such file" for a file that is plainly there.
    workspace = os.path.abspath(args.workspace)
    submission = [os.path.join(workspace, "run.sh")]
    reference = [os.path.join(os.path.abspath(here), "reference", "run.sh")]
    target_replay = target and workspace == os.path.dirname(reference[0])
    reference_workspace, reference_base, reference_environment = reference_context(here)
    if reference_base != '/':
        reference = [os.path.join(reference_workspace, 'run.sh')]
        if target_replay:
            workspace = reference_workspace
            submission = list(reference)
            args.workspace = workspace
    if not target and not os.path.exists(submission[0]):
        return report(reward=0.0, correct=False, correctness_passed=0,
                      correctness_total=sum(not item.get('dropped') for item in frozen['graded']), speedup=0.0,
                      note="no run.sh in the workspace, so there is nothing to grade")

    if target and not USE_CONFINEMENT:
        return report(reward=0.0, correct=False, correctness_passed=0,
                      correctness_total=sum(not item.get('dropped') for item in frozen['graded']),
                      speedup=0.0, note='target-language evaluation requires confinement')
    if USE_CONFINEMENT:
        ROOTS['candidate'] = contexts.enter_context(Root(workspace, uid=50001,
            runtime_base=reference_base if target_replay else '/',
            runtime_environment=reference_environment if target_replay else None))
        reference_dir = os.path.dirname(reference[0])
        ROOTS['reference'] = contexts.enter_context(Root(reference_dir, uid=50002,
            runtime_base=reference_base, runtime_environment=reference_environment))
        ISOLATION_REPORT = verify_pair(ROOTS['reference'], ROOTS['candidate'])
        if target and not target_replay:
            try:
                known = [Path(reference_dir) / name for name in ('program', 'serve.bin')]
                target_evidence = build_target(ROOTS['candidate'], target, reference_binaries=known)
                ROOTS['candidate'].audit_execution(target_evidence['entry_argv'] + frozen.get('target_helpers', []))
                ROOTS['reference'].audit_execution()
                submission = target_evidence['entry_argv']
            except Exception as error:
                return report(reward=0.0, correct=False, correctness_passed=0,
                              correctness_total=sum(not item.get('dropped') for item in frozen['graded']),
                              speedup=0.0, note='target-language build refused: ' + str(error)[:1500])
    # The task writer may have left a package reference tree in tests/reference. E7 must drive
    # exactly the emitted reference and report its real stderr; it must never silently substitute
    # the factory workspace.
    passed = 0
    total = sum(not item.get('dropped') for item in frozen['graded'])
    mismatches = []
    note = ""
    try:
        reference_values = {}
        if policy:
            with Subject(reference, cwd=os.path.dirname(reference[0]), role='reference') as baseline:
                for expectation in frozen['graded']:
                    if expectation.get('dropped'):
                        continue
                    pid = expectation['probe_id']
                    reply = baseline.call(frozen['probes'][pid])
                    if observed_digest(reply) != expectation['digest']:
                        return report(reward=0.0, correct=False, correctness_passed=0,
                                      correctness_total=total, speedup=0.0,
                                      note='reference no longer matches the frozen numerical baseline')
                    reference_values[pid] = reply
        with Subject(submission, cwd=workspace) as subject:
            for expectation in frozen["graded"]:
                if expectation.get("dropped"):
                    continue
                probe = frozen["probes"][expectation["probe_id"]]
                try:
                    reply = subject.call(probe)
                    same = (matching_reply(reference_values[expectation['probe_id']], reply, policy)
                            if policy else observed_digest(reply) == expectation['digest'])
                    if same:
                        passed += 1
                    else:
                        mismatches.append(expectation["probe_id"])
                except Exception as exc:
                    note = "the submission stopped answering: %s" % exc
                    break
    except Exception as exc:
        return report(reward=0.0, correct=False, correctness_passed=0, correctness_total=total,
                      speedup=0.0, note="the submission would not start: %s" % exc)

    if passed < total or total == 0:
        return report(reward=score(passed, total, 0.0), correct=False,
                      correctness_passed=passed, correctness_total=total, speedup=0.0,
                      note=note or "not every graded probe matched the reference: %s" %
                           ", ".join(mismatches[:8]))

    # TIMED ONLY ONCE CORRECT, and on inputs held out of grading, so that a submission cannot
    # answer them during the correctness pass and replay a cache when the clock starts.
    speedup, note = measure_speed(frozen, submission, reference, args, here)
    return report(reward=score(passed, total, speedup) if TIMING_REPORT.get("usable") else 0.0,
                  timing=TIMING_REPORT, timing_valid=bool(TIMING_REPORT.get("usable")), correct=True,
                  correctness_passed=passed, correctness_total=total,
                  speedup=round(speedup, 4), note=note)


def measure_speed(frozen, submission, reference, args, here):
    """-> (speedup, a note saying how it was arrived at).

    Paired and alternated: reference and submission are timed one after the other on the same
    input, so that a machine that slows down half way through slows both. A difference smaller than
    the reference's own run-to-run spread is reported as no change rather than as a small win.
    """
    global TIMING_REPORT
    TIMING_REPORT = {"usable": False, "protocol": PROTOCOL_VERSION}
    timed = frozen.get("timed") or []
    if not timed:
        return 0.0, "no workload was held out for timing, so speed was not measured"

    reference_dir = os.path.dirname(reference[0])
    if not os.path.exists(reference[0]):
        return 0.0, "the package ships no reference to time against"

    try:
        with Subject(submission, cwd=args.workspace) as mine, \
             Subject(reference, cwd=reference_dir, role='reference') as ref:
            expected = {}
            policy = frozen.get('numeric_policy')
            for probe_id in timed:
                probe = frozen["probes"][probe_id]
                expected[probe_id] = ref.call(probe)
                frozen_digest = frozen.get('timed_expectations', {}).get(probe_id)
                if frozen_digest and observed_digest(expected[probe_id]) != frozen_digest:
                    return 0.0, 'timed reference no longer matches its frozen baseline'
                if not matching_reply(expected[probe_id], mine.call(probe), policy):
                    return 0.0, "held-out workload behavior differs from the reference"
            def cost(subject, probe_id):
                seconds = 0.0
                for _ in range(TIMED_REPEATS):
                    subject.activate()
                    started = time.perf_counter()
                    reply = subject.call(frozen["probes"][probe_id])
                    seconds += time.perf_counter() - started
                    if not matching_reply(expected[probe_id], reply, policy):
                        raise ValueError("timed response differs from reference")
                return seconds
            result = measure(lambda pid: cost(ref, pid), lambda pid: cost(mine, pid),
                             lambda shape, i: shape, timed)
            TIMING_REPORT = result.to_json()
            TIMING_REPORT["input_policy"] = "fixed held-out inputs; repeated calls in persistent process"
            TIMING_REPORT["cost_boundary"] = "evaluator wall clock; JSON transport included; comparison checks excluded"
            TIMING_REPORT["repeats"] = TIMED_REPEATS
            return result.speedup, result.note
    except Exception as exc:
        return 0.0, "timing could not be completed: %s" % exc


if __name__ == "__main__":
    sys.exit(main())
