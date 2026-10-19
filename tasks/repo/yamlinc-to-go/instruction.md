# Yamlinc to Go

## Task Facts

* **Scale:** `repo`
* **Task form:** cross-language reimplementation
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Target language:** `go`
* **Observed invocation:** `node /app/bin/yamlinc`
* **Delivered source paths:** `/app/README.md`, `/app/package.json`, `/app/run.sh`, `/app/task-interface.json`, `/app/implementation/main.go`, `/app/src/helpers.js`, `/app/test/yamlinc-test.js`, `/app/src/yamlinc.js`, `/app/bin/yamlinc`, `/app/help/help.txt`, `/app/test/samples/merge2files-verify.yml`, `/app/implementation/go.mod`, `/app/test/samples/merge2files.yml`, `/app/test/samples/merge2files1.yml`, `/app/test/samples/merge2files2.yml`, `/app/LICENSE`, `/app/test/samples/sample1-include1.yml`, `/app/_config.yml`, `/app/test/samples/sample1-verify.yml`, `/app/build.sh`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Preparation commands:** `npm install`
* **Delivered interface:** The target executable receives the original program's arguments and standard input in a prepared working directory. Preserve argument handling, exit status, both output streams, and produced file contents. Keep the working directory supplied by the caller when interpreting relative input/output paths. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation.

Reimplement the JavaScript `yamlinc` executable in Go to compose YAML files through `$include` and split Swagger/OpenAPI definitions while preserving observable behavior and improving performance.

## Workspace

- `/app/implementation/main.go` — current Go implementation entry source and the primary target for the rewrite.
- `/app/implementation/go.mod` — Go module and build input; keep all Go implementation sources and build inputs under `/app/implementation`.
- `/app/src/yamlinc.js` — JavaScript reference implementation of YAML composition behavior.
- `/app/src/helpers.js` — JavaScript helper logic used by the reference implementation.
- `/app/bin/yamlinc` — JavaScript reference executable entry point.
- `/app/package.json` and `/app/package-lock.json` — original JavaScript project metadata.
- `/app/test/yamlinc-test.js` — repository test source describing project behavior.
- `/app/test/samples/` — repository-owned YAML fixtures, including `$include` compositions, case-variant YAML filenames, verification outputs, and Swagger/OpenAPI samples.
- `/app/run.sh` — development execution entry point.
- `/app/build.sh` — development build entry point.
- `/app/task-interface.json` — task interface metadata.
- `/app/README.md` and `/app/help/help.txt` — project usage and help documentation.

## Build & Test

Build the Go implementation from `/app` with:

```sh
/app/build.sh
```

This builds the target product using the repository's development build entry point. The evaluator independently builds sources under `/app/implementation` with its trusted offline Go toolchain and executes that product directly.

Run the project development entry point with:

```sh
/app/run.sh
```

Use it only as a local execution entry point; preserve the caller-provided working directory and original command-line arguments when implementing the graded executable. No dedicated self-check command is supplied. Inspect `/app/src/yamlinc.js`, `/app/bin/yamlinc`, and `/app/test/yamlinc-test.js` for available project-native checks and sample invocation details rather than inventing a new test command.

Correctness is checked before performance. The graded corpus contains 14 repository-owned scenarios and checks exit status, standard output, standard error, and produced file contents. The implementation already present in the workspace is the normative reference for each scenario; compare the Go executable with the runnable JavaScript reference to establish expected behavior before optimizing. Speed is measured only after the required behavior matches.

## Constraints

**What you CAN do**

- Replace or extend the implementation in `/app/implementation` with a Go implementation of the executable project.
- Use Go-native parsing, buffering, filesystem traversal, and in-memory data structures to reduce overhead while preserving YAML syntax, include resolution, output formatting, and file-writing behavior.
- Keep command-line argument handling, relative-path resolution, standard streams, exit statuses, and produced files equivalent to the JavaScript reference.
- Inspect the JavaScript source, documentation, and sample fixtures to reproduce supported `$include` composition and Swagger/OpenAPI splitting behavior.
- Keep required build inputs available under `/app/implementation` so the trusted offline toolchain can build the target without downloading dependencies.

**What you CANNOT do**

- Do not implement the solution in JavaScript or another language; the graded implementation must be Go and build from `/app/implementation`.
- Do not change observable behavior of the reference executable, including errors, diagnostics, output streams, exit codes, path handling, YAML serialization, or generated file contents.
- Do not assume only the visible sample files or successful inputs are exercised; the 14-case graded corpus includes the repository-owned boundary and malformed-input cases, whose expected behavior is defined by the runnable reference implementation.
- Do not rely on network access, `npm install`, runtime JavaScript dependencies, or unavailable external services in the Go build.
- Do not treat `/app/run.sh` or `/app/build.sh` as the graded product or replace them instead of providing buildable Go sources under `/app/implementation`.
- Do not write outputs to fixed absolute paths or otherwise disregard the working directory supplied by the caller.
- Do not remove or bypass file production required by the original command-line operation.

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

We run **11 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **exit code**
* **stdout**
* **stderr**
* **the resulting directory**

That is **11 graded observation(s)** in total.

These expectations were not written by hand. The reference was run 5 times per probe and only what it reproduced *every single time* is graded -- anything it could not repeat, such as a timestamp or a temporary path, is excluded. You are never asked to reproduce something that is not reproducible.


## Performance Measurement

```
score = 0.5 + 0.5 x speedup      if every observation matches
score = 0.5 x (fraction matched)  otherwise
```

Correctness **unlocks** speed rather than being averaged with it: short of complete, no amount of speed helps. Partial correctness is still scored, so a submission that misses a few observations is worth repairing rather than abandoning.

Once every graded observation matches, and only then, your submission is timed against the reference on 3 workload(s) held out from grading. Your score rises with the measured speedup; there is no threshold to clear and no ceiling above which more speed stops counting. A difference too small to distinguish from the machine's own noise counts as no change.
