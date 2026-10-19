# Texo Compute Stats to Rust

## Task Facts

* **Scale:** `module`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `compute_stats`
* **Factory dispatch marker:** `serve compute_stats`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/stats.py`, `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, `/app/implementation/Cargo.toml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation.

Reimplement `compute_stats` from the Python reference as a Rust module with equivalent observable results and improved performance.

## Workspace

- `/app/original/stats.py` — runnable Python reference for `compute_stats`; use it as the normative source for expected behavior.
- `/app/implementation/src/main.rs` — Rust entry point built by the evaluator.
- `/app/implementation/src/subject.rs` — Rust implementation source available for the task.
- `/app/implementation/Cargo.toml` — Rust build configuration.
- `/app/run.sh` — development entry point for the JSON-lines service.
- `/app/build.sh` — development build entry point.
- `/app/task-interface.json` — task interface metadata.
- `/app/implementation/` — directory containing all Rust implementation sources and build inputs that the evaluator builds.

## Build & Test

Build the Rust implementation from `/app`:

```sh
/app/build.sh
```

Start the development JSON-lines service:

```sh
/app/run.sh
```

The service accepts harness requests containing `id`, `op`, `call`, and positional `args`; the harness uses this envelope to invoke the `compute_stats` entry point. Its response envelope is transport plumbing, not behavior under test. No dedicated self-check command is supplied; inspect `/app/original/stats.py` and the existing project sources for available checks rather than inventing one.

Correctness is checked before performance is measured. The graded corpus covers the semantic prefix and boundary cases named by the probe contract. Compare the Rust results with the runnable reference in `/app/original/stats.py` to establish the expected behavior for those cases. Malformed input is excluded from the graded contract.

## Constraints

**What you CAN do**

- Replace or improve the Rust code under `/app/implementation`, including `src/main.rs`, `src/subject.rs`, and build inputs under that directory.
- Use Rust-native performance techniques such as single-pass iteration, avoiding unnecessary allocations, and appropriate standard-library collection or numeric operations.
- Preserve the function's positional calling convention: `compute_stats` receives one list whose elements are strings.
- Inspect and compare against `/app/original/stats.py` to reproduce its computation and observable results.

**What you CANNOT do**

- Do not implement the solution in Python or another language; the graded implementation must remain Rust.
- Do not change the required `compute_stats` behavior, calling convention, or result structure.
- Do not rely on modifying `/app/run.sh` or `/app/build.sh` to replace the graded product; the evaluator builds sources directly from `/app/implementation` with its trusted offline toolchain.
- Do not add dependencies that require downloading packages during the offline evaluator build.
- Do not write diagnostics to the JSON-lines response stream.
- Do not infer behavior for malformed inputs beyond the stated exclusion; reproduce the reference behavior for the graded semantic-prefix and boundary cases instead.

## Submission Contract

The submission artifact is the entire `/app` directory. Keep the implementation and everything
needed to run it in that directory for collection by the harness.

Correctness is measured first: each graded observation must match the reference's frozen output.
Speed is measured only after every observation matches.

```
score = 0.5 + 0.5 * speedup    if all observations match
score = 0.5 * (fraction matched) otherwise
```

Partial correctness is scored, so a submission that misses a few observations is worth repairing
rather than abandoning.

## Time Budget

The harness enforces the agent time limit configured for this task. Keep your changes saved in
`/app` before the run ends. Do not assume a timer file or daemon is installed.

## Behavioral Rules

* Do not read anything under `tests/`. That directory holds the verifier, the expectations, and a
  runnable reference implementation. Reading it and replaying what you find scores full marks while
  implementing nothing; the directory is in a separate environment that your submission cannot reach.
* Do not call, import, link against, or shell out to the reference implementation. Your submission
  is inspected for this before it is run, and a match scores zero without being graded or timed.
* Everything runs offline. No outbound network access is available.

## Grading Signals

We run **57 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **the value the call returned**

That is **57 graded observation(s)** in total.

These expectations were not written by hand. The reference was run 5 times per probe and only what it reproduced *every single time* is graded -- anything it could not repeat, such as a timestamp or a temporary path, is excluded. You are never asked to reproduce something that is not reproducible.


## Performance Measurement

```
score = 0.5 + 0.5 x speedup      if every observation matches
score = 0.5 x (fraction matched)  otherwise
```

Correctness **unlocks** speed rather than being averaged with it: short of complete, no amount of speed helps. Partial correctness is still scored, so a submission that misses a few observations is worth repairing rather than abandoning.

Once every graded observation matches, and only then, your submission is timed against the reference on 3 workload(s) held out from grading. Your score rises with the measured speedup; there is no threshold to clear and no ceiling above which more speed stops counting. A difference too small to distinguish from the machine's own noise counts as no change.

## Interface

The program is a JSON-lines service. Read one JSON object per line from standard input and produce one JSON object per line on standard output. Each request contains an `id` and an `args` array; preserve the id in the matching response. A successful response has `{\"id\": id, \"ok\": true, \"value\": result}`; a failed call has `{\"id\": id, \"ok\": false, \"error\": message}`. The reference artifact shows the selected symbol's argument order and result shape.

