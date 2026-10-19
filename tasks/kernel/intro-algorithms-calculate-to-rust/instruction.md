# Intro Algorithms Calculate to Rust

## Task Facts

* **Scale:** `kernel`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `calculate`
* **Factory dispatch marker:** `serve calculate`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/final_task_nearest_zero.py`, `/app/implementation/src/main.rs`, `/app/implementation/src/subject.rs`, `/app/implementation/Cargo.toml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Reimplement the Python `calculate` computation from `rezi100r/intro_algorithms` in Rust for equivalent observable results and improved performance.

## Workspace

- `/app/original/final_task_nearest_zero.py`: runnable Python reference implementation that defines the expected behavior of `calculate`.
- `/app/implementation/src/main.rs`: Rust entry source and service integration point.
- `/app/implementation/src/subject.rs`: Rust subject implementation area.
- `/app/implementation/Cargo.toml`: Rust build configuration.
- `/app/implementation`: target-language source tree and all build inputs used by the evaluator.
- `/app/run.sh`: development JSON-lines service entrypoint.
- `/app/build.sh`: development build entrypoint.
- `/app/task-interface.json`: task interface metadata.

The entry point is `calculate`, with positional parameters of type `int_array` and `int`. The service receives requests as JSON lines and dispatches the `calculate` call through the `entry` operation.

## Build & Test

Build the Rust implementation from `/app`:

```sh
/app/build.sh
```

Run the development service from `/app` for a manual invocation or source-level check:

```sh
/app/run.sh
```

The service reads JSON-lines requests and returns JSON-lines responses. No self-check command is supplied in the task context; inspect the implementation and project files for available checks. The evaluator builds `/app/implementation` with its trusted offline Rust toolchain and executes that product directly.

Correctness is checked before performance is measured. The graded corpus includes semantic-prefix and boundary cases. The runnable reference at `/app/original/final_task_nearest_zero.py` is normative for the expected result of each graded case; compare the Rust behavior against it rather than assuming outcomes. Malformed-input behavior is excluded from the contract.

## Constraints

**What you CAN do**

- Rewrite the implementation in Rust while preserving the `calculate` calling convention and observable results.
- Optimize the selected calculation using Rust’s typed integer operations, slices, iterators, and allocation-free or low-allocation logic where appropriate.
- Modify Rust sources and build inputs under `/app/implementation`.
- Keep the implementation compatible with the supplied offline toolchain and existing Cargo configuration.
- Use `/app/run.sh` for development checks through its JSON-lines service interface.

**What you CANNOT do**

- Do not implement the target in Python or another language; this is a cross-language rewrite and the delivered implementation must be Rust.
- Do not change the `calculate` entry point or its two positional parameter kinds: `int_array` and `int`.
- Do not rely on modifying `/app/run.sh` or `/app/build.sh` to replace the graded product; the evaluator builds and executes `/app/implementation` directly.
- Do not add dependencies that require network access or are unavailable to the trusted offline toolchain.
- Do not alter behavior for the graded semantic-prefix or boundary cases relative to the runnable Python reference.
- Match integer values, booleans, strings, field names, and array shapes exactly.
- For floating-point results, satisfy `abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)` using float64 precision; do not require bitwise equality.
- Preserve infinity sign and position. NaN is accepted only at positions where the reference also produces NaN.

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

