# Matrix2 Invertmatrix2 Invert Matrix2 Optimization

## Task Facts

* **Scale:** `kernel`
* **Task form:** in-place performance refactoring
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Entry point:** `invertMatrix2`
* **Factory dispatch marker:** `serve invertMatrix2`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/serve.cjs`, `/app/subject.js`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Improve the runtime performance of the existing JavaScript `invertMatrix2` kernel in place without changing its public API or observable behaviour.

## Workspace

- `/app` is the build directory and contains all implementation and launcher inputs.
- `/app/subject.js` contains the existing implementation and the `invertMatrix2` entry symbol.
- `/app/run.sh` launches the JSON-lines service used by the harness.
- `/app/serve.cjs` loads `subject.js` and dispatches calls to `invertMatrix2`.
- `/app/task-interface.json` defines the task interface.
- The harness launches the service with `node --experimental-specifier-resolution=node ./serve.cjs subject.js invertMatrix2`.
- Requests use `op="run"`, `call="entry"`, and an `args` array to invoke the function. This envelope is only the harness invocation mechanism; grading observes the function's results.
- Deliver the optimized implementation and any required build inputs under `/app`, retaining `/app/run.sh` as the launcher.

## Build & Test

No build commands or project-native self-check commands are supplied. Inspect the files under `/app` for available checks before making changes; do not invent a test command.

The harness automatically runs the frozen correctness suite and measures speed only after correctness passes. The graded corpus includes semantic-prefix, boundary, and malformed-input cases. The implementation initially present in `/app/subject.js` is the normative, runnable reference for the expected behaviour of every such case.

Floating-point results are compared using:

```text
abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)
```

Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. `NaN` is accepted only where the reference also returns `NaN`.

## Constraints

**What you CAN do**

- Optimize the existing JavaScript implementation of `invertMatrix2` in `/app/subject.js`.
- Reduce temporary allocations, intermediate arrays, property lookups, function calls, and repeated arithmetic where reference behaviour is preserved.
- Cache frequently accessed matrix elements in local variables when doing so preserves JavaScript evaluation order and observable access behaviour.
- Simplify determinant and inverse-element calculations only within the supplied floating-point comparison policy.
- Use JavaScript runtime-friendly control flow and data access patterns.
- Inspect and compare against the original implementation to establish behaviour for semantic-prefix, boundary, and malformed-input cases.
- Modify `/app/run.sh` or other delivered build inputs only when necessary to keep the supplied launcher operational and API-compatible.

**What you CANNOT do**

- Change the observable behaviour of `invertMatrix2`, including behaviour for graded boundary and malformed-input cases.
- Change the `invertMatrix2` public API, calling convention, argument handling, return structure, field names, or array shapes.
- Rewrite the kernel in another language or replace it with native, WebAssembly, or external-process code; the implementation must remain JavaScript.
- Assume inputs are always ordinary, valid, nonsingular 2-by-2 matrices when the reference accepts or processes other inputs.
- Reorder coercions, indexed reads, arithmetic, or side effects when that changes behaviour observable from JavaScript.
- Require bitwise equality for floating-point results; use the stated absolute and relative tolerances, while preserving the required `NaN` and signed-infinity positions.
- Add dependencies or alter the JSON-lines harness protocol as a substitute for optimizing the selected computation.
- Broaden the task into repository-wide refactoring unrelated to the `invertMatrix2` kernel.

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

