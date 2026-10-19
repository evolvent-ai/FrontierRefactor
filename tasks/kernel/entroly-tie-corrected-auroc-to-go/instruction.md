# Entroly Tie Corrected Auroc to Go

## Task Facts

* **Scale:** `kernel`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `go`
* **Entry point:** `tie_corrected_auroc`
* **Factory dispatch marker:** `serve tie_corrected_auroc`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/implementation/main.go`, `/app/original/metrics.py`, `/app/implementation/subject.go`, `/app/build.sh`, `/app/implementation/go.mod`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Reimplement the Python `tie_corrected_auroc` kernel in Go for improved performance while preserving the reference implementation’s observable behavior.

## Workspace

- `/app/implementation/main.go` — Go implementation entry source.
- `/app/implementation/subject.go` — Go subject implementation support.
- `/app/implementation/go.mod` — Go module definition and build input.
- `/app/original/metrics.py` — Python reference implementation to match.
- `/app/run.sh` — development JSON-lines service launcher.
- `/app/build.sh` — development build entry point.
- `/app/task-interface.json` — task interface metadata.
- `/app/implementation` — required location for implementation sources and build inputs.

## Build & Test

Build the Go implementation from `/app`:

```sh
/app/build.sh
```

No project-native self-check command is supplied. Inspect the provided source and interface files for available local checks; the harness performs correctness checks automatically.

## Constraints

**What you CAN do**

- Implement the `tie_corrected_auroc` entry symbol in Go under `/app/implementation`.
- Translate the Python Mann–Whitney AUROC computation, including midrank handling for tied score values, while optimizing data layout, sorting, and allocation behavior where equivalent.
- Use Go `float64` arithmetic and integer handling appropriate for the declared inputs: a `float_array` of scores and an `int_array` of equal length.
- Inspect `/app/original/metrics.py` and the implementation already present in the workspace as the normative reference for observable behavior.
- Preserve the harness calling interface: the launcher uses JSON-lines requests to invoke the `entry` call, and results must be returned through the service protocol without diagnostics on the response stream.
- Match floating-point results within `abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)`. Preserve integer values, booleans, strings, field names, and array shapes exactly when applicable. Preserve infinity sign and position; `NaN` is accepted only at matching `NaN` positions.
- Expect correctness to be checked before performance is measured; optimize only after preserving the reference behavior.

**What you CANNOT do**

- Do not replace the task with a Python implementation or change the target language: this is a cross-language rewrite and the deliverable must be a Go implementation.
- Do not alter `/app/run.sh` or `/app/build.sh` as a substitute for implementing the graded program; the evaluator builds sources in `/app/implementation` with its trusted offline toolchain and executes that product directly.
- Do not change the entry point name or calling convention for `tie_corrected_auroc`.
- Do not assume ungraded behavior for the probe contract: the graded corpus includes semantic-prefix and boundary cases, and the workspace implementation is the normative reference for their expected behavior. Malformed input is excluded from grading.
- Do not invent behavior for excluded malformed inputs or rely on a frozen refusal message being reproducible across languages.
- Do not add dependency download or installation steps; keep all required implementation and build inputs under `/app/implementation`.

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

