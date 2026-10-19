# Find Normalizequery Normalize Query to Rust

## Task Facts

* **Scale:** `module`
* **Task form:** cross-language reimplementation
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `normalizeQuery`
* **Factory dispatch marker:** `serve normalizeQuery`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/find.js`, `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, `/app/implementation/Cargo.toml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation.

Reimplement the JavaScript `normalizeQuery` function from `/app/original/find.js` in Rust with equivalent observable behavior and improved performance.

## Workspace

- `/app/original/find.js` — runnable JavaScript reference implementation of `normalizeQuery`; use it as the normative source for expected results.
- `/app/implementation/src/main.rs` — Rust entry source and required implementation location.
- `/app/implementation/src/subject.rs` — existing Rust subject source that may contain implementation scaffolding.
- `/app/implementation/Cargo.toml` — Rust build configuration.
- `/app/implementation` — directory containing all Rust sources and build inputs consumed by the evaluator.
- `/app/build.sh` — development build entry point.
- `/app/run.sh` — development JSON-lines service entry point.
- `/app/task-interface.json` — task interface metadata.

## Build & Test

Build the Rust implementation from `/app`:

```sh
/app/build.sh
```

Run the development service:

```sh
/app/run.sh
```

The service accepts JSON-lines requests using the supplied harness interface; the envelope is only the mechanism used to call the subject, not behavior under test. No dedicated self-check command is supplied. Inspect the reference and project sources for available checks rather than inventing a test command. The harness checks correctness first and measures speed only after the implementation passes correctness checks.

## Constraints

**What you CAN do**

- Replace or extend the Rust implementation under `/app/implementation`.
- Optimize parsing, string handling, allocation, and control flow while preserving the reference function’s observable results.
- Use Rust’s standard library and the existing offline toolchain available to the evaluator.
- Preserve the `normalizeQuery` entry point and its single string parameter.
- Compare the Rust implementation with the runnable JavaScript reference in `/app/original/find.js` while developing.
- Handle the graded semantic-prefix and boundary cases according to the reference implementation.

**What you CANNOT do**

- Do not implement the solution in JavaScript or another language; this is a cross-language rewrite and the deliverable must remain Rust.
- Do not change the required calling convention: `normalizeQuery` receives one string argument through the service’s positional `args` array.
- Do not replace the graded Rust product by modifying `/app/run.sh` or `/app/build.sh`; the evaluator builds sources under `/app/implementation` directly.
- Do not add diagnostics to the JSON-lines response stream.
- Do not assume malformed-input behavior is graded or attempt to reproduce a frozen refusal message; malformed input is excluded by the task contract.
- Do not alter the request/response envelope to encode subject behavior; preserve the harness interface so the evaluator can invoke the implementation.
- Do not add dependency installation or network-dependent build steps; the evaluator uses a trusted offline toolchain.

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

