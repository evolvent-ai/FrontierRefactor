# Color Rgba Rgba Optimization

## Task Facts

* **Scale:** `module`
* **Task form:** in-place performance refactoring
* **Source language:** `typescript`
* **Workspace:** `/app`
* **Entry point:** `rgba`
* **Factory dispatch marker:** `serve rgba`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/subject.ts`, `/app/serve.cjs`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream.

Improve the runtime performance of the existing TypeScript `rgba` function in place while preserving its observable behavior, public API, and positional calling convention; this is not a cross-language rewrite.

## Workspace

- [`/app/subject.ts`](/app/subject.ts): authoritative TypeScript implementation containing the `rgba` entry point.
- [`/app/run.sh`](/app/run.sh): JSON-lines service used by the harness to invoke the subject.
- [`/app/serve.cjs`](/app/serve.cjs): supplied launcher used with the compiled subject.
- [`/app/task-interface.json`](/app/task-interface.json): task interface metadata and invocation contract.
- `/app`: build directory and location for the implementation and generated build inputs.

## Build & Test

Build the TypeScript implementation from `/app` with:

```sh
tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts
```

Run the supplied launcher with:

```sh
node --experimental-specifier-resolution=node ./serve.cjs subject.js rgba
```

The launcher communicates through the supplied JSON-lines service. No separate self-check command is provided; inspect `/app/subject.ts` and the available launcher behavior for project-native checks. The harness checks correctness first and measures speed only after the optimized implementation matches the required behavior.

The graded probe contract includes semantic-prefix, boundary, and malformed-input cases for the string and float parameters. The implementation currently present in `/app/subject.ts` is the normative runnable reference for those cases; compare against it to establish expected behavior without inventing outcomes.

## Constraints

**What you CAN do**

- Optimize the implementation inside `/app/subject.ts` while keeping the `rgba` entry point available.
- Reduce allocations, repeated parsing, unnecessary conversions, and redundant branching where behavior remains unchanged.
- Use TypeScript and the existing ES2022/CommonJS build target.
- Preserve the function's handling of all accepted, boundary, and malformed inputs by comparing optimized results with the current implementation.
- Keep changes scoped to the selected `rgba` function and the supporting code required to optimize it.

**What you CANNOT do**

- Do not change the public API, positional calling convention, return shape, or observable behavior of `rgba`.
- Do not rewrite the implementation in another language.
- Do not remove or bypass semantic-prefix, boundary, or malformed-input behavior covered by the graded corpus.
- Do not alter `/app/run.sh` or the JSON-lines invocation mechanism to conceal behavioral differences.
- Do not add dependencies or require network access.
- Do not change unrelated workspace files or introduce repository-wide refactors.
- Do not assume floating-point outputs may be changed without checking the current implementation's observable results.

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

