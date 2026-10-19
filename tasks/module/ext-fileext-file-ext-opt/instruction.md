# Ext Fileext File Ext Optimization

## Task Facts

* **Scale:** `module`
* **Task form:** in-place performance refactoring
* **Source language:** `typescript`
* **Workspace:** `/app`
* **Entry point:** `fileExt`
* **Factory dispatch marker:** `serve fileExt`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/subject.ts`, `/app/serve.cjs`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream.

Improve the runtime performance of the `fileExt` function in place while preserving its observable behavior, public API, and TypeScript implementation.

## Workspace

- `/app/subject.ts`: TypeScript source containing the `fileExt` entry point.
- `/app/serve.cjs`: launcher used to load the compiled subject and dispatch calls to `fileExt`.
- `/app/run.sh`: JSON-lines service entry point used by the harness.
- `/app/task-interface.json`: task interface metadata.

## Build & Test

Build the TypeScript implementation from `/app` with:

```sh
tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts
```

This emits the JavaScript used by the launcher.

No standalone self-check command is supplied. Inspect `/app/subject.ts` for available project-native checks. The harness calls `/app/run.sh` through its JSON-lines interface; the request envelope is only the mechanism for invoking the subject, and the graded observations are `fileExt` results.

Correctness is checked before performance is measured. The graded corpus includes semantic-prefix, boundary, and malformed-input cases for the string parameter. The implementation already present in the workspace is the normative reference for the expected result of each case; compare against it before and after the optimization.

## Constraints

**What you CAN do**

- Optimize the implementation of `fileExt` in `/app/subject.ts` while retaining its existing string calling convention.
- Use TypeScript and standard JavaScript string operations or other local logic that reduces allocations, scanning, or repeated work.
- Inspect the existing implementation and use targeted comparisons against its results across normal, semantic-prefix, boundary, and malformed-input inputs.
- Keep changes local to the selected function unless a supporting change is required to preserve its existing behavior.

**What you CANNOT do**

- Do not change the public API, function signature, return type, or calling convention of `fileExt`.
- Do not change observable behavior for any string input, including semantic-prefix, boundary, or malformed-input cases.
- Do not rewrite the task in another language or replace the TypeScript implementation with an external dependency or service.
- Do not modify the JSON-lines harness protocol, launcher behavior, request dispatch, or response envelope.
- Do not treat the internal `serve` dispatch marker as an executable command.
- Do not add unrelated repository-wide changes or alter files outside the supplied workspace unless required to build the implementation.

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

