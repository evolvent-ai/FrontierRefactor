# Diff Diffatcaret Diff At Caret Optimization

## Task Facts

* **Scale:** `module`
* **Task form:** in-place performance refactoring
* **Source language:** `typescript`
* **Workspace:** `/app`
* **Entry point:** `diffAtCaret`
* **Factory dispatch marker:** `serve diffAtCaret`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/serve.cjs`, `/app/subject.ts`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `sh -c 'tsc --target ES2022 --module commonjs --skipLibCheck --allowJs $(find . -name '"'"'*.ts'"'"' -not -path '"'"'./node_modules/*'"'"' -not -name '"'"'*.d.ts'"'"' 2>/dev/null) ./subject.ts || tsc --target ES2022 --module commonjs --skipLibCheck ./subject.ts'`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream.

Improve the runtime performance of the existing TypeScript `diffAtCaret` function in place while preserving its observable behavior, public API, and calling convention.

## Workspace

- `/app/subject.ts` — entry source containing the `diffAtCaret` implementation.
- `/app/run.sh` — JSON-lines service launcher used to invoke the entry point.
- `/app/serve.cjs` — service runtime used by the launcher.
- `/app/task-interface.json` — task interface metadata.
- `/app` — build directory and location for implementation and generated build inputs.
- Entry point: `diffAtCaret`, called with `(string, string, float)` arguments.

## Build & Test

Build the TypeScript source from `/app` with the supplied fallback compilation command:

```sh
sh -c 'tsc --target ES2022 --module commonjs --skipLibCheck --allowJs $(find . -name '"'"'*.ts'"'"' -not -path '"'"'./node_modules/*'"'"' -not -name '"'"'*.d.ts'"'"' 2>/dev/null) ./subject.ts || tsc --target ES2022 --module commonjs --skipLibCheck ./subject.ts'
```

Start the project-native JSON-lines service for a local invocation check:

```sh
/app/run.sh
```

The service accepts requests containing an `id`, `op: "run"`, `call: "entry"`, and positional `args`, and returns the corresponding result object. This envelope is only the harness mechanism; grading observes the result produced by `diffAtCaret`.

No separate self-check command is supplied. Inspect `/app/subject.ts` for any available project-native checks before making changes. Correctness is checked first against the frozen corpus, and performance is measured only after the implementation passes correctness checks.

The graded probe contract includes semantic-prefix, boundary, and malformed-input cases. The implementation already present in the workspace is the normative reference for the expected behavior of every case; it is runnable and can be compared with the optimized implementation. Do not infer or replace those outcomes.

## Constraints

**What you CAN do**

- Optimize the implementation of `diffAtCaret` in `/app/subject.ts` while keeping the existing TypeScript toolchain and function signature.
- Reduce allocations, repeated string processing, or unnecessary scans when doing so preserves results for all valid and malformed inputs.
- Use TypeScript and standard JavaScript string operations compatible with the supplied ES2022 CommonJS build.
- Inspect the existing implementation and compare optimized results with the runnable normative implementation across semantic-prefix, boundary, and malformed-input inputs.
- Modify implementation and necessary build inputs under `/app` while preserving the service entry point and invocation convention.

**What you CANNOT do**

- Do not change the public API, including the `diffAtCaret` symbol, its positional argument order, or its `(string, string, float)` parameter kinds.
- Do not change observable behavior, including behavior for semantic-prefix, boundary, or malformed-input cases in the graded corpus.
- Do not rewrite the task into another language or replace the TypeScript implementation with a different runtime or external operation.
- Do not change the JSON-lines service contract, entry-point dispatch, command-line behavior, or filesystem behavior used to call the subject.
- Do not add dependency installation steps or rely on unavailable packages.
- Do not invent benchmark thresholds, accuracy bounds, or alternate expected outcomes.
- Do not treat the request/response envelope or diagnostic handling as subject behavior under test.

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

