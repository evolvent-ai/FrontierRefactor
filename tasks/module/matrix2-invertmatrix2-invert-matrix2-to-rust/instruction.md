# Matrix2 Invertmatrix2 Invert Matrix2 to Rust

## Task Facts

* **Scale:** `module`
* **Task form:** cross-language reimplementation
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `invertMatrix2`
* **Factory dispatch marker:** `serve invertMatrix2`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/matrix2.js`, `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, `/app/implementation/Cargo.toml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation.

Reimplement the JavaScript `invertMatrix2` function from `rabbit-ear/rabbit-ear` in Rust, preserving its observable behavior and calling convention while improving performance through the language change.

## Workspace

- `/app/original/matrix2.js`: JavaScript reference containing `invertMatrix2`.
- `/app/implementation/src/main.rs`: Rust entry point and JSON-lines service integration.
- `/app/implementation/src/subject.rs`: Rust subject implementation.
- `/app/implementation/Cargo.toml`: Rust build configuration and inputs.
- `/app/implementation`: Target source tree built directly by the evaluator.
- `/app/run.sh`: Development entry point for the JSON-lines service.
- `/app/build.sh`: Development build entry point.
- `/app/task-interface.json`: Task interface metadata.

## Build & Test

Build the Rust implementation from `/app`:

```sh
/app/build.sh
```

This builds the implementation using the development build entry point. The evaluator independently builds the sources under `/app/implementation` with its trusted offline Rust toolchain.

Run the service from `/app` when inspecting or exercising the implementation:

```sh
/app/run.sh
```

The service accepts JSON-lines requests using the supplied interface, with `op` set to `"run"`, `call` set to `"entry"`, and positional arguments in `args`. The envelope is only the harness mechanism for invoking the subject; the graded behavior is the result produced by `invertMatrix2`.

No additional self-check command is supplied. Inspect the project and reference source for available checks rather than assuming an executable test command exists.

Correctness is checked against the frozen JavaScript behavior before performance is measured. The graded probe contract includes semantic-prefix and boundary cases. The runnable implementation already present in the workspace is the normative reference for those cases; compare the Rust results with it to establish expected behavior. Malformed input is excluded from the contract.

## Constraints

**What you CAN do**

- Implement `invertMatrix2` in Rust under `/app/implementation`, using `/app/original/matrix2.js` as the behavioral reference.
- Preserve the module-level calling convention: one positional floating-point array argument, represented by the JSON-lines interface as an element of `args`.
- Use Rust numeric and collection techniques that reduce allocation and copying while preserving the reference behavior.
- Keep the implementation compatible with the trusted offline toolchain and the existing Rust project configuration.
- Update the Rust entry point and supporting implementation files as needed so the evaluator can build and invoke the `invertMatrix2` entry point directly.
- Use `/app/run.sh` and the supplied JSON-lines interface to compare observable Rust results with the JavaScript reference during development.

**What you CANNOT do**

- Do not implement the solution in JavaScript or another language; the target implementation must remain Rust.
- Do not change the observable behavior of `invertMatrix2`, including behavior covered by semantic-prefix and boundary cases.
- Do not replace the target implementation with changes only to `/app/run.sh` or `/app/build.sh`; the evaluator builds and executes sources under `/app/implementation` directly.
- Do not assume malformed-input behavior is graded or attempt to reproduce a frozen refusal message for malformed input.
- Do not add dependency installation or network-dependent build steps; the build environment is offline.
- Do not alter the JSON-lines envelope as a substitute for implementing the subject behavior. IDs and response objects support harness invocation and are not themselves the behavior under test.
- Do not emit diagnostics into the service response stream.

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

