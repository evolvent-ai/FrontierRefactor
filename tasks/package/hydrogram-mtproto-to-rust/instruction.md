# Hydrogram Mtproto to Rust

## Task Facts

* **Scale:** `package`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `get_type_hint`, `remove_whitespaces`, `get_docstring_arg_type`, `get_references`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/hatch_build.py`, `/app/implementation/src/main.rs`, `/app/original/compiler/__init__.py`, `/app/original/dev_tools/check_api_schema_updates.py`, `/app/original/hydrogram/__init__.py`, `/app/original/tests/__init__.py`, `/app/original/compiler/api/__init__.py`, `/app/original/compiler/docs/__init__.py`, `/app/original/compiler/errors/__init__.py`, `/app/original/docs/source/conf.py`, `/app/original/hydrogram/connection/__init__.py`, `/app/original/hydrogram/crypto/__init__.py`, `/app/original/hydrogram/enums/__init__.py`, `/app/original/hydrogram/errors/__init__.py`, `/app/original/hydrogram/handlers/__init__.py`, `/app/original/hydrogram/helpers/__init__.py`, `/app/original/hydrogram/methods/__init__.py`, `/app/original/hydrogram/nav/__init__.py`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Reimplement the exposed Hydrogram compiler operations in Rust with observable behavior equivalent to the Python reference while improving performance through the cross-language rewrite.

## Workspace

- `/app/implementation/` — target Rust implementation and build inputs compiled by the evaluator.
- `/app/implementation/src/main.rs` — supplied Rust entry source; implement the `entry` service here or through Rust modules included by it.
- `/app/implementation/src/subject.rs` — additional supplied Rust source relevant to the target implementation.
- `/app/original/compiler/api/compiler.py` — Python reference implementation for the exposed compiler operations.
- `/app/original/compiler/` — related Python compiler package sources and error definitions.
- `/app/task-interface.json` — task interface metadata.
- `/app/run.sh` — development launcher for the JSON-lines service.
- `/app/build.sh` — development build entrypoint.
- `/app/original/` — reference project tree; use the relevant compiler sources to establish expected behavior rather than attempting to port the entire Hydrogram repository.

The Rust `entry` implementation must dispatch the first positional argument to one of these operations, passing the remaining positional arguments unchanged:

- `get_type_hint(type)`
- `remove_whitespaces(source)`
- `get_docstring_arg_type(t)`
- `get_references(t, kind)`

The harness invokes the product through a JSON-lines service. Each request identifies `call: "entry"` and supplies positional `args`; each response preserves the request `id` and reports either a successful value or an error. This envelope is the harness transport mechanism; the graded behavior is the returned operation result.

## Build & Test

Build the Rust target from `/app`:

```sh
/app/build.sh
```

This prepares the development product using the supplied build entrypoint. The evaluator independently builds sources under `/app/implementation` with its trusted offline Rust toolchain.

Run the development service from `/app`:

```sh
/app/run.sh
```

This starts the JSON-lines service used to exercise `entry`. No dedicated self-check command is supplied; inspect `/app/original/compiler/api/compiler.py` and the available project sources for suitable comparison checks. The harness checks correctness before measuring execution speed, so preserve behavior before optimizing.

## Constraints

**What you CAN do**

- Replace the Python implementation with Rust code under `/app/implementation`.
- Organize the implementation into additional Rust modules and build inputs under `/app/implementation` as needed.
- Use Rust string scanning, byte-oriented processing, lookup tables, and allocation reduction to optimize parsing and reference extraction.
- Reproduce the Python compiler behavior for all four declared operations, including normal, boundary, and malformed inputs represented by the reference corpus.
- Compare the Rust service's operation results with the runnable Python reference while developing.
- Keep the implementation self-contained and compatible with the evaluator's trusted offline toolchain.

**What you CANNOT do**

- Do not implement the target in Python or another language; the graded implementation must be Rust.
- Do not reduce the package to a single operation or omit any of `get_type_hint`, `remove_whitespaces`, `get_docstring_arg_type`, and `get_references`.
- Do not change the `entry` calling convention: the first element of `args` selects the operation and the remaining elements are its positional arguments.
- Do not replace observable Python behavior with guessed behavior; use `/app/original/compiler/api/compiler.py` as the reference for return values, errors, parsing, whitespace handling, and reference selection.
- Do not place required implementation sources or build inputs outside `/app/implementation`.
- Do not rely on network access, runtime dependency installation, or modifications to `/app/run.sh` or `/app/build.sh` as a substitute for the graded Rust product.
- Do not write diagnostics into the JSON response stream.
- Do not optimize at the expense of correctness; performance is evaluated only after the implementation passes behavioral checks.

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

