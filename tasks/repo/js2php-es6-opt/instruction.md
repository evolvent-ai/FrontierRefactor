# Js2php Es6 Optimization

## Task Facts

* **Scale:** `repo`
* **Task form:** in-place performance refactoring
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Observed invocation:** `node /app/js2php`
* **Delivered source paths:** `/app/README.md`, `/app/package.json`, `/app/run.sh`, `/app/task-interface.json`, `/app/core/array.js`, `/app/test/generate.js`, `/app/test/fixtures/anonymous_function.js`, `/app/core/date.js`, `/app/test/suite.js`, `/app/test/fixtures/array_index.js`, `/app/core/function.js`, `/app/test/fixtures/arrow_functions.js`, `/app/core/global.js`, `/app/test/fixtures/class.js`, `/app/core.js`, `/app/core/json.js`, `/app/test/fixtures/class_inheritance.js`, `/app/index.js`, `/app/core/math.js`, `/app/test/fixtures/closures.js`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Preparation commands:** `npm install`
* **Delivered interface:** The evaluator invokes /app/run.sh with the original program's arguments and standard input in a prepared working directory. Preserve argument handling, exit status, both output streams, and produced file contents. Keep the working directory supplied by the caller when interpreting relative input/output paths.

Improve the performance of the existing JavaScript ES6-to-PHP source-to-source transpiler in place while preserving its observable behavior and public API.

## Workspace

- `/app/js2php` — executable transpiler entry point, invocable with Node.js.
- `/app/index.js` — main JavaScript implementation.
- `/app/core.js` — core transpilation support.
- `/app/scope.js` and `/app/utils.js` — scope handling and shared utilities.
- `/app/core/array.js`, `/app/core/date.js`, `/app/core/function.js`, `/app/core/global.js`, `/app/core/json.js`, `/app/core/math.js`, `/app/core/number.js`, and `/app/core/string.js` — built-in and runtime translation support.
- `/app/run.sh` — evaluator-facing command wrapper. The evaluator invokes it with the original arguments and standard input.
- `/app/package.json` and `/app/package-lock.json` — Node.js project metadata and dependency lockfile.
- `/app/test/suite.js` and `/app/test/generate.js` — repository test and fixture tooling to inspect for available checks.
- `/app/test/fixtures/*.js` and corresponding `.php` files — repository-owned transpilation cases covering language constructs, core operations, errors, and failures.

## Build & Test

No build command or project-native self-check command is supplied. Inspect `/app/test/suite.js`, `/app/test/generate.js`, and the executable entry points for available checks rather than inventing a test command.

The supplied entry-point invocation is:

```sh
node /app/js2php
```

Use the caller-provided working directory when interpreting relative input and output paths. Correctness is checked first against the frozen workload; performance is measured only after the implementation remains behaviorally correct.

## Constraints

### What you CAN do

- Optimize the JavaScript implementation under `/app`, including algorithms, hot paths, allocation patterns, lookup structures, and repeated parsing or formatting work.
- Refactor internal modules while keeping their existing calling conventions and externally observable results.
- Use JavaScript and Node.js facilities already compatible with the project to reduce unnecessary work.
- Compare optimized output and execution behavior with the existing implementation before and after changes.
- Preserve repository-owned fixture coverage while improving throughput across the selected transpilation workload.

### What you CANNOT do

- Do not rewrite the implementation in another language; this is an in-place JavaScript optimization.
- Do not change the public API, command-line argument handling, standard input behavior, standard output or standard error, exit status, or produced file contents.
- Do not change the working-directory semantics for relative paths.
- Do not alter observable transpilation behavior, including handling of valid, unsupported, malformed, or failure cases represented by the repository fixtures.
- Do not replace `/app/run.sh` or `/app/js2php` with a different interface.
- Do not add assumptions about arguments, output formats, performance thresholds, or benchmark results that are not specified by the project.
- Keep all implementation changes within the supplied `/app` workspace and retain JavaScript as the implementation language.

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

We run **13 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **exit code**
* **stdout**
* **stderr**
* **the resulting directory**

That is **13 graded observation(s)** in total.

These expectations were not written by hand. The reference was run 5 times per probe and only what it reproduced *every single time* is graded -- anything it could not repeat, such as a timestamp or a temporary path, is excluded. You are never asked to reproduce something that is not reproducible.


## Performance Measurement

```
score = 0.5 + 0.5 x speedup      if every observation matches
score = 0.5 x (fraction matched)  otherwise
```

Correctness **unlocks** speed rather than being averaged with it: short of complete, no amount of speed helps. Partial correctness is still scored, so a submission that misses a few observations is worth repairing rather than abandoning.

Once every graded observation matches, and only then, your submission is timed against the reference on 3 workload(s) held out from grading. Your score rises with the measured speedup; there is no threshold to clear and no ceiling above which more speed stops counting. A difference too small to distinguish from the machine's own noise counts as no change.
