# Scu Plus Course System Optimization

## Task Facts

* **Scale:** `package`
* **Task form:** in-place performance refactoring
* **Source language:** `typescript`
* **Workspace:** `/app`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `resolveAvatarRedirectUrl`, `mixWithWhite`, `normalizeAspectRatio`, `hideFailCourse`, `customText`
* **Delivered source paths:** `/app/README.md`, `/app/package.json`, `/app/run.sh`, `/app/task-interface.json`, `/app/scu-plus/update_and_push_tag.py`, `/app/src/background.ts`, `/app/scu-plus/src/background.ts`, `/app/scu-plus/tests/safari-update.test.mjs`, `/app/src/common/avatar.ts`, `/app/src/constants/actions.ts`, `/app/src/contents/id-scu.ts`, `/app/src/script/config.ts`, `/app/scu-plus/src/common/avatar.ts`, `/app/scu-plus/src/constants/actions.ts`, `/app/scu-plus/src/contents/id-scu.ts`, `/app/scu-plus/src/script/config.ts`, `/app/src/features/beautify/index.ts`, `/app/src/features/course-evaluation/index.ts`, `/app/src/features/course-filter/index.ts`, `/app/src/features/course-table/ics.ts`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `sh -c 'if [ -f package.json ] && grep -q '"'"'"type"[[:space:]]*:[[:space:]]*"module"'"'"' package.json; then sed -i '"'"'s/"type"[[:space:]]*:[[:space:]]*"module"/"type": "commonjs"/'"'"' package.json; echo '"'"'[build] package.json declared type=module; set to commonjs to match the CommonJS tsc emits'"'"'; fi; tsc --target ES2022 --module commonjs --skipLibCheck --allowJs $(find . -name '"'"'*.ts'"'"' -not -path '"'"'./node_modules/*'"'"' -not -name '"'"'*.d.ts'"'"' 2>/dev/null) ./subject.cts || tsc --target ES2022 --module commonjs --skipLibCheck ./subject.cts'`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Optimize the existing TypeScript package in place to improve the runtime performance of all five exposed operations while preserving their observable behavior and public API.

## Workspace

- `/app/subject.cts`: harness entry source exporting the `entry` symbol and dispatching calls to the package operations.
- `/app/src/common/avatar.ts`: implementation of `resolveAvatarRedirectUrl(avatarSource: string, avatarInfo: string)`.
- `/app/src/features/beautify/palette.ts`: implementation of `mixWithWhite(hex: string, ratio: number)`.
- `/app/src/features/ocr/model.ts`: implementation of `normalizeAspectRatio(ar: number)`.
- `/app/src/features/homepage/index.ts`: implementations of `hideFailCourse(enabled: boolean)` and `customText(id: string, text: string)`.
- `/app/src`: primary TypeScript source tree and the main optimization target.
- `/app/scu-plus/src`: additional copy of the package source present in the workspace; inspect how it relates to `/app/src` before deciding whether corresponding changes are required.
- `/app/package.json`: package configuration.
- `/app/task-interface.json`: description of the harness interface and exposed operations.
- `/app/run.sh`: JSON-lines service launcher used by the harness.
- `/app/README.md`: project documentation and potential project-native validation guidance.

## Build & Test

From `/app`, build the TypeScript sources and `/app/subject.cts` with the supplied command:

```sh
sh -c 'if [ -f package.json ] && grep -q '"'"'"type"[[:space:]]*:[[:space:]]*"module"'"'"' package.json; then sed -i '"'"'s/"type"[[:space:]]*:[[:space:]]*"module"/"type": "commonjs"/'"'"' package.json; echo '"'"'[build] package.json declared type=module; set to commonjs to match the CommonJS tsc emits'"'"'; fi; tsc --target ES2022 --module commonjs --skipLibCheck --allowJs $(find . -name '"'"'*.ts'"'"' -not -path '"'"'./node_modules/*'"'"' -not -name '"'"'*.d.ts'"'"' 2>/dev/null) ./subject.cts || tsc --target ES2022 --module commonjs --skipLibCheck ./subject.cts'
```

The launcher builds before starting the service. The harness invokes the supplied service command:

```sh
/app/run.sh
```

It sends JSON-lines requests to `entry`; the first positional argument selects one of `resolveAvatarRedirectUrl`, `mixWithWhite`, `normalizeAspectRatio`, `hideFailCourse`, or `customText`, and the remaining elements are that operation's arguments. This envelope is only the invocation mechanism, not behavior under test.

No project-native self-check command was supplied. Inspect `/app/package.json`, `/app/README.md`, and the source tree for available checks rather than inventing one. Automated grading first checks correctness against the frozen corpus and measures speed only after correctness passes.

## Constraints

**What you CAN do**

- Modify the existing TypeScript implementation and its build inputs under `/app` to reduce execution time.
- Optimize all exposed operations collectively; package coverage includes 15 `customText` probes, 2 `hideFailCourse` probes, 15 `mixWithWhite` probes, 13 `normalizeAspectRatio` probes, and 15 `resolveAvatarRedirectUrl` probes.
- Reduce repeated parsing, string allocation, regular-expression work, object creation, property lookup, and unnecessary DOM access where the existing behavior permits it.
- Hoist immutable constants, precompute reusable values, simplify hot control flow, and cache deterministic computations when cache lifetime and key semantics cannot change observable behavior.
- Use TypeScript and JavaScript runtime features supported by the supplied ES2022/CommonJS build.
- Refactor internal implementation details while preserving each operation's name, calling convention, return value, side effects, and error behavior.
- Use the implementation already present in the workspace as the normative reference. It is runnable and establishes the expected behavior for every graded case.

**What you CANNOT do**

- Do not change observable behavior or the public API of `entry` or any declared operation.
- Do not remove, rename, bypass, or alter the signatures of `resolveAvatarRedirectUrl`, `mixWithWhite`, `normalizeAspectRatio`, `hideFailCourse`, or `customText`.
- Do not rewrite the package in another language; this is an in-place TypeScript optimization, not a cross-language rewrite.
- Do not specialize the implementation to known probe values, hard-code outputs, or skip required side effects.
- Do not assume inputs are limited to ordinary valid examples. The 60-probe graded corpus explicitly includes 48 valid cases, 8 boundary cases, and 4 error cases; preserve the current implementation's exact behavior for all of them without inventing expected outcomes.
- Do not alter the JSON-lines dispatch contract required by `/app/run.sh`: requests call `entry`, the first argument selects the operation, and all declared operations must remain available.
- Do not treat request IDs, response envelopes, or diagnostic-stream handling as graded package behavior; grading observes the selected operations' own results.
- Do not introduce unsupported build requirements or depend on commands, services, or packages absent from the supplied workspace context.
- Do not claim new floating-point accuracy guarantees or require bitwise floating-point equality; no numerical comparison tolerance or NaN/Infinity policy was supplied beyond preserving the normative implementation's observable results.

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

