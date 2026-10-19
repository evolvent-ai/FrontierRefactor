# Mathmodelagent Build Matplotlib Init Code Optimization

## Task Facts

* **Scale:** `module`
* **Task form:** in-place performance refactoring
* **Source language:** `python`
* **Workspace:** `/app`
* **Entry point:** `build_matplotlib_init_code`
* **Factory dispatch marker:** `serve build_matplotlib_init_code`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/serve.py`, `/app/subject.py`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream.

Optimize the existing Python implementation of `build_matplotlib_init_code` in place so it runs faster while preserving its observable behavior, public API, and calling convention; this is not a cross-language rewrite.

## Workspace

- `/app/subject.py`: authoritative implementation containing the `build_matplotlib_init_code` entry point.
- `/app/serve.py`: service launcher used to dispatch calls to the subject implementation.
- `/app/run.sh`: JSON-lines service entry script used by the harness.
- `/app/task-interface.json`: task interface and invocation metadata.
- `/app`: build directory and workspace root.

## Build & Test

No build commands or project-native self-check commands are supplied. Inspect `/app/subject.py`, `/app/serve.py`, and `/app/task-interface.json` for any available local checks before editing. The harness invokes `/app/run.sh` automatically and checks correctness before measuring runtime performance.

The graded probe corpus covers semantic-prefix, boundary, and malformed-input cases for the string parameter. The implementation present in `/app/subject.py` is the normative reference for the expected result of each case; it is runnable and can be compared against the optimized implementation.

## Constraints

**What you CAN do**

- Optimize only the selected Python function, `build_matplotlib_init_code`, and closely related private implementation details required by that function.
- Preserve the function's existing positional string-argument calling convention and its returned value.
- Reduce repeated parsing, scanning, allocation, or formatting work when doing so preserves the generated Matplotlib initialization code exactly in observable behavior.
- Use Python standard-library techniques and data structures that improve performance for repeated or large string inputs.
- Compare the optimized implementation with the existing implementation across representative valid, boundary, and malformed inputs before relying on an optimization.

**What you CANNOT do**

- Do not change the public API, function signature, accepted argument contract, return type, or observable output and error behavior.
- Do not rewrite the implementation in another language; this is an in-place Python optimization.
- Do not alter the JSON-lines harness protocol, `/app/run.sh`, request dispatch, response envelope, or diagnostic handling.
- Do not remove or special-case boundary or malformed-input behavior merely to improve speed; those cases are included in the graded corpus.
- Do not introduce dependencies, require installation steps, or change project configuration.
- Do not modify unrelated workspace files or expand the task into repository-wide refactoring.
- Do not assume that mathematically equivalent generated code is behaviorally equivalent; preserve the subject's observable result as established by the normative implementation.

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

