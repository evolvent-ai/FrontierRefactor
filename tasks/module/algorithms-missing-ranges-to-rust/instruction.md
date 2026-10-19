# Algorithms Missing Ranges to Rust

## Task Facts

* **Scale:** `module`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `missing_ranges`
* **Factory dispatch marker:** `serve missing_ranges`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/missing_ranges.py`, `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, `/app/implementation/Cargo.toml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation.

Reimplement the Python `missing_ranges` function in Rust for better performance while preserving its observable behaviour and positional calling convention.

## Workspace

- `/app/original/missing_ranges.py`: runnable Python reference implementation that defines the normative behaviour.
- `/app/implementation/src/main.rs`: Rust service entry point and target source.
- `/app/implementation/src/subject.rs`: Rust implementation module to inspect and update.
- `/app/implementation/Cargo.toml`: Rust build configuration.
- `/app/implementation`: target source tree and all build inputs used by the evaluator.
- `/app/build.sh`: development build entry point.
- `/app/run.sh`: JSON-lines service entry point.
- `/app/task-interface.json`: task interface metadata.

The entry point is `missing_ranges`, with parameters `(int_array, int, int)`. Preserve the existing service calling convention: requests are sent to `/app/run.sh` as JSON lines, and the harness invokes the Rust subject through the `run`/`entry` operation.

## Build & Test

Build from `/app` with the supplied development command:

```sh
/app/build.sh
```

This builds the Rust implementation using the project’s configured toolchain. The evaluator independently builds sources under `/app/implementation` with its trusted offline toolchain.

Launch the supplied JSON-lines service for a local invocation:

```sh
/app/run.sh
```

No separate self-check command is supplied. Inspect the implementation and project files for any available checks; the harness automatically runs the frozen correctness suite and measures speed only after correctness passes.

The graded probe contract includes semantic-prefix and boundary cases. Use `/app/original/missing_ranges.py` as the normative reference for the result of every graded case, including its boundary behavior. Malformed input is excluded from the contract.

## Constraints

**What you CAN do**

- Rewrite the selected Python function as Rust under `/app/implementation`.
- Preserve the `missing_ranges` symbol’s three-parameter calling convention and result representation expected by the existing interface.
- Read the Python reference before changing the Rust logic, including its handling of ordering, duplicates, bounds, empty arrays, and boundary values.
- Improve runtime and allocation behavior with Rust-native iteration, sorting, range scanning, and data structures only when they preserve the reference behavior.
- Modify Rust build inputs such as `/app/implementation/Cargo.toml` only when required for the implementation and compatible with the evaluator’s offline toolchain.

**What you CANNOT do**

- Do not implement the solution in Python or leave the graded implementation dependent on the Python reference; the target must remain Rust.
- Do not change the `missing_ranges` API, parameter order, output shape, or observable error/result behavior established by the reference.
- Do not rely on network access or undeclared dependencies; the evaluator builds `/app/implementation` offline.
- Do not replace the graded implementation by modifying `/app/run.sh` or `/app/build.sh`; the evaluator builds and executes the target sources directly.
- Do not treat the JSON-lines envelope, request IDs, or diagnostic-stream rules as subject behaviour under test; use them only to call the implementation.
- Do not optimize based on invented benchmark thresholds or alter behavior for ungraded malformed inputs.
- Do not modify unrelated project files or add repository-wide work outside this module.

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

