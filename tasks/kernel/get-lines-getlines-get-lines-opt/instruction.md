# Get Lines Getlines Get Lines Optimization

## Task Facts

* **Scale:** `kernel`
* **Task form:** in-place performance refactoring
* **Source language:** `typescript`
* **Workspace:** `/app`
* **Entry point:** `getLines`
* **Factory dispatch marker:** `serve getLines`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/subject.ts`, `/app/serve.cjs`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Improve the runtime performance of the TypeScript `getLines` computation in place while preserving its observable behavior and public API; this is not a cross-language rewrite.

## Workspace

- `/app/subject.ts`: TypeScript implementation containing the `getLines` entry point.
- `/app/task-interface.json`: task interface configuration for the selected symbol and invocation.
- `/app/serve.cjs`: launcher used to expose `getLines` through the harness.
- `/app/run.sh`: JSON-lines service entry point.
- `/app`: build directory; the supplied TypeScript build emits JavaScript here.

## Build & Test

Compile the TypeScript implementation from `/app` with:

```sh
tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts
```

Start the supplied JSON-lines service from `/app` with:

```sh
/app/run.sh
```

The service accepts harness requests for the `getLines` entry point. No separate self-check command is supplied; inspect `/app/subject.ts` for available project-native checks. Correctness is checked first against the frozen corpus, and speed is measured only after correctness passes. The graded corpus includes semantic-prefix, boundary, and malformed-input cases. The existing implementation is the normative reference for the expected result of each case.

## Constraints

**What you CAN do**

- Optimize the implementation in `/app/subject.ts` while keeping `getLines` callable with its existing two-parameter convention: a string and a float array.
- Use TypeScript and JavaScript runtime techniques such as reducing allocations, avoiding repeated scans or conversions, simplifying hot loops, and reusing computed values where behavior remains unchanged.
- Build with the supplied ES2022 CommonJS command and keep generated build inputs under `/app`.
- Preserve the existing handling of normal, boundary, and malformed inputs exactly as established by the current implementation.

**What you CANNOT do**

- Do not change the `getLines` public API, parameter order, parameter kinds, return shape, or observable behavior.
- Do not rewrite the task in another language or replace the TypeScript implementation with a different entry point.
- Do not assume boundary or malformed-input outcomes; the current runnable implementation defines them, and those cases are graded.
- Do not require bitwise-identical floating-point results. Floating-point values are compared with `abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)`.
- Preserve exact integer values, booleans, strings, field names, and array shapes.
- Preserve infinities by sign and position, and preserve `NaN` at matching positions.
- Do not alter the harness request/response mechanism or use its JSON envelope as a substitute for preserving the subject function's behavior.

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

