# Cirq Highlight to Rust

## Task Facts

* **Scale:** `module`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `highlight`
* **Factory dispatch marker:** `serve highlight`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/shell_tools.py`, `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, `/app/implementation/Cargo.toml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation.

Reimplement the Python `highlight` function in Rust for equivalent observable behavior, preserving its calling convention while improving performance through the cross-language rewrite.

## Workspace

- `/app/original/shell_tools.py`: runnable Python reference implementation for establishing expected behavior.
- `/app/implementation/src/main.rs`: Rust entry point to implement and expose.
- `/app/implementation/src/subject.rs`: Rust subject implementation.
- `/app/implementation/Cargo.toml`: Rust build configuration and inputs.
- `/app/implementation`: target-language source tree and all build inputs used by the evaluator.
- `/app/build.sh`: development build entry point.
- `/app/run.sh`: JSON-lines service entry point used to call the subject.
- `/app/task-interface.json`: task interface metadata.

The entry symbol is `highlight`. It accepts three positional parameters: a string, an integer, and a boolean. Preserve this positional calling convention through the service interface.

The JSON-lines service sends requests with `id`, `op: "run"`, `call: "entry"`, and positional `args`; it returns the subject result while preserving the request `id`. This envelope is only the harness calling mechanism. The graded behavior is the result produced by `highlight`.

## Build & Test

Build the Rust implementation from `/app`:

```sh
/app/build.sh
```

This builds the target sources under `/app/implementation` using the available trusted offline toolchain.

Run the development service from `/app`:

```sh
/app/run.sh
```

This starts the JSON-lines interface used to invoke the implementation. No separate self-check command is supplied; inspect the implementation and reference source for available project-native checks. The evaluator automatically checks correctness first against the frozen corpus, then measures speed only after correctness passes.

## Constraints

**What you CAN do**

- Replace or refactor the implementation under `/app/implementation` while keeping the solution in Rust.
- Use Rust string handling and allocation strategies appropriate for wrapping a string with terminal color codes.
- Compare the Rust result with the runnable Python reference in `/app/original/shell_tools.py` while developing.
- Optimize formatting, conversion, and allocation paths after matching the reference behavior.
- Keep build inputs self-contained under `/app/implementation` for the evaluator's offline build.

**What you CANNOT do**

- Do not implement the task in Python or another language; the delivered subject must be Rust and buildable by the evaluator.
- Do not change the `highlight` calling convention or omit support for its string, integer, and boolean parameters.
- Do not assume behavior for semantic prefix or boundary cases. These cases are graded, and the existing runnable implementation is the normative reference for their expected results.
- Malformed input is excluded from the graded contract because its frozen refusal message cannot be reproduced across languages.
- Do not treat the JSON request/response envelope or diagnostic handling as the behavior being tested.
- Do not rely on dependency downloads or external runtime services; the evaluator builds `/app/implementation` with its trusted offline toolchain.
- Do not replace the required Rust implementation with changes to `/app/run.sh` or `/app/build.sh`; those are development entry points, while the evaluator builds and executes the target product directly.

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

