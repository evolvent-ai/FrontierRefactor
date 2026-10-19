# Edit Distance Cpp Editdistdp Edit Dist Dp Optimization

## Task Facts

* **Scale:** `module`
* **Task form:** in-place performance refactoring
* **Source language:** `cpp`
* **Workspace:** `/app`
* **Entry point:** `editDistDP`
* **Factory dispatch marker:** `serve editDistDP`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/serve.c`, `/app/subject.cpp`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `c++ -std=c++17 -O2 -x c -c ./serve.c -o ./serve.o`; `c++ -std=c++17 -O2 -o ./serve.bin ./serve.o ./subject.cpp`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream.

Make the existing C++ `editDistDP` implementation faster in place while preserving its observable behavior, calling convention, and public API.

## Workspace

- `/app/subject.cpp` — implementation source containing the `editDistDP` entry point.
- `/app/serve.c` — launcher source used to expose the entry point through the task harness.
- `/app/task-interface.json` — interface metadata for the harness.
- `/app/run.sh` — JSON-lines service launcher used to invoke the implementation.
- Entry point: `editDistDP`, with parameters of kinds `string, string, int, int`.

## Build & Test

Build the launcher and subject implementation from `/app`:

```sh
c++ -std=c++17 -O2 -x c -c ./serve.c -o ./serve.o
c++ -std=c++17 -O2 -o ./serve.bin ./serve.o ./subject.cpp
```

The first command compiles the launcher; the second links it with `/app/subject.cpp`. The service is run with:

```sh
/app/run.sh
```

No self-check command is supplied. Inspect the source for any available project-native checks rather than inventing a test command. Correctness is checked first by the harness, and speed is measured only after the implementation passes correctness checks.

The graded probe contract includes semantic-prefix, boundary, and malformed-input cases. The implementation currently present in `/app/subject.cpp` is the normative reference for the expected result of every such case; compare the optimized implementation against that runnable reference without assuming outcomes not established by the source. The JSON-lines service is only the harness mechanism for calling the subject; the graded behavior is the result produced by `editDistDP`.

## Constraints

**What you CAN do**

- Modify the implementation of `editDistDP` in `/app/subject.cpp` in place.
- Optimize the dynamic-programming computation using C++ techniques such as reduced memory, eliminating redundant work, cache-friendly iteration, and avoiding unnecessary allocations or copies.
- Preserve all behavior established by the existing implementation for ordinary, prefix, boundary, and malformed-input arguments.
- Use the existing C++17 build environment and keep the implementation compatible with the supplied launcher.

**What you CANNOT do**

- Do not change the public API, symbol name, parameter types, parameter order, or calling convention of `editDistDP`.
- Do not rewrite the task in another language or replace the C++ implementation with an external process or service.
- Do not change observable behavior, including behavior for semantic-prefix, boundary, or malformed-input cases.
- Do not alter `/app/run.sh`, the request/response protocol, or launcher behavior as a substitute for optimizing `editDistDP`.
- Do not remove or bypass input handling required by the existing implementation.
- Do not add dependencies or rely on unavailable repository-wide files or commands.

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

We run **56 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **the value the call returned**

That is **56 graded observation(s)** in total.

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

