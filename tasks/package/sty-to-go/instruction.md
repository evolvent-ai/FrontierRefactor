# Sty to Go

## Task Facts

* **Scale:** `package`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `go`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `mute`, `unmute`, `sgr`, `eightbit_fg`, `eightbit_bg`, `rgb_fg`, `rgb_bg`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/implementation/main.go`, `/app/original/sty/__init__.py`, `/app/original/tests/__init__.py`, `/app/original/tests/docs/__init__.py`, `/app/implementation/subject.go`, `/app/original/sty/lib.py`, `/app/original/tests/__main__.py`, `/app/original/tests/docs/coloring.py`, `/app/original/sty/primitive.py`, `/app/original/tests/demo.py`, `/app/original/tests/docs/customizing.py`, `/app/original/sty/register.py`, `/app/original/tests/performance.py`, `/app/original/tests/docs/effects.py`, `/app/original/sty/renderfunc.py`, `/app/original/tests/test_ansi_values.py`, `/app/original/tests/docs/etc.py`, `/app/original/sty/rendertype.py`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Reimplement the Python `sty` package in Go for better performance while preserving the observable behavior of all seven exposed string-styling operations.

## Workspace

- `/app/implementation/main.go`: Go entry point supplied for the target implementation.
- `/app/implementation/subject.go`: Go implementation source.
- `/app/implementation/go.mod`: Go module and build configuration.
- `/app/original/sty/lib.py`: Python reference implementation for `mute` and `unmute`.
- `/app/original/sty/renderfunc.py`: Python reference implementation for `sgr`, `eightbit_fg`, `eightbit_bg`, `rgb_fg`, and `rgb_bg`.
- `/app/original/sty/primitive.py`, `/app/original/sty/register.py`, and `/app/original/sty/rendertype.py`: supporting reference behavior.
- `/app/run.sh`: development JSON-lines service launcher.
- `/app/build.sh`: development build entry point.
- `/app/task-interface.json`: interface and dispatch metadata.

The entry point is `entry`. The first positional argument selects one of these operations: `mute`, `unmute`, `sgr`, `eightbit_fg`, `eightbit_bg`, `rgb_fg`, or `rgb_bg`. Remaining positional arguments must follow the selected Python operation's calling convention.

## Build & Test

Build the Go sources with:

```sh
/app/build.sh
```

This performs the supplied development build. The evaluator independently builds sources under `/app/implementation` with its trusted offline Go toolchain, so keep all implementation sources and build inputs there.

Run the development service with:

```sh
/app/run.sh
```

This starts the JSON-lines harness interface for exercising `entry`. Requests use the supplied envelope containing an `id`, `op: "run"`, `call: "entry"`, and positional `args`; the envelope is only the harness mechanism, while grading observes the operation results.

No dedicated self-check command is supplied. Inspect the Python reference and available project files for useful checks. The frozen grading suite covers 65 probes across the seven operations, including 51 valid cases, 7 boundary cases, and 7 malformed-input cases. Correctness is checked before performance is measured.

## Constraints

**What you CAN do**

- Replace or complete the Go sources under `/app/implementation`.
- Use Go's standard library and efficient string construction, formatting, and integer handling to implement terminal escape-sequence rendering.
- Inspect and run the implementation under `/app/original/sty` as the normative reference for expected behavior.
- Optimize allocations and repeated formatting work after matching the reference behavior.
- Preserve the seven package operations collectively:
  - `mute(*objects)`
  - `unmute(*objects)`
  - `sgr(num)`
  - `eightbit_fg(num)`
  - `eightbit_bg(num)`
  - `rgb_fg(r, g, b)`
  - `rgb_bg(r, g, b)`

**What you CANNOT do**

- Do not implement the solution in Python or another language; the delivered implementation must be Go.
- Do not omit, rename, or change the calling convention of any declared operation.
- Do not assume boundary or malformed-input behavior. Those cases are part of the graded corpus, and the runnable Python implementation already present in `/app/original/sty` is the normative reference for what they must do.
- Do not change the observable results established by the Python reference, including returned string contents, formatting, errors, or handling of valid and invalid arguments.
- Do not place required implementation sources or build inputs outside `/app/implementation`.
- Do not rely on downloading dependencies or network access; the evaluator uses an offline toolchain.
- Do not treat `/app/run.sh` or `/app/build.sh` as the graded product. They are development entry points; the evaluator builds the target sources directly.
- Do not write diagnostics into the JSON response stream used by the harness.

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

We run **62 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **the value the call returned**

That is **62 graded observation(s)** in total.

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

