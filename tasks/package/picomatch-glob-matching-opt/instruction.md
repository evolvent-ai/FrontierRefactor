# Picomatch Glob Matching Optimization

## Task Facts

* **Scale:** `package`
* **Task form:** in-place performance refactoring
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `isObject`, `hasRegexChars`, `isRegexChar`, `escapeRegex`, `toPosixSlashes`, `isWindows`, `removeBackslashes`, `escapeLast`, `removePrefix`, `wrapOutput`, `basename`
* **Delivered source paths:** `/app/README.md`, `/app/package.json`, `/app/run.sh`, `/app/task-interface.json`, `/app/bench/first-match-minimatch.js`, `/app/examples/extglob-negated.js`, `/app/lib/constants.js`, `/app/picomatch/index.js`, `/app/picomatch/bench/first-match-minimatch.js`, `/app/picomatch/examples/extglob-negated.js`, `/app/picomatch/lib/constants.js`, `/app/picomatch/test/api.picomatch.js`, `/app/picomatch/test/support/match.js`, `/app/bench/first-match-picomatch.js`, `/app/examples/extglob.js`, `/app/lib/parse.js`, `/app/picomatch/posix.js`, `/app/picomatch/bench/first-match-picomatch.js`, `/app/picomatch/examples/extglob.js`, `/app/picomatch/lib/parse.js`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Optimize the existing JavaScript picomatch utility operations in place for lower runtime cost while preserving every observable result and the public API.

## Workspace

- `/app/lib/utils.js`: Primary implementation of the 11 graded utility operations.
- `/app/lib/constants.js`: Shared constants used by the package implementation.
- `/app/lib/parse.js`, `/app/lib/scan.js`, and `/app/lib/picomatch.js`: Related package internals that may constrain utility behavior.
- `/app/index.js` and `/app/posix.js`: Public package entry points.
- `/app/subject.cjs`: Grading subject and exported `entry` symbol.
- `/app/serve.cjs`: JSON-lines service launcher used by the harness.
- `/app/run.sh`: Harness run command. It launches the service from `/app`.
- `/app/task-interface.json`: Machine-readable interface definition.
- `/app/package.json`: Package metadata and available project scripts.
- `/app/picomatch/lib/utils.js`: Additional supplied copy of the utility implementation; inspect its relationship to `/app/lib/utils.js` before deciding whether corresponding changes are required.
- `/app/bench/` and `/app/picomatch/bench/`: Existing benchmark sources available for implementation context.
- `/app/README.md`: Package documentation and API context.

## Build & Test

No build command or project-native self-check command is supplied. Inspect `/app/package.json` and the existing source for available checks; do not assume an undocumented command exists.

The harness invokes `/app/run.sh`, which starts `/app/serve.cjs` with `/app/subject.cjs` and the `entry` symbol. This is the grading transport, not a project-native correctness or performance test. Requests select one of these operations through the first positional argument:

`isObject`, `hasRegexChars`, `isRegexChar`, `escapeRegex`, `toPosixSlashes`, `isWindows`, `removeBackslashes`, `escapeLast`, `removePrefix`, `wrapOutput`, and `basename`.

The frozen grader checks correctness first and measures speed only after the implementation passes correctness. The graded corpus contains 140 probes across all 11 operations: 118 valid cases, 11 boundary cases, and 11 error cases. The implementation already present in the workspace is the normative reference for each result and error behavior; compare candidate optimizations against it when establishing expected behavior.

## Constraints

**What you CAN do**

- Optimize the existing JavaScript implementation in place under `/app`.
- Improve hot paths with cheaper condition ordering, reduced allocation, fewer temporary strings, fewer regular-expression executions, and simpler loops where equivalent behavior can be demonstrated.
- Hoist reusable constants or regular expressions when doing so does not introduce mutable shared state or observable initialization changes.
- Add internal helpers when they measurably reduce duplicated work and do not alter exports or calling conventions.
- Specialize common cases with fast paths while retaining the existing behavior for uncommon, boundary, and error inputs.
- Use the existing implementation as the behavioral oracle for all graded operations.
- Inspect the supplied benchmark sources and package metadata to understand existing performance patterns and available project checks.
- Modify implementation and build inputs under `/app` and keep `/app/run.sh` operational.

**What you CANNOT do**

- Change the observable behavior, public API, exports, operation names, argument conventions, return values, mutation behavior, or thrown-error behavior of any graded operation.
- Replace JavaScript with another language or introduce a cross-language implementation.
- Remove or bypass any of the 11 declared operations exposed through `entry`.
- Optimize only ordinary valid inputs while changing the 11 graded boundary cases or 11 graded error cases.
- Treat the JSON-lines request envelope, request IDs, or diagnostic-stream handling as the behavior being optimized; they are only the harness mechanism used to call the subject.
- Add dependencies or rely on network access, external services, machine-specific state, or undeclared executables.
- Hard-code outputs for the known probe counts or particular anticipated inputs.
- Change `/app/run.sh`, `/app/serve.cjs`, or `/app/subject.cjs` in a way that avoids executing the real package operations.
- Invent benchmark thresholds, performance formulas, build commands, or self-check commands not supplied by the workspace context.

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

We run **137 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **the value the call returned**

That is **137 graded observation(s)** in total.

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

