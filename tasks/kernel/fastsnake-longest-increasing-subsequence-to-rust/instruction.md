# Fastsnake Longest Increasing Subsequence to Rust

## Task Facts

* **Scale:** `kernel`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `longest_increasing_subsequence`
* **Factory dispatch marker:** `serve longest_increasing_subsequence`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/longest_increasing_subsequence.py`, `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, `/app/implementation/Cargo.toml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Reimplement the Python `longest_increasing_subsequence` entry point in Rust to preserve its observable behavior while improving performance.

## Workspace

- `/app/original/longest_increasing_subsequence.py` — runnable normative Python reference; inspect it to establish exact semantics.
- `/app/implementation/src/main.rs` — Rust service entry source.
- `/app/implementation/src/subject.rs` — Rust subject implementation location for `longest_increasing_subsequence`.
- `/app/implementation/Cargo.toml` — Rust build configuration.
- `/app/build.sh` — development build entry point.
- `/app/run.sh` — development JSON-lines service launcher.
- `/app/task-interface.json` — task interface metadata.
- `/app/implementation` — required location for all graded Rust implementation sources and build inputs.

## Build & Test

Build the Rust implementation from `/app`:

```sh
/app/build.sh
```

Use the development launcher to start the JSON-lines service that invokes the `longest_increasing_subsequence` subject:

```sh
/app/run.sh
```

No standalone self-check command is supplied. Inspect the reference and project sources for available checks; the automatic harness checks correctness before measuring speed.

## Constraints

**What you CAN do**

- Implement or replace the Rust code under `/app/implementation`, including `src/main.rs`, `src/subject.rs`, and required Rust build inputs.
- Implement `longest_increasing_subsequence` for its single positional `int_array` parameter, whose elements are signed 64-bit integers in the declared range `[-1000, 1000]`.
- Inspect and run `/app/original/longest_increasing_subsequence.py` to determine the reference algorithm’s exact return value, comparison semantics, and edge-case behavior.
- Use an efficient Rust algorithm and data structures appropriate for longest-increasing-subsequence computation, provided all observable reference behavior is preserved.
- Use the JSON-lines launcher during development; it is the harness mechanism for calling the Rust subject.
- Preserve declared numeric comparison behavior where applicable: floating-point values use `abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)`, while integers, booleans, strings, field names, and array shapes must match exactly. Infinities must match by sign and position, and NaN is accepted only at matching NaN positions.

**What you CANNOT do**

- Do not change the task into an in-place Python optimization: this is a cross-language rewrite, and the delivered implementation must be Rust.
- Do not alter the public entry symbol: the callable subject is `longest_increasing_subsequence`.
- Do not place graded implementation code only in `/app/run.sh` or `/app/build.sh`; the evaluator builds and executes sources under `/app/implementation` directly with its trusted offline toolchain.
- Do not change observable behavior in pursuit of speed. The graded corpus includes semantic-prefix and boundary cases; the runnable workspace reference is normative for their expected behavior.
- Do not implement behavior for malformed input as a compatibility target. Malformed input is excluded because the reference’s frozen refusal message cannot be reproduced cross-language.
- Do not add dependency download or installation steps; the evaluator uses an offline toolchain.
- Do not emit diagnostics on the JSON response stream.

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

