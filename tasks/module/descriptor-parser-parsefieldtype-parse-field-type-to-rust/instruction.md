# Descriptor Parser Parsefieldtype Parse Field Type to Rust

## Task Facts

* **Scale:** `module`
* **Task form:** cross-language reimplementation
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `parseFieldType`
* **Factory dispatch marker:** `serve parseFieldType`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/descriptor-parser.js`, `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, `/app/implementation/Cargo.toml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation.

Reimplement the JavaScript `parseFieldType` function from `leonardosnt/jar-string-editor` in Rust, preserving observable behavior while improving performance through the cross-language rewrite.

## Workspace

- `/app/original/descriptor-parser.js` — JavaScript reference implementation of `parseFieldType`; use it as the normative behavioral reference.
- `/app/implementation/src/main.rs` — Rust entry source.
- `/app/implementation/src/subject.rs` — Rust implementation module.
- `/app/implementation/Cargo.toml` — Rust build configuration and inputs.
- `/app/implementation` — all target implementation sources and build inputs must remain here.
- `/app/run.sh` — development JSON-lines service entry point.
- `/app/build.sh` — development build entry point.
- `/app/task-interface.json` — task interface metadata.

The harness calls the Rust product through a JSON-lines service. Each request uses `op: "run"`, `call: "entry"`, and an array of positional `args`; the entry call must accept one string argument corresponding to `parseFieldType` and return the subject result in the documented response envelope.

## Build & Test

Build the Rust implementation from `/app`:

```sh
/app/build.sh
```

This is the supplied development build command. The evaluator independently builds sources under `/app/implementation` with its trusted offline toolchain.

Run the service for a JSON-lines invocation:

```sh
/app/run.sh
```

A standalone self-check command is not supplied. Inspect `/app/original/descriptor-parser.js`, `/app/implementation/src/main.rs`, and `/app/implementation/src/subject.rs` for available checks or invocation details rather than inventing a test command.

Correctness is checked against the frozen reference behavior before performance is measured. The request/response envelope is only the harness mechanism; grading observes the result produced by `parseFieldType`.

## Constraints

**What you CAN do**

- Rewrite the implementation in Rust under `/app/implementation`.
- Modify `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, and `/app/implementation/Cargo.toml` as needed to produce the required entry point.
- Use Rust string-processing techniques, allocation reduction, slicing, scanning, and equivalent parsing logic to improve runtime performance.
- Compare the Rust result with the runnable JavaScript implementation in `/app/original/descriptor-parser.js` while developing.
- Preserve the one-positional-string calling convention and the observable result type and value for supported inputs.
- Ensure the built Rust product can service JSON-lines requests through the supplied interface without writing diagnostics into the response stream.

**What you CANNOT do**

- Do not implement the target in JavaScript or another language; the graded implementation must be Rust.
- Do not replace the graded implementation by changing `/app/run.sh` or `/app/build.sh`; the evaluator builds and executes the target sources under `/app/implementation` directly.
- Do not add dependencies that require network access; the evaluator uses an offline Rust toolchain.
- Do not reduce `parseFieldType` to a different API, change its argument convention, or expose only a benchmark-specific path.
- Do not assume malformed-input behavior must be reproduced: malformed input is excluded from the probe contract because its frozen refusal message is not portable across languages.
- The graded corpus includes semantic-prefix and boundary cases for the string parameter. For every such case, use the runnable implementation in `/app/original/descriptor-parser.js` as the normative reference for the expected outcome; do not invent outcomes or omit boundary handling.
- Do not treat the JSON request envelope, request IDs, or diagnostic-stream handling as subject behavior under test; they only provide the harness transport.

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

