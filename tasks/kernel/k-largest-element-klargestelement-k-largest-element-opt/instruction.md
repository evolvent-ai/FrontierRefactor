# K Largest Element Klargestelement K Largest Element Optimization

## Task Facts

* **Scale:** `kernel`
* **Task form:** in-place performance refactoring
* **Source language:** `typescript`
* **Workspace:** `/app`
* **Entry point:** `kLargestElement`
* **Factory dispatch marker:** `serve kLargestElement`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/serve.cjs`, `/app/subject.ts`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `sh -c 'tsc --target ES2022 --module commonjs --skipLibCheck --allowJs $(find . -name '"'"'*.ts'"'"' -not -path '"'"'./node_modules/*'"'"' -not -name '"'"'*.d.ts'"'"' 2>/dev/null) ./subject.ts || tsc --target ES2022 --module commonjs --skipLibCheck ./subject.ts'`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Improve the runtime performance of the existing TypeScript `kLargestElement` function in place without changing its public API or observable behavior.

## Workspace

- `/app` — build directory; run all commands from here.
- `/app/subject.ts` — authoritative implementation source containing the `kLargestElement` entry point.
- `/app/serve.cjs` — launcher used by the harness to load `subject.js` and invoke `kLargestElement`.
- `/app/run.sh` — JSON-lines service entry used by the harness.
- `/app/task-interface.json` — task interface configuration.
- `/app/subject.js` — generated CommonJS output expected by the launcher after compilation.

## Build & Test

From `/app`, compile the TypeScript implementation and supporting TypeScript files with:

```sh
sh -c 'tsc --target ES2022 --module commonjs --skipLibCheck --allowJs $(find . -name '"'"'*.ts'"'"' -not -path '"'"'./node_modules/*'"'"' -not -name '"'"'*.d.ts'"'"' 2>/dev/null) ./subject.ts || tsc --target ES2022 --module commonjs --skipLibCheck ./subject.ts'
```

The harness invokes the built subject through `/app/run.sh` as a JSON-lines service. Requests use `op="run"`, `call="entry"`, and an `args` array of positional arguments; this protocol is only the invocation mechanism, not behavior under test.

No project-native self-check command was supplied. Inspect `/app/subject.ts` and the other listed workspace files for any available checks instead of inventing one. The frozen harness checks correctness automatically and measures speed only after the implementation passes correctness checks.

## Constraints

**What you CAN do**

- Modify the existing TypeScript implementation of `kLargestElement` in `/app/subject.ts`.
- Optimize the selected computation using more efficient selection algorithms, tighter loops, reduced allocation, or less sorting where those changes preserve all existing results and side effects.
- Reuse storage or mutate data only if the current implementation's observable behavior, including any input mutation behavior, remains unchanged.
- Add private TypeScript helpers or internal data structures when they improve performance without changing the exported API.
- Use ES2022 and built-in JavaScript or TypeScript facilities available in the supplied build environment.
- Compare candidate floating-point results using the supplied policy: `abs(candidate - reference) <= 1e-12 + 1e-9 * abs(reference)`.
- Preserve exact integer values, booleans, strings, field names, and array shapes. Preserve infinity signs and positions; `NaN` is accepted only where the reference also returns `NaN`.
- Use the implementation initially present in `/app/subject.ts` as the normative reference. The graded corpus includes semantic-prefix, boundary, and malformed-input cases for `float_array` and `float` arguments; establish their expected behavior by comparing against that runnable reference without assuming or inventing outcomes.

**What you CANNOT do**

- Change the observable behavior of `kLargestElement`, including behavior for boundary or malformed inputs.
- Change the `kLargestElement` name, parameter convention, return contract, exports, or other public API details.
- Rewrite the implementation in another language; this is an in-place TypeScript optimization.
- Replace floating-point behavior with a contract requiring bitwise equality or a different numerical tolerance.
- Add required package operations or external dependencies; no package operations are declared for this task.
- Change `/app/run.sh`, `/app/serve.cjs`, or the JSON-lines invocation contract in a way that prevents the harness from loading `subject.js` and calling `kLargestElement`.
- Emit diagnostics to the JSON-lines response stream.
- Optimize only for typical valid inputs while disregarding the graded semantic-prefix, boundary, or malformed-input cases.

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

