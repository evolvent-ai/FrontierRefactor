# Yamlfmt Files Optimization

## Task Facts

* **Scale:** `repo`
* **Task form:** in-place performance refactoring
* **Source language:** `go`
* **Workspace:** `/app`
* **Observed invocation:** `/app/yamlfmt`
* **Delivered source paths:** `/app/Makefile`, `/app/README.md`, `/app/go.mod`, `/app/go.sum`, `/app/run.sh`, `/app/task-interface.json`, `/app/cmd/yamlfmt/config.go`, `/app/cmd/yamlfmt/flags.go`, `/app/cmd/yamlfmt/main.go`, `/app/command/command.go`, `/app/engine/consecutive_engine.go`, `/app/formatters/basic/config.go`, `/app/formatters/kyaml/factory.go`, `/app/integrationtest/command/command_test.go`, `/app/internal/assert/assert.go`, `/app/internal/collections/errors.go`, `/app/internal/features/eof_newline.go`, `/app/internal/gitlab/codequality.go`, `/app/internal/hotfix/retain_line_break.go`, `/app/internal/jsonschema/schema_test.go`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Preparation commands:** `go build -o /app/yamlfmt ./cmd/yamlfmt`
* **Delivered interface:** The evaluator invokes /app/run.sh with the original program's arguments and standard input in a prepared working directory. Preserve argument handling, exit status, both output streams, and produced file contents. Keep the working directory supplied by the caller when interpreting relative input/output paths.

Improve the runtime performance of the existing Go `yamlfmt` executable in place without changing its command-line, filesystem, output, error, exit-status, or public API behavior.

## Workspace

- `/app/cmd/yamlfmt/`: executable entry point in `main.go`, with command configuration in `config.go` and flag handling in `flags.go`.
- `/app/run.sh`: evaluator entry point; it invokes the program with the original arguments and standard input.
- `/app/command/`: command execution and integration behavior in `command.go` and its tests.
- `/app/engine.go` and `/app/engine/`: formatting orchestration, output handling, and error behavior.
- `/app/formatters/basic/`: primary formatter implementation, configuration, features, and tests.
- `/app/formatters/kyaml/`: kyaml formatter factory and implementation.
- `/app/pkg/yaml/`: YAML parsing, encoding, emitting, scanning, resolving, sorting, and related tests.
- `/app/content_analyzer.go`, `/app/path_collector.go`, and `/app/formatter.go`: input analysis, path selection, and formatter interfaces.
- `/app/go.mod` and `/app/go.sum`: Go module and dependency definitions.
- `/app/integrationtest/` and the package-level `*_test.go` files: available project-native correctness checks and behavior coverage.
- `harvest-inputs.tar.gz`: supplied workload fixtures. The graded corpus contains 15 scenarios exercised through `/app/run.sh`; preserve produced files and both output streams for these repository-owned cases.

## Build & Test

Build the executable from `/app` with:

```sh
go build -o /app/yamlfmt ./cmd/yamlfmt
```

No self-check command was supplied. Inspect the Go tests and integration-test code for an appropriate project-native correctness check before relying on the optimization. The harness checks correctness first against the existing implementation and then measures speed; do not trade observable behavior for a faster path.

## Constraints

**What you CAN do**

- Optimize the existing Go implementation in `/app`, especially YAML parsing, formatting, scanning, encoding, file traversal, and repeated allocation or copying on the exercised paths.
- Use Go-appropriate techniques such as reducing allocations, reusing buffers or intermediate state where ownership permits, avoiding redundant parsing or formatting passes, and improving hot-loop data structures.
- Add internal helpers, benchmarks, tests, or implementation details without changing public API signatures or calling conventions.
- Profile or inspect the supplied workload and compare optimized behavior with the current implementation before finalizing changes.
- Preserve the caller-provided working directory when resolving relative input and output paths.

**What You CANNOT do**

- Do not change observable behavior for any supported command-line or filesystem case, including arguments, standard output, standard error, exit status, file contents, file creation or modification behavior, formatting options, error handling, and YAML edge cases.
- Do not change the public API or the command-line interface.
- Do not rewrite the project in another language; the implementation must remain Go.
- Do not replace `/app/run.sh` or bypass its argument and standard-input contract.
- Do not remove or weaken handling for malformed, boundary, or unusual YAML inputs in the graded corpus; the implementation already present in the workspace is the normative reference for the expected result of each case.
- Do not introduce dependency or environment requirements that are unavailable to the prepared build, and do not assume dependency installation is available offline.
- Do not modify repository-owned fixtures or use benchmark-specific shortcuts that fail on general inputs.

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

We run **12 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **exit code**
* **stdout**
* **stderr**
* **the resulting directory**

That is **12 graded observation(s)** in total.

These expectations were not written by hand. The reference was run 5 times per probe and only what it reproduced *every single time* is graded -- anything it could not repeat, such as a timestamp or a temporary path, is excluded. You are never asked to reproduce something that is not reproducible.


## Performance Measurement

```
score = 0.5 + 0.5 x speedup      if every observation matches
score = 0.5 x (fraction matched)  otherwise
```

Correctness **unlocks** speed rather than being averaged with it: short of complete, no amount of speed helps. Partial correctness is still scored, so a submission that misses a few observations is worth repairing rather than abandoning.

Once every graded observation matches, and only then, your submission is timed against the reference on 3 workload(s) held out from grading. Your score rises with the measured speedup; there is no threshold to clear and no ceiling above which more speed stops counting. A difference too small to distinguish from the machine's own noise counts as no change.
