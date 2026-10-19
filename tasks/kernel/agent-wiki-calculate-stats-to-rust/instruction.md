# Agent Wiki Calculate Stats to Rust

## Task Facts

* **Scale:** `kernel`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `calculate_stats`
* **Factory dispatch marker:** `serve calculate_stats`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/aggregate_benchmark.py`, `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, `/app/implementation/Cargo.toml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Rewrite the `calculate_stats` computation from Python in Rust, preserving its observable behavior while improving performance through the cross-language implementation.

## Workspace

- `/app/implementation/src/main.rs`: Rust entry source and service integration point.
- `/app/implementation/src/subject.rs`: Rust subject implementation location.
- `/app/implementation/Cargo.toml`: Rust build configuration and inputs.
- `/app/original/aggregate_benchmark.py`: Original Python reference implementation; use it to establish the required calculation and behavior.
- `/app/build.sh`: Development build entrypoint.
- `/app/run.sh`: Development JSON-lines service entrypoint.
- `/app/task-interface.json`: Task interface metadata.

## Build & Test

Build the Rust implementation with:

```sh
/app/build.sh
```

The evaluator builds the sources under `/app/implementation` with its trusted offline toolchain and executes the resulting product directly. No self-check command is supplied; inspect the project and reference source for available checks. The development service is available through `/app/run.sh`, but the harness invokes the `calculate_stats` entry point through its JSON-lines calling interface.

Correctness is checked before performance is measured. The graded corpus includes semantic-prefix and boundary cases. The runnable implementation already present in the workspace is the normative reference for those cases; compare the Rust behavior against it to establish expected results. Malformed-input behavior is excluded from the graded contract.

## Constraints

**What you CAN do**

- Reimplement the `calculate_stats` entry point in Rust under `/app/implementation`.
- Optimize the mean, standard deviation, minimum, and maximum calculation using Rust-native data traversal and appropriate `f64` operations.
- Inspect `/app/original/aggregate_benchmark.py` and the existing implementation to reproduce the reference algorithm and edge-case behavior.
- Keep the implementation compatible with the trusted offline Rust toolchain and use only build inputs available under `/app/implementation`.
- Preserve the positional argument calling convention: one `float_array` parameter containing float64 values.
- Preserve the result's field names, structure, array shapes, integer values, booleans, and strings exactly.
- Return floating-point results within `1e-12 + 1e-09 * abs(reference)` of the reference result.
- Preserve matching NaN positions and the sign and position of infinities.

**What you CANNOT do**

- Do not implement the solution in Python or another language; the graded implementation must remain Rust.
- Do not change the `calculate_stats` entry point, its positional calling convention, or the subject result format.
- Do not rely on replacing `/app/run.sh` or `/app/build.sh` to substitute for the graded implementation; the evaluator builds `/app/implementation` directly.
- Do not assume malformed-input behavior is graded or add a cross-language refusal contract for it.
- Do not require bitwise equality for floating-point results; use the supplied tolerance policy while preserving NaN and infinity behavior.
- Do not write diagnostics into the JSON-lines response stream used to call the subject.

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

