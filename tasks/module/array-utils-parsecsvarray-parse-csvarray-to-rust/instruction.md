# Array Utils Parsecsvarray Parse Csvarray to Rust

## Task Facts

* **Scale:** `module`
* **Task form:** cross-language reimplementation
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `parseCSVArray`
* **Factory dispatch marker:** `serve parseCSVArray`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/array-utils.js`, `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, `/app/implementation/Cargo.toml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation.

Reimplement the JavaScript `parseCSVArray` function in Rust with equivalent observable behavior and improved performance through the language change.

## Workspace

- `/app/original/array-utils.js` — JavaScript reference implementation of `parseCSVArray`.
- `/app/implementation/src/main.rs` — Rust entry point that must build into the graded product.
- `/app/implementation/src/subject.rs` — Rust subject implementation location.
- `/app/implementation/Cargo.toml` — Rust package and build configuration.
- `/app/implementation` — directory containing all Rust sources and build inputs used by the evaluator.
- `/app/build.sh` — development build entry point.
- `/app/run.sh` — JSON-lines service entry point for invoking the subject.
- `/app/task-interface.json` — task interface metadata.

The preserved calling convention is one positional string argument for the `parseCSVArray` entry point. The service harness sends JSON-lines requests with `op: "run"`, `call: "entry"`, and the argument in `args`; the JSON envelope is only the invocation mechanism, not behavior under test.

## Build & Test

Build the Rust implementation from `/app`:

```sh
/app/build.sh
```

This builds the target sources under `/app/implementation` with the available offline toolchain.

For a development invocation, start the supplied JSON-lines service:

```sh
/app/run.sh
```

No dedicated self-check command is supplied. Inspect `/app/original/array-utils.js` and the implementation sources for available checks or comparison procedures. The harness runs the frozen correctness suite automatically before measuring performance.

## Constraints

**What you CAN do**

- Replace the JavaScript implementation with a Rust implementation under `/app/implementation`.
- Optimize parsing, allocation, string handling, and intermediate data structures while preserving the reference function's observable results.
- Use the existing Rust entry-point and subject structure, or adjust files within `/app/implementation` as needed for the build.
- Compare the Rust implementation with the runnable reference in `/app/original/array-utils.js` while developing.
- Keep the service integration compatible with the supplied JSON-lines invocation mechanism.

**What you CANNOT do**

- Do not implement the solution in JavaScript or another language; the graded implementation must be Rust.
- Do not change the `parseCSVArray` calling convention: it accepts one string parameter.
- Do not change observable behavior from the JavaScript reference. The graded corpus includes semantic-prefix and boundary cases, and the implementation already present in the workspace is the normative reference for the expected result of each case.
- Malformed input is excluded from the graded corpus because the reference's frozen refusal message cannot be reproduced cross-language; do not treat that exclusion as permission to diverge on graded semantic or boundary cases.
- Do not place required implementation sources or build inputs outside `/app/implementation`; the evaluator builds that directory directly.
- Do not rely on changing `/app/run.sh` or `/app/build.sh` to replace the graded Rust product.
- Do not emit diagnostics on the service response stream.
- Do not claim correctness from performance alone: correctness is checked first, and speed is measured only after the implementation passes the frozen behavioral checks.

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

