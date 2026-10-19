# Coding Life Game Logic Optimization

## Task Facts

* **Scale:** `package`
* **Task form:** in-place performance refactoring
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `Event`, `default`, `App`, `Talent`, `Life`, `Property`, `Achievement`, `checkCondition`, `extractMaxTriggers`, `summary`, `getRate`, `getGrade`, `clone`, `max`, `min`, `sum`, `average`, `map`
* **Delivered source paths:** `/app/README.md`, `/app/package.json`, `/app/run.sh`, `/app/task-interface.json`, `/app/lib/dom-to-image.min.js`, `/app/life_restart/webpack.config.cjs`, `/app/public/bundle.js`, `/app/repl/app.js`, `/app/src/achievement.js`, `/app/utils/verifyCondition.js`, `/app/view/sw.js`, `/app/life_restart/docs/bundle.js`, `/app/life_restart/lib/dom-to-image.min.js`, `/app/life_restart/public/bundle.js`, `/app/life_restart/repl/app.js`, `/app/life_restart/src/achievement.js`, `/app/life_restart/test/index.js`, `/app/life_restart/utils/verifyCondition.js`, `/app/life_restart/view/sw.js`, `/app/src/data/achievements.js`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Optimize the existing JavaScript package in place for faster execution while preserving the observable behavior and public API of all exposed operations.

## Workspace

- `/app/subject.cjs` defines the `entry` symbol used by the harness and dispatches package operations.
- `/app/serve.cjs` provides the JSON-lines service that loads and calls `entry`.
- `/app/run.sh` launches the service from `/app`.
- `/app/task-interface.json` describes the task interface.
- `/app/package.json` contains the package metadata and available project scripts.
- `/app/src/` contains the primary JavaScript implementation.
- `/app/src/event.js`, `/app/src/app.js`, `/app/src/talent.js`, `/app/src/life.js`, `/app/src/property.js`, and `/app/src/achievement.js` implement the exposed game components.
- `/app/src/functions/condition.js` implements `checkCondition` and `extractMaxTriggers`.
- `/app/src/functions/summary.js` implements `summary`.
- `/app/src/functions/addition.js` implements `getRate` and `getGrade`.
- `/app/src/functions/util.js` implements `clone`, `max`, `min`, `sum`, `average`, and `map`.
- `/app/src/data/` contains the game data consumed by the implementation.
- `/app/src/index.js` is the package source entry.
- `/app/webpack.config.cjs` is the primary bundler configuration.
- `/app/life_restart/` contains a parallel project tree, including source files and its own `/app/life_restart/webpack.config.cjs`.
- `/app/public/bundle.js` and `/app/life_restart/public/bundle.js` are generated browser bundles; change build inputs rather than generated output unless the existing build process requires otherwise.

## Build & Test

No separate build command or project-native self-check command was supplied. The launcher performs any required build preparation. Inspect `/app/package.json`, the source, and existing project files for available checks before making changes; do not invent a test command.

The harness launches the implementation with `/app/run.sh` as a JSON-lines service. Requests call `entry`, with the first positional argument selecting one of the declared package operations. This protocol is only the invocation mechanism; grading observes the selected operation's result, not the request envelope or diagnostic behavior.

Correctness is checked before performance is measured. The frozen graded corpus contains 139 probes across all 18 operations: 111 valid cases, 18 boundary cases, and 10 error cases. The implementation initially present in the workspace is the normative reference for every case, including boundary and malformed-input behavior. Compare optimized behavior against that implementation rather than inventing expected outcomes.

## Constraints

**What you CAN do**

- Modify the existing JavaScript implementation and its build inputs under `/app`.
- Optimize all exposed operations collectively: `Event`, `default`, `App`, `Talent`, `Life`, `Property`, `Achievement`, `checkCondition`, `extractMaxTriggers`, `summary`, `getRate`, `getGrade`, `clone`, `max`, `min`, `sum`, `average`, and `map`.
- Reduce repeated parsing, allocation, cloning, property lookup, array traversal, and intermediate-array creation where equivalence is established.
- Cache immutable derived data or compiled condition representations when cache lifetime and keying preserve existing behavior.
- Replace expensive iteration patterns with tighter JavaScript loops when ordering, coercion, sparse-array handling, mutation behavior, and exceptions remain unchanged.
- Optimize hot class initialization and game-state transitions while preserving instance shape and externally visible state.
- Use JavaScript runtime features already supported by the supplied Node invocation.
- Update `/app/subject.cjs`, `/app/run.sh`, or supporting implementation files when needed, provided the required `entry` interface and launcher behavior remain intact.

**What you CANNOT do**

- Change observable behavior for valid, boundary, or error inputs; the original implementation is the behavioral reference.
- Change the public API, operation names, calling conventions, return structures, mutation behavior, error behavior, or operation availability.
- Reduce the task to optimizing only `entry`; `entry` is the dispatch point, while all 18 exposed package operations are in scope.
- Rewrite the implementation in another language; the solution must remain JavaScript.
- Remove support for any declared operation, including both `Event` and the `default` export from `/app/src/event.js`.
- Introduce caches that expose shared mutable state, return stale results, alter object identity where observable, or allow one request to affect another unexpectedly.
- Assume algebraically equivalent rewrites are behaviorally equivalent when JavaScript coercion, `NaN`, infinities, signed zero, getters, sparse arrays, or exception timing may differ.
- Change generated assets or unrelated application behavior without a demonstrated need for the package optimization.
- Add dependency installation steps or rely on undeclared external executables.
- Emit diagnostics onto the JSON-lines response stream used by `/app/run.sh`.
- Invent benchmark thresholds, performance formulas, or correctness criteria beyond the supplied graded corpus.

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

We run **136 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **the value the call returned**

That is **136 graded observation(s)** in total.

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

