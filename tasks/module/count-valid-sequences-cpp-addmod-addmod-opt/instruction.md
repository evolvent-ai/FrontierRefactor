# Count Valid Sequences Cpp Addmod Addmod Optimization

## Task Facts

* **Scale:** `module`
* **Task form:** in-place performance refactoring
* **Source language:** `cpp`
* **Workspace:** `/app`
* **Entry point:** `addmod`
* **Factory dispatch marker:** `serve addmod`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/serve.c`, `/app/subject.cpp`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `c++ -std=c++17 -O2 -x c -c ./serve.c -o ./serve.o`; `c++ -std=c++17 -O2 -o ./serve.bin ./serve.o ./subject.cpp`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream.

Optimize the existing C++ `addmod` implementation in place for speed while preserving its observable behavior and public API.

## Workspace

- `/app/subject.cpp` — entry-source file containing the `addmod` entry point to optimize.
- `/app/serve.c` — service launcher source used to invoke the subject.
- `/app/run.sh` — runtime launcher for the JSON-lines service.
- `/app/task-interface.json` — task interface configuration.
- `/app` — build directory and location for generated `serve.o` and `serve.bin`.

## Build & Test

Build the service launcher object from `/app`:

```sh
c++ -std=c++17 -O2 -x c -c ./serve.c -o ./serve.o
```

Link the launcher with the optimized C++ implementation:

```sh
c++ -std=c++17 -O2 -o ./serve.bin ./serve.o ./subject.cpp
```

Start the supplied runtime service with:

```sh
/app/run.sh
```

No standalone self-check command is supplied. Inspect the workspace for any available checks; the frozen harness checks correctness before measuring speed.

## Constraints

**What you CAN do**

- Modify the implementation of `addmod` in `/app/subject.cpp` while retaining its existing C++ calling convention.
- Use C++17-compatible optimizations such as removing redundant arithmetic, avoiding unnecessary branches or temporaries, and selecting equivalent integer operations.
- Preserve the existing `int, int` parameter types and result behavior.
- Use the runnable implementation already present in the workspace as the normative reference when establishing behavior.
- Compare against that reference for the graded semantic-prefix, boundary, and malformed-input cases; all of those case categories are included in the graded corpus.
- Keep `/app/run.sh` and the build inputs functional so the launcher can call `addmod`.

**What you CANNOT do**

- Change the observable behavior of `addmod`, including its behavior for semantic-prefix, boundary, or malformed-input cases.
- Change the public API, entry-point symbol name, parameter kinds, or C++ language requirement.
- Replace the C++ implementation with another language or alter the service interface used by the harness to invoke the subject.
- Assume outcomes for malformed or boundary inputs without establishing them from the existing runnable implementation.
- Add diagnostics or other output that interferes with the service response stream.
- Rely on correctness changes for performance gains: correctness is evaluated first, and speed is measured only after the implementation passes correctness checks.

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

We run **57 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **the value the call returned**

That is **57 graded observation(s)** in total.

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

