# Xmloxide XML Parsing Optimization

## Task Facts

* **Scale:** `repo`
* **Task form:** in-place performance refactoring
* **Source language:** `rust`
* **Workspace:** `/app`
* **Observed invocation:** `/app/target/release/xmllint`
* **Delivered source paths:** `/app/Cargo.lock`, `/app/Cargo.toml`, `/app/Makefile`, `/app/README.md`, `/app/run.sh`, `/app/task-interface.json`, `/app/benches/comparison_bench.rs`, `/app/examples/basic_parse.rs`, `/app/include/libxml2_compat.h`, `/app/src/async_xml.rs`, `/app/tests/c14n_conformance.rs`, `/app/fuzz/fuzz_targets/fuzz_html5_fragment.rs`, `/app/pyxmloxide/src/lib.rs`, `/app/src/bin/xmllint.rs`, `/app/src/catalog/mod.rs`, `/app/src/css/eval.rs`, `/app/src/encoding/mod.rs`, `/app/src/error/mod.rs`, `/app/src/ffi/c14n.rs`, `/app/src/html/entities.rs`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Preparation commands:** `cargo build --release --bin xmllint --features cli`
* **Delivered interface:** The evaluator invokes /app/run.sh with the original program's arguments and standard input in a prepared working directory. Preserve argument handling, exit status, both output streams, and produced file contents. Keep the working directory supplied by the caller when interpreting relative input/output paths.

Improve the runtime performance of the existing pure-Rust xmloxide XML parsing executable without changing its observable behavior or public API; this is an in-place optimization, not a cross-language rewrite.

## Workspace

- `/app/Cargo.toml` and `/app/Cargo.lock`: Rust package configuration and locked dependencies.
- `/app/src/bin/xmllint.rs`: `xmllint` command-line entry point.
- `/app/run.sh`: evaluator entry point; it invokes the program with the original arguments and standard input.
- `/app/src/parser/`: XML parsing implementation, including `mod.rs`, `xml.rs`, `input.rs`, `push.rs`, and related parser paths.
- `/app/src/reader/` and `/app/src/sax/`: reader and SAX parsing interfaces used by parsing workloads.
- `/app/src/html/` and `/app/src/html5/`: HTML parsing components, including tokenization and tree building.
- `/app/src/tree/`: parsed document and node structures.
- `/app/src/serial/`: XML, HTML, and canonical serialization paths whose outputs must remain unchanged.
- `/app/src/error/`, `/app/src/encoding/`, and `/app/src/util/`: error, encoding, and shared utility code involved in parsing.
- `/app/benches/parser_bench.rs` and `/app/benches/comparison_bench.rs`: repository benchmark sources to inspect when identifying performance-sensitive paths.
- `/app/tests/`, `/app/examples/`, and `/app/fuzz/`: existing project checks and usage references to inspect before changing behavior.
- `/app/README.md` and `/app/Makefile`: project documentation and available project-native commands.
- `/app/harvest-inputs.tar.gz`: workload input fixtures used by the selected scenarios.

## Build & Test

Build the release `xmllint` binary with the supplied preparation command:

```text
cargo build --release --bin xmllint --features cli
```

The resulting executable is `/app/target/release/xmllint`. The evaluator calls `/app/run.sh` with the original arguments and standard input; preserve its exit status, standard output, standard error, and produced files. No self-check command is supplied in the task context, so inspect the existing tests, examples, benchmarks, README, and Makefile for an appropriate project-native check rather than inventing one. Correctness is checked first against the frozen workload, and speed is measured only after the implementation remains behaviorally correct.

## Constraints

**What you CAN do**

- Optimize the existing Rust implementation in `/app` while retaining its public interfaces and command-line behavior.
- Profile or inspect the XML parsing, input handling, tree construction, encoding, error, serialization, reader, and SAX paths to locate avoidable allocation, copying, parsing, or dispatch overhead.
- Improve data structures, iteration, buffering, ownership/borrowing, allocation reuse, and hot-path control flow where the resulting behavior remains identical.
- Use the existing parser benchmarks and repository tests as references when evaluating changes.
- Keep changes within the existing Rust project and update implementation and build inputs under `/app` as needed.

**What you CANNOT do**

- Do not change observable behavior for the 14 graded scenarios, including exit status, standard output, standard error, or produced file contents.
- Do not change the public API or the calling behavior of the `xmllint` executable and `/app/run.sh` interface.
- Do not rewrite the implementation in another language; the solution must remain Rust.
- Do not change argument handling or resolve relative input/output paths against a different working directory than the caller supplies.
- Do not remove or weaken parsing, error-reporting, serialization, encoding, reader, SAX, HTML, or compatibility behavior to obtain a speedup.
- Do not assume that a faster result is acceptable if correctness differs; the automatic harness establishes correctness before measuring performance.
- Do not invent benchmark thresholds, expected outputs, or unsupported self-check commands.

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
