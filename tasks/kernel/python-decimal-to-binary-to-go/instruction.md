# Python Decimal to Binary to Go

## Task Facts

* **Scale:** `kernel`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `go`
* **Entry point:** `decimal_to_binary`
* **Factory dispatch marker:** `serve decimal_to_binary`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/implementation/main.go`, `/app/original/quinc_mc_cluskey.py`, `/app/implementation/subject.go`, `/app/build.sh`, `/app/implementation/go.mod`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Reimplement the Python `decimal_to_binary` computation in Go for equivalent observable results with improved performance through the cross-language rewrite.

## Workspace

- `/app/original/quinc_mc_cluskey.py` — runnable Python reference implementation that defines the normative behavior of `decimal_to_binary`.
- `/app/implementation/main.go` — Go entry source to implement and expose the target.
- `/app/implementation/subject.go` — existing Go implementation source.
- `/app/implementation/go.mod` — Go module and build configuration.
- `/app/build.sh` — development build entrypoint, runnable from `/app`.
- `/app/run.sh` — development JSON-lines service entrypoint.
- `/app/task-interface.json` — task interface metadata.
- `/app/implementation/` — directory containing the Go sources and build inputs used by the evaluator.

## Build & Test

Build the Go implementation from `/app`:

```sh
/app/build.sh
```

After building, exercise the development JSON-lines service with the task's representative call:

```sh
printf '%s\n' '{"id":1,"op":"run","call":"entry","args":[3,[1.5]]}' | /app/run.sh
```

The service request envelope is only the harness mechanism for invoking the subject; assess the returned subject value against the Python reference. No additional self-check command is supplied; inspect the source for any available project-native checks. The harness runs the frozen correctness suite automatically before measuring performance.

## Constraints

**What you CAN do**

- Replace or extend the implementation under `/app/implementation` in Go.
- Implement the `decimal_to_binary` entry point for an integer and a float64 array.
- Use Go-native data structures and algorithms to reduce allocation and conversion overhead while preserving the reference computation.
- Compare behavior with `/app/original/quinc_mc_cluskey.py` while developing, including semantic-prefix and boundary cases.
- Preserve the result's structure and element types expected by the calling interface.

**What you CANNOT do**

- Do not change languages: the delivered implementation must be Go and must build from sources under `/app/implementation`.
- Do not change the `decimal_to_binary` calling convention or require a different entry point.
- Do not treat malformed-input behavior as part of the required compatibility target; malformed input is excluded because the reference refusal message is language-specific.
- The graded corpus includes semantic-prefix and boundary cases. Use the runnable Python implementation already in the workspace as the normative reference for the expected result of each case; do not assume outcomes that are not established by that reference.
- Preserve exact integer values, booleans, strings, field names, and array shapes.
- For floating-point results, match the supplied float64 comparison policy: absolute error must be at most `1e-12 + 1e-09 * abs(reference)`.
- Preserve matching NaN positions and the sign and position of infinities; do not require bitwise equality for ordinary floating-point values.
- Do not rely on replacing `/app/run.sh` or `/app/build.sh`; the evaluator builds the target sources directly with its trusted offline toolchain.
- Do not write diagnostics to the JSON-lines response stream.

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

