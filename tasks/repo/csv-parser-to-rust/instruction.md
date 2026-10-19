# Csv Parser to Rust

## Task Facts

* **Scale:** `repo`
* **Task form:** cross-language reimplementation
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Observed invocation:** `node /app/bin/csv-parser`
* **Delivered source paths:** `/app/README.md`, `/app/package.json`, `/app/run.sh`, `/app/task-interface.json`, `/app/examples/transform.js`, `/app/test/byteOffset.test.js`, `/app/implementation/src/main.rs`, `/app/test/helpers/helper.js`, `/app/test/escape.test.js`, `/app/test/headers.test.js`, `/app/test/issues.test.js`, `/app/commitlint.config.js`, `/app/test/mapHeaders.test.js`, `/app/index.d.ts`, `/app/test/mapValues.test.js`, `/app/index.js`, `/app/test/maxRowBytes.test.js`, `/app/index.test-d.ts`, `/app/test/newline.test.js`, `/app/test/quote.test.js`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Preparation commands:** `npm install`
* **Delivered interface:** The target executable receives the original program's arguments and standard input in a prepared working directory. Preserve argument handling, exit status, both output streams, and produced file contents. Keep the working directory supplied by the caller when interpreting relative input/output paths. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation.

Reimplement the reference (javascript) in rust so that the observable behaviour is identical but the implementation is entirely in rust.

## Workspace

* `/app` — your working directory; everything you submit lives here

## Build & Test

Reference preparation commands recorded by the factory. They may install dependencies and are not necessarily available to the offline solver:

    npm install

No project-native self-check command was supplied. Inspect the available source and project configuration for a real test, sample invocation, or benchmark; the harness performs official grading automatically.

## Constraints

Treat the repository as an executable project. Preserve its command-line interface, exit statuses, standard output/error, produced files, and build/runtime entry points.

**What you CAN do**

* Rewrite the implementation in rust

**What you CANNOT do**

* Call or import the original javascript reference; stay in rust

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
