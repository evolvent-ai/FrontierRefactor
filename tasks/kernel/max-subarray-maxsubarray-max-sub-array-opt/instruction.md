# Max Subarray Maxsubarray Max Sub Array Optimization

## Task Facts

* **Scale:** `kernel`
* **Task form:** in-place performance refactoring
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Entry point:** `maxSubArray`
* **Factory dispatch marker:** `serve maxSubArray`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/serve.cjs`, `/app/subject.js`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Optimize the existing JavaScript `maxSubArray` computation in place for lower runtime while preserving its public API and all observable behavior.

## Workspace

- `/app` is the build directory and contains the complete delivered task workspace.
- `/app/subject.js` contains the existing implementation and the `maxSubArray` entry symbol to optimize.
- `/app/run.sh` launches the JSON-lines service used by the harness.
- `/app/serve.cjs` loads `subject.js` and dispatches calls to `maxSubArray`.
- `/app/task-interface.json` describes the task interface and invocation contract.
- The launcher runs Node.js with `--experimental-specifier-resolution=node`.
- Requests invoke `maxSubArray` through `call="entry"` with an array of positional arguments. The JSON-lines envelope is only the harness transport; grading observes the function's results.

## Build & Test

No build commands or project-native self-check commands are supplied. The launcher performs any required preparation automatically. Inspect `/app/subject.js` and the other supplied workspace files for available checks before making changes; do not invent a test command.

The harness automatically checks correctness before measuring performance. Speed is measured only for an implementation that passes the frozen correctness suite.

Floating-point results are compared using:

```text
abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)
```

Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. `NaN` is accepted only where the reference also produces `NaN`.

## Constraints

**What you CAN do**

- Modify the implementation and required build inputs under `/app`.
- Optimize `maxSubArray` using JavaScript-specific techniques such as reducing allocations, avoiding temporary arrays and callbacks, simplifying hot-loop control flow, caching repeated property reads, and using a single linear scan where compatible with the reference behavior.
- Specialize the hot path for the declared `float_array` parameter while retaining every behavior exercised by the graded corpus.
- Use `/app/run.sh` and the supplied JSON-lines interface to investigate the current implementation's behavior.
- Treat the implementation initially present in `/app/subject.js` as the normative behavioral reference.
- Preserve floating-point outputs within the supplied tolerance rather than requiring bitwise equality.

**What you CANNOT do**

- Change the public API, entry symbol, calling convention, return structure, input mutation behavior, exception behavior, or any other observable behavior of `maxSubArray`.
- Rewrite the implementation in another language; this is an in-place JavaScript optimization.
- Replace or bypass `maxSubArray` with a different externally visible interface.
- Assume only ordinary finite arrays are graded. The graded corpus includes semantic-prefix, boundary, and malformed-input cases. Establish the expected result for each case by comparing against the runnable implementation initially present in the workspace; do not invent new behavior for those inputs.
- Require exact floating-point equality when the supplied tolerance permits a difference.
- Change the sign or position of infinities, produce `NaN` where the reference does not, or omit `NaN` where the reference produces it.
- Add dependency installation or download steps as build commands.
- Write diagnostics or other non-protocol content to the JSON-lines response stream.

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

