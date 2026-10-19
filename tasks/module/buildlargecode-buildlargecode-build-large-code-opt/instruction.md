# Buildlargecode Buildlargecode Build Large Code Optimization

## Task Facts

* **Scale:** `module`
* **Task form:** in-place performance refactoring
* **Source language:** `typescript`
* **Workspace:** `/app`
* **Entry point:** `buildLargeCode`
* **Factory dispatch marker:** `serve buildLargeCode`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/subject.ts`, `/app/serve.cjs`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream.

Optimize the existing TypeScript `buildLargeCode` implementation in place so it runs faster while preserving its observable behavior, calling convention, and public API.

## Workspace

- `/app/subject.ts` — authoritative TypeScript source containing the `buildLargeCode` entry point.
- `/app/serve.cjs` — launcher used to expose the compiled entry point.
- `/app/run.sh` — JSON-lines service used by the harness to call the subject.
- `/app/task-interface.json` — task interface metadata.
- `/app` — build directory and output location.

## Build & Test

Build the TypeScript implementation from `/app` with:

```sh
tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts
```

This compiles `/app/subject.ts` to the JavaScript consumed by the launcher.

No self-check command is supplied. Inspect the source and available project-native checks before making changes. The harness calls the subject through `/app/run.sh`; its JSON-lines request envelope is only the invocation mechanism, not behavior under test.

Correctness is checked first against the frozen corpus, and execution speed is measured only after correctness passes. The graded corpus includes semantic-prefix, boundary, and malformed-input cases. The implementation currently present in `/app/subject.ts` is the normative reference for the expected behavior of those cases; it is runnable and can be compared with the optimized implementation.

## Constraints

**What you CAN do**

- Modify the implementation in `/app/subject.ts` to reduce runtime cost and unnecessary allocations.
- Remain in TypeScript and preserve the `buildLargeCode` positional calling convention with its float parameter.
- Use equivalent control flow, local caching, preallocation, loop optimizations, and other implementation-level changes when they preserve all observable results.
- Compare the optimized implementation with the existing implementation across representative normal, prefix, boundary, and malformed-input calls before relying on performance measurements.

**What you CANNOT do**

- Do not change the `buildLargeCode` public API, parameter order, return shape, or observable behavior.
- Do not replace the implementation with another language or move the task outside TypeScript.
- Do not assume that malformed or boundary inputs may be rejected, normalized, or handled differently; match the current implementation, which is the normative reference.
- Do not alter `/app/run.sh`, the launcher protocol, or unrelated entry points as a substitute for optimizing `buildLargeCode`.
- Do not add diagnostics to the JSON-lines response stream or treat the request/response envelope as part of the function’s graded behavior.
- Do not invent numerical tolerances or require bitwise-equal floating-point results beyond the verifier’s existing comparison policy.

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

