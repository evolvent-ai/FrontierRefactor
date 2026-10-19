# Persiantools to Go

## Task Facts

* **Scale:** `package`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `go`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `ar_to_fa`, `fa_to_ar`, `en_to_fa`, `fa_to_en`, `to_word`, `replace`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/implementation/main.go`, `/app/original/persiantools/__init__.py`, `/app/original/tests/__init__.py`, `/app/implementation/subject.go`, `/app/original/persiantools/characters.py`, `/app/original/tests/test_characters.py`, `/app/original/persiantools/digits.py`, `/app/original/tests/test_digits.py`, `/app/original/persiantools/jdatetime.py`, `/app/original/tests/test_jalalidate.py`, `/app/original/persiantools/utils.py`, `/app/original/tests/test_jalalidatetime.py`, `/app/original/tests/test_official_kabise.py`, `/app/original/tests/test_performance.py`, `/app/original/tests/test_utils.py`, `/app/original/AGENTS.md`, `/app/original/CHANGELOG.md`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Reimplement the exposed `persiantools` character, digit, and utility operations in Go with observable behavior equivalent to the Python reference and improved performance through the cross-language rewrite.

## Workspace

- `/app/implementation/main.go` — Go service entry source; preserve the `entry` dispatch contract.
- `/app/implementation/subject.go` — existing Go implementation source to inspect and extend.
- `/app/implementation/go.mod` — Go build configuration.
- `/app/original/persiantools/characters.py` — reference implementations for `ar_to_fa` and `fa_to_ar`.
- `/app/original/persiantools/digits.py` — reference implementations for `en_to_fa`, `fa_to_en`, and `to_word`.
- `/app/original/persiantools/utils.py` — reference implementation for `replace`.
- `/app/original/tests/test_characters.py`, `/app/original/tests/test_digits.py`, and `/app/original/tests/test_utils.py` — source-level reference checks.
- `/app/build.sh` — supplied build entrypoint.
- `/app/run.sh` — supplied JSON-lines service entrypoint.
- `/app/task-interface.json` — task interface metadata.

## Build & Test

Build the Go sources that will be graded:

```sh
/app/build.sh
```

Run the product as the supplied JSON-lines service for development checks:

```sh
/app/run.sh
```

No dedicated self-check command is supplied. Inspect the reference source and available project checks when validating behavior. The harness invokes `entry` through requests whose first argument selects one of these operations: `ar_to_fa`, `fa_to_ar`, `en_to_fa`, `fa_to_en`, `to_word`, or `replace`.

Correctness is checked before performance is measured. The graded corpus contains 66 probes: 54 valid cases, 6 boundary cases, and 6 error or malformed-input cases. The runnable implementation already present in the workspace is normative for the expected result of every case; compare the Go implementation against it rather than assuming outcomes for boundary or error inputs.

## Constraints

**What you CAN do**

- Replace or refactor the Go sources under `/app/implementation`, including the dispatch and operation implementations.
- Use Go-native string and rune processing, lookup tables, preallocated buffers, and allocation-conscious conversions to improve throughput.
- Read the Python package and its tests to reproduce exact character mappings, digit conversion, number-word formatting, replacement semantics, validation, and error behavior.
- Preserve JSON-safe result types and operation-specific return values.
- Keep build inputs under `/app/implementation` and use only the available offline Go toolchain.

**What you CANNOT do**

- Do not implement the solution in Python or another language; the graded target must be a buildable Go implementation.
- Do not omit, rename, or change the calling convention of any declared operation. `entry` receives positional arguments with the operation name first and must dispatch all six operations.
- Do not alter observable behavior to simplify malformed, boundary, or error cases; those cases are part of the graded corpus and must match the runnable reference.
- Do not replace the graded implementation by modifying `/app/run.sh` or `/app/build.sh`; the evaluator builds sources in `/app/implementation` directly.
- Do not treat the JSON-lines request and response envelope as subject behavior. Use it only as the harness mechanism, preserving request IDs and success/error response shape without adding diagnostics to the response stream.
- Do not add network-dependent build steps or rely on unavailable dependencies.

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

We run **63 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **the value the call returned**

That is **63 graded observation(s)** in total.

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

