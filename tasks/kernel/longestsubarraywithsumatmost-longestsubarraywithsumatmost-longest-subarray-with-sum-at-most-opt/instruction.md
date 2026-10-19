# Longestsubarraywithsumatmost Longestsubarraywithsumatmost Longest Subarray With Sum At Most Optimization

## Task Facts

* **Scale:** `kernel`
* **Task form:** in-place performance refactoring
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Entry point:** `longestSubarrayWithSumAtMost`
* **Factory dispatch marker:** `serve longestSubarrayWithSumAtMost`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/serve.cjs`, `/app/subject.js`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Improve the runtime performance of the JavaScript `longestSubarrayWithSumAtMost` function in place while preserving its public API and every observable behavior.

## Workspace

- [`/app/subject.js`](/app/subject.js): implementation containing the `longestSubarrayWithSumAtMost` entry point to optimize.
- [`/app/run.sh`](/app/run.sh): JSON-lines service launcher used by the harness.
- [`/app/serve.cjs`](/app/serve.cjs): service dispatch used to invoke the selected entry point.
- [`/app/task-interface.json`](/app/task-interface.json): task interface and invocation metadata.
- `/app`: workspace containing the implementation and build inputs for the deliverable.

## Build & Test

No build commands or project-native self-check commands are supplied. Inspect the source and available project files for any applicable checks rather than inventing a command.

The supplied service command is:

```sh
/app/run.sh
```

This starts the harness interface used to call `longestSubarrayWithSumAtMost`; it is not a standalone correctness test. The harness checks correctness first and measures performance only after the implementation passes.

The graded corpus includes semantic-prefix, boundary, and malformed-input cases. The implementation currently present in `/app/subject.js` is the normative runnable reference for the expected behavior of those cases. Compare the optimized implementation against that reference when establishing correctness; do not infer or redefine their outcomes.

## Constraints

**What you CAN do**

- Modify the implementation of `longestSubarrayWithSumAtMost` in [`/app/subject.js`](/app/subject.js).
- Optimize the selected computation for JavaScript and the declared `float_array, float` parameters.
- Improve algorithmic complexity, reduce unnecessary allocations, simplify hot loops, and use JavaScript data structures or numeric operations that preserve the existing results.
- Keep changes focused on the selected kernel and inspect the existing implementation before choosing an optimization.
- Preserve the current behavior for normal inputs, semantic-prefix cases, boundary cases, malformed inputs, and floating-point edge cases.

**What you CANNOT do**

- Do not change the public API, calling convention, entry-point name, or argument order of `longestSubarrayWithSumAtMost`.
- Do not rewrite the task in another language; the implementation must remain JavaScript.
- Do not change observable behavior, including behavior for malformed inputs and boundary cases.
- Do not replace the selected function with a different contract or assume mathematical behavior that differs from the normative implementation.
- Do not alter the JSON-lines launcher protocol, harness dispatch, or unrelated workspace behavior.
- Do not require bitwise equality for floating-point results. The comparison policy allows `abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)`.
- Preserve integer values, booleans, strings, field names, and array shapes exactly; infinities must match in sign and position, and `NaN` is accepted only at matching positions.
- Deliver the optimized implementation and any required build inputs under `/app`.

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

