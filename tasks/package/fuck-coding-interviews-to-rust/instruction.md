# Fuck Coding Interviews to Rust

## Task Facts

* **Scale:** `package`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `binary_search`, `binary_search_recursive`, `binary_search_left_bound`, `linear_search`, `mad`, `factorial`, `factorial_for_loop`, `fib`, `fib_for_loop`, `bubble_sort`, `counting_sort`, `heapsort`, `heap_sort_heapq`, `insertion_sort`, `merge`, `mergesort`, `quicksort`, `quicksort_in_place`, `selection_sort`, `selection_sort_in_place`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/implementation/src/main.rs`, `/app/original/algorithms/__init__.py`, `/app/original/data_structures/__init__.py`, `/app/original/problems/__init__.py`, `/app/original/algorithms/hashing/__init__.py`, `/app/original/algorithms/math/__init__.py`, `/app/original/algorithms/searching/__init__.py`, `/app/original/algorithms/sorting/__init__.py`, `/app/original/data_structures/arrays/__init__.py`, `/app/original/data_structures/b_trees/__init__.py`, `/app/original/data_structures/graphs/__init__.py`, `/app/original/data_structures/hash_maps/__init__.py`, `/app/original/data_structures/heaps/__init__.py`, `/app/original/data_structures/linked_lists/__init__.py`, `/app/original/data_structures/queues/__init__.py`, `/app/original/data_structures/sets/__init__.py`, `/app/original/data_structures/stacks/__init__.py`, `/app/original/data_structures/trees/__init__.py`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Reimplement the exposed Python algorithms package in Rust through the `entry` symbol, preserving observable behaviour while improving performance through the language change.

## Workspace

- `/app/implementation/src/main.rs` — Rust entry source; implement the package dispatcher and `entry` handling here.
- `/app/implementation/src/subject.rs` — existing Rust subject source and implementation context.
- `/app/implementation` — target-language sources and all build inputs used by the evaluator.
- `/app/original/algorithms/searching` — Python references for `binary_search`, `binary_search_recursive`, `binary_search_left_bound`, and `linear_search`.
- `/app/original/algorithms/hashing/mad_compression.py` — Python reference for `mad`.
- `/app/original/algorithms/math/factorial.py` and `/app/original/algorithms/math/fibonacci.py` — Python references for the factorial and Fibonacci operations.
- `/app/original/algorithms/sorting` — Python references for all sorting operations, including `merge`, `mergesort`, `quicksort`, `quicksort_in_place`, `heapsort`, `heap_sort_heapq`, `counting_sort`, `bubble_sort`, `insertion_sort`, `selection_sort`, and `selection_sort_in_place`.
- `/app/task-interface.json` — task interface metadata.
- `/app/build.sh` — development build entrypoint.
- `/app/run.sh` — JSON-lines service entrypoint for local calls.

The package entry must preserve all 20 operations: `binary_search`, `binary_search_recursive`, `binary_search_left_bound`, `linear_search`, `mad`, `factorial`, `factorial_for_loop`, `fib`, `fib_for_loop`, `bubble_sort`, `counting_sort`, `heapsort`, `heap_sort_heapq`, `insertion_sort`, `merge`, `mergesort`, `quicksort`, `quicksort_in_place`, `selection_sort`, and `selection_sort_in_place`.

## Build & Test

Build the Rust implementation from `/app`:

```sh
/app/build.sh
```

This is the supplied development build command. The evaluator uses its trusted offline Rust toolchain to build the sources under `/app/implementation` and executes the resulting product directly.

Run the local JSON-lines service:

```sh
/app/run.sh
```

The service receives requests whose first positional argument selects an operation and whose remaining positional arguments follow that operation’s Python calling convention. The supplied context does not include a dedicated self-check command; inspect the source and available project checks for additional local validation. The harness performs the official frozen correctness checks automatically, then measures speed only after correctness passes.

The graded corpus contains 176 probes, including 16 boundary cases and 20 malformed or error cases. Use the runnable Python implementation under `/app/original` as the normative reference for the expected result of every probe, including those cases.

## Constraints

### **What you CAN do**

- Rewrite the implementation in Rust under `/app/implementation`.
- Use Rust standard-library data structures and algorithms, including efficient vectors, indexing, recursion where appropriate, heaps, and in-place partitioning.
- Optimize allocation, copying, recursion, and algorithmic hot paths while preserving each operation’s distinct behaviour.
- Compare the Rust service’s subject results with the Python references in `/app/original` during development.
- Keep the JSON-lines launcher protocol needed to invoke `entry`: the request’s first `args` element selects the package operation, and later elements are positional arguments.

### **What you CANNOT do**

- Do not use Python or another implementation language for the graded target; the deliverable must be a buildable Rust implementation.
- Do not omit, merge, or substitute any of the 20 declared package operations.
- Do not change the `entry` calling convention or the operation argument ordering.
- Do not replace the target with changes only to `/app/run.sh` or `/app/build.sh`; the evaluator builds and grades sources under `/app/implementation` directly.
- Do not assume that similarly named algorithms are interchangeable: preserve the observable differences between recursive, iterative, left-bound, copying, and in-place variants.
- Do not invent outcomes for boundary or malformed inputs; reproduce the behaviour of the runnable Python reference.
- Do not write diagnostics to the JSON response stream.
- Do not add dependency installation or network-based build steps; the evaluator uses an offline toolchain.

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

We run **166 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **the value the call returned**

That is **166 graded observation(s)** in total.

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

