# Tembo Rendering Engine Optimization

## Task Facts

* **Scale:** `package`
* **Task form:** in-place performance refactoring
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `render`, `getId`, `setId`, `appendChild`, `removeChild`, `replaceChild`, `createText`, `createElement`, `TreeNode`, `TextNode`, `setProp`, `getChildren`, `getText`, `setText`, `isText`, `setDOM`, `getID`, `setID`, `insertChild`, `isElement`, `isNative`, `differentTypes`, `differentPatch`, `clone`, `merge`
* **Delivered source paths:** `/app/README.md`, `/app/package.json`, `/app/run.sh`, `/app/task-interface.json`, `/app/src/Tembo.js`, `/app/tambo/Gruntfile.js`, `/app/example/react/react.js`, `/app/src/core/Tembo.core.can.js`, `/app/src/interface/Component.js`, `/app/src/render/NativeRoot.js`, `/app/src/renderers/Blessed.js`, `/app/src/updaters/BatchUpdate.js`, `/app/tambo/src/Tembo.js`, `/app/tambo/tests/util.js`, `/app/tambo/example/react/react.js`, `/app/tambo/src/core/Tembo.core.can.js`, `/app/tambo/src/interface/Component.js`, `/app/tambo/src/render/NativeRoot.js`, `/app/tambo/src/renderers/Blessed.js`, `/app/tambo/src/updaters/BatchUpdate.js`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Improve the runtime performance of the JavaScript Tembo rendering-engine package in place while preserving every observable result, error behavior, calling convention, and public operation.

## Workspace

- `/app/subject.cjs`: delivered entry module exposing the `entry` symbol used by the harness.
- `/app/serve.cjs`: JSON-lines service launcher used to invoke `entry`.
- `/app/run.sh`: supplied launcher command for the subject service.
- `/app/src/renderers/`: renderer implementations, including:
  - `/app/src/renderers/Blessed.js`
  - `/app/src/renderers/DOM.js`
  - `/app/src/renderers/String.js`
  - `/app/src/renderers/Test.js`
- `/app/src/render/`: rendering and patch utilities, including:
  - `/app/src/render/util.js`
  - `/app/src/render/ShadowNode.js`
  - `/app/src/render/NativeRoot.js`
- `/app/src/interface/`: rendering interfaces, including `Component.js` and `Patch.js`.
- `/app/src/updaters/`: update implementations, including `BatchUpdate.js` and `SyncUpdate.js`.
- `/app/src/Tembo.js`: package-level implementation entry.
- `/app/package.json` and `/app/Gruntfile.js`: project configuration and build metadata.
- `/app/task-interface.json`: task interface metadata.
- `/app/README.md`: project documentation.
- `/app/tambo/`: related source and project files that may provide implementation context; keep changes scoped to the delivered implementation under `/app`.

The package surface graded through `entry` includes `render`, `getId`, `setId`, `appendChild`, `removeChild`, `replaceChild`, `createText`, `createElement`, `TreeNode`, `TextNode`, `setProp`, `getChildren`, `getText`, `setText`, `isText`, `setDOM`, `getID`, `setID`, `insertChild`, `isElement`, `isNative`, `differentTypes`, `differentPatch`, `clone`, and `merge`.

## Build & Test

Run the supplied launcher from `/app` to exercise the JSON-lines service. Each request uses `op: "run"`, `call: "entry"`, and an `args` array whose first element selects one declared package operation; the remaining elements are that operation's positional arguments.

```sh
/app/run.sh
```

No build commands or project-native self-check commands were supplied. Inspect the source and project configuration for available checks before making changes. The harness runs the frozen correctness and performance evaluation automatically: it checks correctness first, then measures speed only for behaviorally correct implementations.

The graded corpus contains 25 package operations with 200 probes across valid, boundary, and error cases. The implementation currently present in the workspace is the normative behavioral reference for those cases; compare optimized behavior against that runnable implementation without assuming or inventing outcomes for malformed or boundary inputs.

## Constraints

**What you CAN do**

- Modify the existing JavaScript implementation in `/app` in place.
- Optimize shared rendering, tree manipulation, patch comparison, cloning, merging, and renderer helper paths used by the exposed package operations.
- Reduce allocations, repeated property lookups, unnecessary traversals, and redundant conversions where the returned values and side effects remain unchanged.
- Use JavaScript-native techniques such as cached local references, appropriate loop forms, early exits that preserve evaluation order, and data structures already consistent with the implementation.
- Inspect related files under `/app/tambo` for historical or alternative implementation context, but validate any adopted change against the delivered `/app` implementation.
- Preserve the existing module format, service integration, and operation dispatch through `entry`.

**What you CANNOT do**

- Do not change the public API or remove, rename, reorder, or reinterpret any declared package operation.
- Do not change observable behavior, including return values, mutation and aliasing behavior, child ordering, property handling, identity behavior, error behavior, side effects, or evaluation order where it is observable.
- Do not rewrite the implementation in another language; the optimized implementation must remain JavaScript.
- Do not replace the package with a narrower implementation focused on only one operation or renderer.
- Do not alter the JSON-lines launcher contract, `/app/run.sh`, command-line behavior, or filesystem layout required by the harness.
- Do not add diagnostics to the service response stream or change how requests are dispatched to `entry`.
- Do not assume boundary or error probes are unimportant; they are part of the graded corpus and must continue to match the existing implementation.
- Do not add dependency installation or unrelated repository-wide refactors.
- Do not claim performance improvements by changing outputs, weakening correctness, or bypassing operations that the package exposes.

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

We run **197 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **the value the call returned**

That is **197 graded observation(s)** in total.

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

