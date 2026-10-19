# Pymemoryeditor Process Search Optimization

## Task Facts

* **Scale:** `package`
* **Task form:** in-place performance refactoring
* **Source language:** `python`
* **Workspace:** `/app`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `tokenize_pattern`, `parse_value_type`, `parse_scan_type`, `find_spec`
* **Delivered source paths:** `/app/Makefile`, `/app/README.md`, `/app/pyproject.toml`, `/app/run.sh`, `/app/task-interface.json`, `/app/PyMemoryEditor/__init__.py`, `/app/scripts/__init__.py`, `/app/PyMemoryEditor/app/__init__.py`, `/app/PyMemoryEditor/linux/functions.py`, `/app/PyMemoryEditor/macos/__init__.py`, `/app/PyMemoryEditor/mcp/__init__.py`, `/app/PyMemoryEditor/process/__init__.py`, `/app/PyMemoryEditor/util/__init__.py`, `/app/PyMemoryEditor/win32/functions.py`, `/app/PyMemoryEditor/win32/enums/__init__.py`, `/app/PyMemoryEditor/__main__.py`, `/app/scripts/build_preview.py`, `/app/PyMemoryEditor/app/_auto_refresh_dialog.py`, `/app/PyMemoryEditor/linux/libc.py`, `/app/PyMemoryEditor/macos/functions.py`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Make the python implementation faster without changing its observable behaviour.

## Workspace

* `/app` — your working directory; everything you submit lives here
* Entry point / symbol under test: `entry`

## Build & Test

No project-native self-check command was supplied. Inspect the available source and project configuration for a real test, sample invocation, or benchmark; the harness performs official grading automatically.

## Constraints

Treat the package as one contract surface and preserve every exposed operation, including dispatch, serialization, errors, and operation-specific behavior.

**What you CAN do**

* Change any part of the implementation in python

**What you CANNOT do**

* Change the public API or the language

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

