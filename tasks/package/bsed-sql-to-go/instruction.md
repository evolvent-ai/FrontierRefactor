# Bsed SQL to Go

## Task Facts

* **Scale:** `package`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `go`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `default_interpreter`, `print_commands`, `print_help`, `main`, `parse_special_chars`, `keyword_to_user_input_type`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/implementation/main.go`, `/app/original/setup.py`, `/app/original/bsed/__init__.py`, `/app/original/tests/__init__.py`, `/app/implementation/subject.go`, `/app/original/bsed/definitions.py`, `/app/original/tests/context.py`, `/app/original/bsed/interpreter.py`, `/app/original/tests/test_append.py`, `/app/original/bsed/parser.py`, `/app/original/tests/test_clear.py`, `/app/original/bsed/special_chars.py`, `/app/original/tests/test_delete.py`, `/app/original/bsed/token_tree.py`, `/app/original/tests/test_escaped_symbols.py`, `/app/original/bsed/translator.py`, `/app/original/tests/test_in_place_flag.py`, `/app/original/tests/test_nonescaped_symbols.py`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Reimplement the Python `bsed` package's exposed operations in Go for improved performance while preserving the Python reference's observable behavior.

## Workspace

- `/app/implementation/main.go` contains the Go `entry` service entry point.
- `/app/implementation/subject.go` and `/app/implementation/go.mod` contain the target implementation and its Go build inputs.
- `/app/original/bsed/interpreter.py` defines the Python reference operations `default_interpreter`, `print_commands`, `print_help`, and `main`.
- `/app/original/bsed/special_chars.py` defines the Python reference operation `parse_special_chars`.
- `/app/original/bsed/token_tree.py` defines the Python reference operation `keyword_to_user_input_type`.
- `/app/original/bsed/parser.py`, `/app/original/bsed/translator.py`, and `/app/original/bsed/definitions.py` provide related reference behavior.
- `/app/original/bsed/config/command_translations.json`, `/app/original/bsed/config/line_condition_translations.json`, and `/app/original/bsed/config/token_tree.json` contain the package's translation and token configuration.
- `/app/run.sh` is the development JSON-lines service launcher, and `/app/build.sh` is the supplied development build entry point.

## Build & Test

Build the Go implementation from `/app`:

```sh
/app/build.sh
```

No self-check command is supplied. Inspect the reference source and available project files for checks; use the runnable Python implementation as the normative reference when establishing expected results.

Correctness is checked before performance is measured. The graded corpus covers 60 probes across all six operations, including 30 boundary cases, 24 error cases, and 6 valid cases. The existing runnable reference defines the expected behavior for those cases.

## Constraints

**What you CAN do**

- Implement the package in Go under `/app/implementation`, using `main.go`, `subject.go`, and other Go source or build-input files placed there as needed.
- Preserve all exposed operations: `default_interpreter`, `print_commands`, `print_help`, `main`, `parse_special_chars`, and `keyword_to_user_input_type`.
- Keep the `entry` symbol as the service entry point. Its first positional argument selects an operation, and remaining positional arguments are passed to that operation.
- Read and reproduce behavior from `/app/original/bsed` and its supplied JSON configuration files.
- Use Go's standard library for JSON handling, string processing, regular expressions, file access, and process execution where reference behavior requires them.
- Optimize internal parsing, token lookup, command construction, and repeated configuration access after behavior is established.
- Use `/app/run.sh` as the development launcher for the JSON-lines protocol; it is the harness mechanism for calling the subject.

**What you CANNOT do**

- Do not implement a different SQL-like language or alter observable behavior from the runnable Python reference, including boundary and malformed-input behavior covered by the graded corpus.
- Do not replace the required Go implementation with Python, Perl, a wrapper around the reference package, or another language.
- Do not omit, rename, or change the calling convention of any declared package operation.
- Do not rely on replacing `/app/run.sh` or `/app/build.sh` to affect grading; the evaluator builds and executes the Go target directly from `/app/implementation`.
- Do not write diagnostics to the JSON-lines response stream.
- Do not add dependency download or installation steps to the build process; use the trusted offline Go toolchain and available sources.

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

