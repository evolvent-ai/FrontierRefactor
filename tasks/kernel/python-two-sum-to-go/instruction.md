# Python Two Sum to Go

## Task Facts

* **Scale:** `kernel`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `go`
* **Entry point:** `twoSum`
* **Factory dispatch marker:** `serve twoSum`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/implementation/main.go`, `/app/original/Two_Sum.py`, `/app/implementation/subject.go`, `/app/build.sh`, `/app/implementation/go.mod`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Reimplement the Python `twoSum` function in Go for improved performance while preserving the reference implementation's observable behavior.

## Workspace

- `/app/original/Two_Sum.py`: frozen Python reference implementation to inspect and use when establishing expected behavior.
- `/app/implementation/main.go`: Go entry-point source for the delivered implementation.
- `/app/implementation/subject.go`: Go source associated with the subject implementation.
- `/app/implementation/go.mod`: Go module build input.
- `/app/implementation`: directory containing all Go implementation sources and build inputs that the evaluator builds.
- `/app/build.sh`: supplied development build entry point.
- `/app/run.sh`: supplied JSON-lines service launcher used to invoke `twoSum`.
- `/app/task-interface.json`: task interface metadata.

## Build & Test

Build the Go implementation from `/app`:

```sh
/app/build.sh
```

Use the supplied service launcher from `/app` to exercise the `twoSum` entry point through the JSON-lines harness:

```sh
/app/run.sh
```

No project-native self-check command is supplied. Inspect the available source files, especially `/app/original/Two_Sum.py`, for behavior to compare during development. The harness checks correctness before measuring performance.

## Constraints

**What you CAN do**

- Implement the `twoSum` entry point in Go under `/app/implementation`.
- Read `/app/original/Two_Sum.py` and compare against the runnable workspace implementation to establish the required result shape, ordering, duplicate handling, and no-match behavior.
- Use Go data structures appropriate for the reference semantics, including maps when they preserve the Python function's observable behavior and improve lookup performance.
- Optimize allocation patterns, lookup complexity, and iteration while retaining the Python reference's externally visible results.
- Preserve the calling contract for an `int_array` parameter containing `int64` values in the declared range `[-1000, 1000]` and an integer target in the same range.
- Preserve the supplied numeric comparison policy when numeric results occur: floating-point values use `abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)` with `float64` precision; integer values, booleans, strings, field names, and array shapes must match exactly; infinities must match by sign and position; NaN is accepted only at matching positions.
- Use `/app/run.sh` as the harness mechanism for invoking `twoSum`; requests are JSON-lines calls with positional arguments.

**What you CANNOT do**

- Do not implement a different two-sum contract based on conventional expectations; semantic-prefix and boundary cases are part of the graded corpus, and the runnable implementation already present in the workspace is the normative reference for their behavior.
- Do not rely on reproducing malformed-input failures. Malformed input is excluded because the Python refusal message cannot be frozen and reproduced reliably in Go.
- Do not change the target language: the delivered implementation must remain Go.
- Do not place required implementation sources or build inputs outside `/app/implementation`; the evaluator builds that directory directly with its trusted offline toolchain.
- Do not assume replacing `/app/run.sh` or `/app/build.sh` changes the graded program. They are development entry points only.
- Do not change the entry symbol from `twoSum` or alter its positional-argument calling convention.
- Do not write diagnostics to the JSON-lines response stream used by the launcher.

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

