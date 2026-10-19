# Luhn Check Utils Createluhnmodulus Create Luhn Modulus Optimization

## Task Facts

* **Scale:** `kernel`
* **Task form:** in-place performance refactoring
* **Source language:** `typescript`
* **Workspace:** `/app`
* **Entry point:** `createLuhnModulus`
* **Factory dispatch marker:** `serve createLuhnModulus`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/subject.ts`, `/app/serve.cjs`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Improve the runtime performance of the TypeScript `createLuhnModulus` function in place while preserving its observable behavior and public API; this is not a cross-language rewrite.

## Workspace

- `/app/subject.ts`: TypeScript source containing the `createLuhnModulus` entry point.
- `/app/serve.cjs`: launcher used to expose the entry point for invocation.
- `/app/run.sh`: JSON-lines service used by the harness.
- `/app/task-interface.json`: task interface metadata.
- `/app`: build directory and location for the delivered implementation and generated build inputs.

## Build & Test

Build the TypeScript implementation from `/app` with:

```bash
tsc --target ES2022 --module commonjs --skipLibCheck --outDir . ./subject.ts
```

This compiles `subject.ts` to CommonJS output in `/app`.

Run the project service with:

```bash
/app/run.sh
```

The service accepts JSON-lines requests using the supplied harness interface. No separate self-check command is supplied; inspect `/app/subject.ts` and the available project files for any source-level checks. The harness automatically runs the frozen correctness suite and measures speed only after correctness passes.

The graded probe contract includes semantic prefix, boundary, and malformed-input cases. The implementation currently present in `/app/subject.ts` is the normative runnable reference for the expected behavior of those cases; compare the optimized implementation against it without assuming or inventing outcomes.

For floating-point results, the harness accepts:

`abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)`

Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match by sign and position, and `NaN` is accepted only at matching positions.

## Constraints

**What you CAN do**

- Optimize the implementation of `createLuhnModulus` in `/app/subject.ts` while keeping its existing calling convention.
- Reduce allocations, repeated conversions, redundant branching, and unnecessary work in the Luhn modulus calculation where the resulting observable behavior remains unchanged.
- Use TypeScript and standard JavaScript/TypeScript runtime operations appropriate for the existing ES2022 CommonJS build.
- Preserve the function's handling of float-array inputs, including semantic prefixes, boundaries, malformed values, infinities, and `NaN`, by checking behavior against the existing implementation.
- Keep changes focused on the selected kernel and retain compatibility with the supplied launcher and service.

**What you CANNOT do**

- Do not change the public API, function signature, calling convention, or entry symbol `createLuhnModulus`.
- Do not change observable behavior for any valid, boundary, prefix, malformed-input, `NaN`, or infinity case.
- Do not rewrite the task in another language; the implementation must remain TypeScript.
- Do not modify the JSON-lines harness protocol or treat its request/response envelope as subject behavior under test.
- Do not add diagnostic output to the service response stream.
- Do not replace the selected function with a different operation, alter unrelated workspace behavior, or require new commands not supplied in the task context.
- Do not demand bitwise floating-point equality; follow the supplied tolerance and exact structure/type rules.

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

