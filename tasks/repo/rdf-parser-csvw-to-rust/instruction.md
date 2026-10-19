# Rdf Parser Csvw to Rust

## Task Facts

* **Scale:** `repo`
* **Task form:** cross-language reimplementation
* **Source language:** `javascript`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Observed invocation:** `node /app/bin/csvw-metadata.js`
* **Delivered source paths:** `/app/README.md`, `/app/package.json`, `/app/run.sh`, `/app/task-interface.json`, `/app/bin/csvw-metadata.js`, `/app/lib/CsvParser.js`, `/app/test/CsvParser.test.js`, `/app/implementation/src/main.rs`, `/app/lib/metadata/Metadata.js`, `/app/test/support/namespaces.js`, `/app/lib/MetadataBuilder.js`, `/app/test/ObjectParserTransform.test.js`, `/app/lib/metadata/RdfUtils.js`, `/app/lib/ObjectParserTransform.js`, `/app/test/csvw-metadata.test.js`, `/app/lib/metadata/TableSchema.js`, `/app/lib/namespace.js`, `/app/test/parseDateTime.test.js`, `/app/lib/metadata/index.js`, `/app/index.js`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Preparation commands:** `npm install`
* **Delivered interface:** The target executable receives the original program's arguments and standard input in a prepared working directory. Preserve argument handling, exit status, both output streams, and produced file contents. Keep the working directory supplied by the caller when interpreting relative input/output paths. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation.

Reimplement the JavaScript CSV on the Web parser in Rust for improved performance while preserving the reference program's observable behavior across all selected workloads.

## Workspace

- `/app/bin/csvw-metadata.js`: JavaScript command-line entry point and behavioral reference.
- `/app/lib/`: JavaScript parser implementation, including `CsvParser.js`, `MetadataBuilder.js`, `ObjectParserTransform.js`, `parseDateTime.js`, metadata models, RDF utilities, and namespace handling.
- `/app/implementation/src/main.rs`: Rust implementation entry source to replace or complete.
- `/app/implementation/Cargo.toml`: Rust build configuration and build inputs.
- `/app/build.sh`: development build entry point.
- `/app/run.sh`: development execution entry point.
- `/app/package.json`: JavaScript project configuration.
- `/app/task-interface.json`: task interface metadata.
- `/app/test/`: repository-owned reference tests and CSVW fixtures, including parser tests, metadata tests, RDF output cases, and malformed or boundary cases.
- `/app/test/support/`: CSV, metadata JSON, Turtle, and N-Triples fixtures used by the reference behavior.
- The selected workload contains 19 scenarios and uses `inputs.tar.gz`; preserve produced files and their contents for these repository-owned cases.

## Build & Test

Build the Rust target from `/app` with:

```sh
/app/build.sh
```

This builds the implementation using the repository's configured build entry point. The evaluator independently builds sources under `/app/implementation` with its trusted offline Rust toolchain and executes the resulting product directly.

The supplied JavaScript reference invocation is:

```sh
node /app/bin/csvw-metadata.js
```

Use it when inspecting reference behavior and comparing the Rust implementation. No dedicated self-check command is supplied; inspect the source and repository-owned tests and fixtures for additional project-native checks rather than inventing a test command. Correctness is evaluated first against the frozen scenarios; performance is measured only after the implementation satisfies the behavioral checks.

## Constraints

**What you CAN do**

- Replace the implementation under `/app/implementation` with a Rust implementation, including changes to `/app/implementation/src/main.rs`, `Cargo.toml`, and other build inputs required by the trusted offline toolchain.
- Use Rust's standard library and dependencies already available to the evaluator's offline toolchain.
- Implement CSV parsing, CSVW metadata handling, URI/template expansion, datatype and date-time processing, namespace resolution, and RDF serialization using efficient streaming and allocation-conscious data structures where compatible with reference behavior.
- Compare the Rust executable with the runnable JavaScript reference in `/app/bin/csvw-metadata.js` and the supporting modules under `/app/lib/` to establish expected behavior.
- Preserve the caller-provided working directory when resolving relative input and output paths.
- Keep command-line argument handling, standard input processing, standard output and standard error behavior, exit statuses, file creation, file contents, ordering, and formatting behavior equivalent to the reference.
- Treat all 19 selected scenarios as graded, including any boundary or malformed-input cases present in the corpus. The existing runnable reference implementation defines the expected result for each case.

**What you CANNOT do**

- Do not implement the solution in JavaScript or another language; the graded target must be a Rust implementation buildable from `/app/implementation`.
- Do not rely on `npm install`, network access, runtime JavaScript, or unavailable external services in the Rust build or executable.
- Do not replace `/app/run.sh` or `/app/build.sh` as a substitute for delivering the graded Rust sources; the evaluator builds and executes the target under `/app/implementation` directly.
- Do not change the command-line or filesystem contract, including argument passing, current-directory semantics, standard streams, exit status, or produced files.
- Do not assume that valid inputs are the only cases that matter; malformed and boundary cases in the selected workload are part of the graded corpus, and their behavior must match the reference without inventing alternative outcomes.
- Do not make unrelated repository-wide changes or alter reference fixtures and tests to accommodate the rewrite.
- Do not trade correctness for optimization: the evaluator establishes behavioral equivalence before measuring runtime performance.

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

We run **16 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **exit code**
* **stdout**
* **stderr**
* **the resulting directory**

That is **16 graded observation(s)** in total.

These expectations were not written by hand. The reference was run 5 times per probe and only what it reproduced *every single time* is graded -- anything it could not repeat, such as a timestamp or a temporary path, is excluded. You are never asked to reproduce something that is not reproducible.


## Performance Measurement

```
score = 0.5 + 0.5 x speedup      if every observation matches
score = 0.5 x (fraction matched)  otherwise
```

Correctness **unlocks** speed rather than being averaged with it: short of complete, no amount of speed helps. Partial correctness is still scored, so a submission that misses a few observations is worth repairing rather than abandoning.

Once every graded observation matches, and only then, your submission is timed against the reference on 3 workload(s) held out from grading. Your score rises with the measured speedup; there is no threshold to clear and no ceiling above which more speed stops counting. A difference too small to distinguish from the machine's own noise counts as no change.
