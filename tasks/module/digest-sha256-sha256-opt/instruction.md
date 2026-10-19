# Digest Sha256 Sha256 Optimization

## Task Facts

* **Scale:** `module`
* **Task form:** in-place performance refactoring
* **Source language:** `typescript`
* **Workspace:** `/app`
* **Entry point:** `sha256`
* **Factory dispatch marker:** `serve sha256`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/subject.ts`, `/app/serve.cjs`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream.

Improve the runtime performance of the existing TypeScript `sha256` function in place while preserving its observable behavior, calling convention, and public API; this is not a cross-language rewrite.

## Workspace

- [`/app/subject.ts`](/app/subject.ts): TypeScript source containing the `sha256` entry point.
- [`/app/run.sh`](/app/run.sh): JSON-lines service launcher used to invoke the subject.
- [`/app/serve.cjs`](/app/serve.cjs): runtime dispatcher used by the launcher.
- [`/app/task-interface.json`](/app/task-interface.json): task interface metadata.
- `/app`: build directory and location for generated `subject.js`.

## Build & Test

Compile the TypeScript implementation from `/app`:

```sh
tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts
```

Run the project service from `/app`:

```sh
/app/run.sh
```

The service receives JSON-lines requests containing `id`, `op: "run"`, `call: "entry"`, and a positional `args` array. The invocation targets `sha256` with a single string parameter. No separate self-check command is supplied; inspect [`/app/subject.ts`](/app/subject.ts) for available checks before making changes.

Correctness is checked first against the frozen test suite, and speed is measured only after correctness passes. The graded probe corpus includes semantic-prefix, boundary, and malformed-input cases. The implementation currently present in the workspace is the normative reference for the expected result of each case; compare against its runnable behavior without assuming outcomes.

## Constraints

**What you CAN do**

- Optimize the implementation in [`/app/subject.ts`](/app/subject.ts) while keeping the `sha256` function's single-string calling convention unchanged.
- Use TypeScript and JavaScript runtime techniques that reduce allocations, repeated conversions, unnecessary branching, or other hot-path overhead.
- Build the implementation with the supplied TypeScript compiler command and keep generated build inputs under `/app`.

**What you CANNOT do**

- Do not change the `sha256` public API, parameter kind, return behavior, or observable behavior.
- Do not rewrite the implementation in another language or replace the TypeScript entry point.
- Do not alter the JSON-lines harness protocol or use it to define subject behavior; the harness is only the mechanism for invoking the function.
- Do not change unrelated files or add dependencies.
- Do not assume different results for semantic-prefix, boundary, or malformed-input strings; preserve the behavior of the existing runnable implementation.
- Do not add diagnostics to the service response stream or change the supplied launcher and runtime contract.

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

