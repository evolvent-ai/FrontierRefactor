# Pyarabic Text to Go

## Task Facts

* **Scale:** `package`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `go`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `is_sukun`, `is_shadda`, `is_tatweel`, `is_tanwin`, `is_tashkeel`, `is_haraka`, `is_shortharaka`, `is_ligature`, `is_hamza`, `is_alef`, `is_yehlike`, `is_wawlike`, `is_teh`, `is_small`, `is_weak`, `is_moon`, `is_sun`, `order`, `name`, `arabicrange`, `has_shadda`, `is_vocalized`, `is_vocalizedtext`, `is_arabicstring`, `is_arabicrange`, `is_arabicword`, `first_char`, `second_char`, `last_char`, `secondlast_char`, `strip_harakat`, `strip_lastharaka`, `strip_tashkeel`, `strip_small`, `strip_tatweel`, `strip_shadda`, `strip_diacritics`, `normalize_ligature`, `normalize_hamza`, `normalize_teh`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/implementation/main.go`, `/app/original/setup.py`, `/app/original/docs/conf.py`, `/app/original/pyarabic/__init__.py`, `/app/original/tests/pyArabicExample.py`, `/app/original/tests/unit/__init__.py`, `/app/implementation/subject.go`, `/app/original/pyarabic/arabrepr.py`, `/app/original/tests/test_araby.py`, `/app/original/tests/unit/test_araby.py`, `/app/original/pyarabic/araby.py`, `/app/original/tests/test_number.py`, `/app/original/pyarabic/araby_const.py`, `/app/original/tests/test_number_ordinal.py`, `/app/original/pyarabic/kalima.py`, `/app/original/tests/test_soundex.py`, `/app/original/pyarabic/named.py`, `/app/original/tests/test_tokenize_pos.py`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Reimplement the exposed `pyarabic.araby` package operations in Go so their observable results match the Python reference while improving runtime performance through the cross-language rewrite.

## Workspace

- `/app/implementation/main.go`: Go service entry point and required `entry` dispatch implementation.
- `/app/implementation/subject.go`: existing Go implementation source to inspect and extend.
- `/app/implementation/go.mod`: Go build configuration.
- `/app/original/pyarabic/araby.py`: Python reference implementation for all exposed package operations.
- `/app/original/pyarabic/araby_const.py`: Python constants and character classifications used by `araby.py`.
- `/app/run.sh`: development entry point that serves JSON-lines requests.
- `/app/build.sh`: development build entry point.
- `/app/task-interface.json`: task interface and dispatch metadata.

The package surface contains 40 operations, including character predicates and classifications, Arabic text checks, character accessors, stripping functions, and normalization functions. The required entry symbol is `entry`; the first request argument selects the operation and the remaining arguments are its positional arguments.

## Build & Test

Build the Go implementation from `/app`:

```sh
/app/build.sh
```

Run the implementation as the JSON-lines development service:

```sh
/app/run.sh
```

The service accepts requests containing `id`, `op="run"`, `call="entry"`, and an `args` array. This envelope is only the harness invocation mechanism; graded behavior is the returned result of each package operation. No separate self-check command is supplied. Inspect `/app/original/pyarabic/araby.py`, `/app/original/pyarabic/araby_const.py`, and the existing Go sources for available project-native checks or comparison workflows.

Correctness is evaluated against the frozen probe corpus before performance is measured. The corpus contains 242 probes across valid, boundary, and error cases; the existing runnable implementation is the normative reference for the expected result of every graded case.

## Constraints

**What you CAN do**

- Implement and optimize the package in Go under `/app/implementation`.
- Use Go rune-aware processing and precomputed lookup tables or sets for Arabic Unicode classifications where they preserve Python behavior.
- Reuse the reference source and constants to reproduce character predicates, Unicode handling, string indexing behavior, normalization mappings, and stripping behavior.
- Add or modify Go build inputs under `/app/implementation` as needed for the implementation.
- Preserve the declared operation names and dispatch all operations through `entry`.

**What you CANNOT do**

- Do not switch to Python or another implementation language; the delivered target must be a buildable Go implementation.
- Do not omit, rename, or combine any of the 40 declared package operations.
- Do not change the positional calling convention: the first element of `args` is the operation name and subsequent elements are that operation's arguments.
- Do not infer behavior for boundary or error inputs; match the runnable Python reference, because those cases are included in the graded corpus.
- Do not treat the JSON-lines request/response envelope as the subject behavior being optimized or redefine operation results to fit the transport.
- Do not place required implementation sources or build inputs outside `/app/implementation`.
- Do not add dependency installation or network-dependent build steps; the evaluator uses a trusted offline Go toolchain.
- Do not claim correctness from compilation alone. The harness checks behavioral equivalence first and measures speed only after correctness passes.

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

We run **197 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **the value the call returned**

That is **197 graded observation(s)** in total.

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

