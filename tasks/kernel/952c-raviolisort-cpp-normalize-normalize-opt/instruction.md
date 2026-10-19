# 952c Raviolisort Cpp Normalize Normalize Optimization

## Task Facts

* **Scale:** `kernel`
* **Task form:** in-place performance refactoring
* **Source language:** `cpp`
* **Workspace:** `/app`
* **Entry point:** `normalize`
* **Factory dispatch marker:** `serve normalize`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/serve.c`, `/app/subject.cpp`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `c++ -std=c++17 -O2 -x c -c ./serve.c -o ./serve.o`; `c++ -std=c++17 -O2 -o ./serve.bin ./serve.o ./subject.cpp`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Improve the runtime performance of the existing C++ `normalize` implementation in place while preserving its observable behavior and public API; this is not a cross-language rewrite.

## Workspace

- `/app/subject.cpp` — implementation containing the `normalize` entry point.
- `/app/serve.c` — launcher used to expose the entry point through the task harness.
- `/app/task-interface.json` — task interface and calling metadata.
- `/app/run.sh` — JSON-lines service used to invoke the built subject.
- `/app` — build directory and location for generated build artifacts.

## Build & Test

Build the launcher and link it with the subject implementation:

```sh
cd /app
c++ -std=c++17 -O2 -x c -c ./serve.c -o ./serve.o
c++ -std=c++17 -O2 -o ./serve.bin ./serve.o ./subject.cpp
```

Run the supplied service entry point for JSON-lines requests:

```sh
cd /app
/app/run.sh
```

The service invokes `normalize` through the harness interface. No separate self-check command is supplied; inspect `/app/subject.cpp` for any available project-native checks rather than inventing a test command. Correctness is checked first against the frozen corpus, and performance is measured only after the implementation remains correct.

## Constraints

**What you CAN do**

- Modify the implementation of `normalize` in `/app/subject.cpp` to reduce runtime and unnecessary work.
- Use C++17-compatible optimizations such as improved iteration, fewer allocations or copies, better data access patterns, and appropriate standard-library algorithms.
- Preserve the existing handling of the `int_array` input, including all valid, boundary, prefix, and malformed-input cases.
- Keep changes scoped to this kernel and validate behavior against the implementation currently present in the workspace before optimizing it.

**What you CANNOT do**

- Do not change the public API, calling convention, symbol name `normalize`, or parameter type.
- Do not rewrite the task in another language; the implementation must remain C++.
- Do not change observable behavior. The graded corpus includes semantic-prefix, boundary, and malformed-input cases; the implementation already present in `/app/subject.cpp` is the normative reference for what each case must do.
- Do not change result structure or types. Integer values, booleans, strings, field names, and array shapes must match exactly.
- For floating-point results, preserve the supplied comparison policy: absolute error must be at most `1e-12 + 1e-09 * abs(reference)`, with matching infinities by sign and NaN accepted only at matching positions. Do not require bitwise equality where this tolerance applies.
- Do not alter the JSON-lines harness protocol or use diagnostics in the response stream as part of the implementation.
- Do not add dependency installation steps or rely on files outside the supplied workspace.

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

