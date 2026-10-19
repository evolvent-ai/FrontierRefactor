# Bits Abs Abs to Rust

## Task Facts

* **Scale:** `module`
* **Task form:** cross-language reimplementation
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `abs`
* **Factory dispatch marker:** `serve abs`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/bits.js`, `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, `/app/implementation/Cargo.toml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation.

Reimplement the JavaScript `abs` function from `gamedev-js/vmath` in Rust, preserving observable behavior while improving performance through the language change.

## Workspace

- `/app/original/bits.js` — JavaScript reference implementation for the `abs` entry point.
- `/app/implementation/src/main.rs` — Rust service entry point.
- `/app/implementation/src/subject.rs` — Rust subject implementation location for `abs`.
- `/app/implementation/Cargo.toml` — Rust build configuration.
- `/app/build.sh` — development build entry point.
- `/app/run.sh` — development JSON-lines service launcher.
- `/app/task-interface.json` — task interface metadata.

## Build & Test

Build the Rust implementation from `/app`:

```sh
./build.sh
```

This builds the development target. The evaluator builds the sources under `/app/implementation` with its trusted offline Rust toolchain.

Start the development JSON-lines service with:

```sh
./run.sh
```

The harness uses this service mechanism to invoke `abs`; it is not itself a correctness test. No project self-check command is supplied. Inspect the provided source files for available local checks.

Correctness is checked before performance is measured.

## Constraints

**What you CAN do**

- Implement the `abs` entry point in Rust under `/app/implementation`, preserving its single floating-point positional calling convention.
- Inspect `/app/original/bits.js` and the existing Rust interface code to establish the reference behavior and required Rust integration.
- Use efficient Rust floating-point operations or branch-based logic when they preserve the reference's observable results.
- Modify Rust implementation and build inputs under `/app/implementation`, including `src/main.rs`, `src/subject.rs`, and `Cargo.toml` when necessary.
- Use `/app/run.sh` during development to exercise the JSON-lines service interface.
- Treat semantic-prefix and floating-point boundary cases as graded. The runnable reference implementation in the workspace is normative for the expected behavior of those cases; compare against it rather than assuming outcomes.

**What you CANNOT do**

- Do not change the task into an in-place JavaScript optimization: this is a cross-language rewrite, and the delivered implementation must remain Rust.
- Do not change the exposed symbol or calling convention: the entry point is `abs` and accepts one `float` parameter.
- Do not rely on replacing `/app/build.sh` or `/app/run.sh` to alter the graded program; the evaluator builds and executes the Rust product under `/app/implementation` directly.
- Do not introduce behavior that differs from the JavaScript reference for the graded semantic-prefix or boundary inputs.
- Do not target malformed input behavior. Malformed input is excluded because the reference refusal message cannot be reproduced across languages.
- Do not write diagnostics to the JSON response stream when using the service interface.
- Do not add dependency-download or installation steps; the evaluator uses an offline trusted toolchain.

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

