# Textics Textics Textics to Rust

## Task Facts

* **Scale:** `module`
* **Task form:** cross-language reimplementation
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `textics`
* **Factory dispatch marker:** `serve textics`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/textics.js`, `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, `/app/implementation/Cargo.toml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation.

Reimplement the JavaScript `textics` function from `/app/original/textics.js` in Rust, preserving its observable behaviour while improving performance through the cross-language rewrite.

## Workspace

- `/app/original/textics.js` — JavaScript reference implementation of `textics`; use it as the normative behavioural reference.
- `/app/implementation/src/main.rs` — Rust implementation entry source.
- `/app/implementation/src/subject.rs` — Rust subject implementation source.
- `/app/implementation/Cargo.toml` — Rust build configuration.
- `/app/implementation/` — directory containing the Rust implementation and all build inputs that must be delivered.
- `/app/run.sh` — development JSON-lines service entrypoint.
- `/app/build.sh` — development build entrypoint.
- `/app/task-interface.json` — task interface metadata.

The entry point is `textics`. It accepts one positional argument of kind `string`; preserve that calling convention.

## Build & Test

Build the Rust implementation from `/app`:

```sh
/app/build.sh
```

This checks the development build using the workspace's configured toolchain. The evaluator separately builds the sources under `/app/implementation` with its trusted offline toolchain and executes the resulting product directly.

For a development invocation, `/app/run.sh` provides the JSON-lines service interface:

```sh
/app/run.sh
```

Requests use the supplied interface with `op="run"`, `call="entry"`, and positional arguments in `args`. The JSON envelope is only the harness mechanism; correctness is determined from the returned subject value, not from the envelope itself. No project-native self-check command is supplied; inspect the reference and implementation sources for available checks rather than inventing one.

The harness checks correctness first and measures execution speed only after the implementation passes the behavioural checks. The graded corpus includes semantic-prefix and boundary cases for the string parameter. Malformed input is excluded. For every graded case, `/app/original/textics.js` is the normative reference: it is runnable and should be used to establish the expected result without assuming outcomes.

## Constraints

**What you CAN do**

- Replace or extend the Rust sources under `/app/implementation`.
- Optimize parsing, iteration, allocation, and string handling while preserving the reference function's observable results.
- Use Rust's standard string and byte-processing facilities and the existing Cargo configuration.
- Add build inputs under `/app/implementation` when required by the implementation.
- Compare the Rust implementation with `/app/original/textics.js` across semantic-prefix and boundary inputs during development.

**What you CANNOT do**

- Do not implement the target in JavaScript or another language; the delivered implementation must remain Rust.
- Do not change the `textics` entry point or its single-string calling convention.
- Do not replace the graded Rust product with changes only to `/app/run.sh` or `/app/build.sh`; the evaluator builds and executes the sources under `/app/implementation` directly.
- Do not depend on network access or unavailable packages; the evaluator uses a trusted offline toolchain.
- Do not treat the JSON-lines request/response envelope as subject behaviour or add diagnostics to the response stream.
- Do not invent results for malformed inputs; those inputs are outside the graded contract.
- Do not sacrifice behavioural equivalence for speed, including on semantic-prefix and boundary cases.

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

