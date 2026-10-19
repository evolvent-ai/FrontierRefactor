# Asrt Wdi Zgodne to Go

## Task Facts

* **Scale:** `kernel`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `go`
* **Entry point:** `zgodne`
* **Factory dispatch marker:** `serve zgodne`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/implementation/main.go`, `/app/original/rozwiazanie1a2023.py`, `/app/implementation/subject.go`, `/app/build.sh`, `/app/implementation/go.mod`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Reimplement the Python `zgodne` function in Go for behavioral equivalence and improved performance through the cross-language rewrite.

## Workspace

- `/app/original/rozwiazanie1a2023.py` contains the runnable normative Python reference for `zgodne`.
- `/app/implementation/main.go` is the Go entry source for the delivered implementation.
- `/app/implementation/subject.go` is available for the Go subject implementation.
- `/app/implementation/go.mod` contains Go module build inputs.
- `/app/implementation` is the required location for all implementation sources and build inputs.
- `/app/build.sh` is the supplied development build entrypoint.
- `/app/run.sh` is the supplied development JSON-lines service entrypoint.
- `/app/task-interface.json` describes the harness interface.
- The entry symbol is `zgodne`, accepting one `int_array` parameter with `int64` elements in the declared range `[-1000, 1000]`.

## Build & Test

Build the Go implementation from `/app`:

```sh
/app/build.sh
```

This builds the development version of the implementation. The evaluator independently builds the sources under `/app/implementation` with its trusted offline Go toolchain.

No self-check command is supplied. Inspect the project and the runnable Python reference for available checks and use `/app/run.sh` to exercise the JSON-lines service during development.

## Constraints

**What you CAN do**

- Reimplement only the selected kernel computation exposed as `zgodne`; preserve its single-array calling convention and observable result.
- Read and execute `/app/original/rozwiazanie1a2023.py` to establish the Python reference behavior before optimizing the Go implementation.
- Place Go source files and all required build inputs under `/app/implementation`, using the existing `main.go`, `subject.go`, and `go.mod` structure where appropriate.
- Use Go-specific performance techniques appropriate to integer-array processing, including linear scans, preallocated slices when needed, and avoiding unnecessary allocations or conversions.
- Use `/app/run.sh` as the development harness mechanism for sending JSON-lines requests to the `zgodne` entry point.
- Preserve declared numeric comparison behavior for any floating-point results: `abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)`. Integer values, booleans, strings, field names, and array shapes must match exactly; infinities must match by sign and position; NaN is accepted only at matching NaN positions.
- Account for the graded semantic-prefix and boundary cases. The existing runnable implementation is the normative reference for their expected behavior, and comparing against it establishes the required results.
- Expect correctness to be checked before speed is measured.

**What you CANNOT do**

- Do not replace the task with a different API, language, or implementation location: the deliverable must be a buildable Go implementation of `zgodne` under `/app/implementation`.
- Do not change the observable behavior of the Python reference, including semantic-prefix and boundary behavior covered by the graded corpus.
- Do not rely on malformed-input behavior: malformed input is excluded because the frozen Python refusal message cannot be reproduced cross-language.
- Do not treat `/app/build.sh` or `/app/run.sh` as the graded program replacement; the evaluator builds and executes the target sources in `/app/implementation` directly.
- Do not add dependency download or installation steps; the evaluator uses a trusted offline toolchain.
- Do not write diagnostics to the JSON response stream used by the development service.

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

