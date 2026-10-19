# Permutation From Factorial Base to Go

## Task Facts

* **Scale:** `kernel`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `go`
* **Entry point:** `from_factorial_base`
* **Factory dispatch marker:** `serve from_factorial_base`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/implementation/main.go`, `/app/original/__init__.py`, `/app/implementation/subject.go`, `/app/build.sh`, `/app/implementation/go.mod`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Reimplement the Python `from_factorial_base` entry point in Go as a cross-language performance rewrite while preserving its observable behavior.

## Workspace

- `/app/implementation/main.go` is the supplied Go entry-point source.
- `/app/implementation/subject.go` contains the Go implementation area for `from_factorial_base`.
- `/app/implementation/go.mod` defines the Go module build inputs.
- `/app/original/__init__.py` contains the original Python reference.
- `/app/build.sh` is the development build entry point.
- `/app/run.sh` launches the JSON-lines service used to call the subject during development.
- `/app/task-interface.json` describes the task interface.
- The graded implementation and all required build inputs must remain under `/app/implementation`.

## Build & Test

Build the Go implementation from `/app`:

```sh
/app/build.sh
```

This builds the development version of the target implementation. No project-native self-check command is supplied; inspect the available source and interface files for any applicable local checks.

Correctness is checked before performance is measured. Performance is evaluated only after the Go implementation matches the reference behavior.

## Constraints

**What you CAN do**

- Implement and optimize only the `from_factorial_base` computation in Go.
- Accept the required `int_array` positional parameter, whose elements are `int64` values in the declared range `[-1000, 1000]`.
- Use Go data structures and algorithms appropriate for efficient permutation reconstruction, while preserving the Python reference's result values, ordering, and array shape.
- Inspect `/app/original/__init__.py` and the existing workspace implementation to establish the required semantics. The graded corpus includes semantic-prefix and boundary cases; the existing workspace implementation is the normative reference for their outcomes and is runnable for comparison.
- Keep the service-compatible entry implementation under `/app/implementation`; the harness invokes `from_factorial_base` through its JSON-lines calling mechanism.
- Preserve declared numeric comparison behavior where applicable: floating-point results are compared with `abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)`, while integer values, booleans, strings, field names, and array shapes must match exactly. Infinity signs and positions must match, and NaN is accepted only at matching NaN positions.

**What you CANNOT do**

- Do not implement a different factorial-base or permutation interpretation: observable behavior must match the Python `from_factorial_base` reference.
- Do not change the target language; the delivered implementation must be Go and build with the evaluator's offline Go toolchain.
- Do not rely on replacing `/app/run.sh` or `/app/build.sh` to affect grading; the evaluator builds and executes the sources in `/app/implementation` directly.
- Do not alter the calling convention: the required symbol is `from_factorial_base` and it is invoked with the declared positional integer-array argument.
- Do not spend effort reproducing malformed-input refusal behavior. Malformed input is excluded from the graded contract because the frozen refusal message cannot be reproduced across languages.
- Do not write diagnostics to the JSON response stream used by the service.

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

