# Ex15 Java Histogram Histogram Optimization

## Task Facts

* **Scale:** `kernel`
* **Task form:** in-place performance refactoring
* **Source language:** `java`
* **Workspace:** `/app`
* **Entry point:** `histogram`
* **Factory dispatch marker:** `serve histogram`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/Serve.java`, `/app/Subject.java`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `javac -d . ./Serve.java ./Subject.java`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Optimize the existing Java `histogram` kernel in place for lower runtime while preserving its public API and observable behavior exactly.

## Workspace

- `/app` — build directory and root of the delivered task.
- `/app/Subject.java` — implementation source containing the `histogram` entry point to optimize.
- `/app/Serve.java` — launcher and request dispatcher used to invoke the entry point.
- `/app/run.sh` — supplied JSON-lines service launcher; it builds the Java sources before execution.
- `/app/task-interface.json` — task interface metadata.
- Deliver the optimized implementation, `/app/run.sh`, and all required build inputs under `/app`.

## Build & Test

From `/app`, compile the supplied Java sources with:

```bash
javac -d . ./Serve.java ./Subject.java
```

Launch the callable service with:

```bash
/app/run.sh
```

The service accepts one JSON request per line with `op="run"`, `call="entry"`, and positional arguments in `args`. The JSON-lines envelope is only the harness mechanism for calling `histogram`; grading observes the kernel's results, not additional protocol behavior.

No project-native self-check command was supplied. Inspect the delivered source and scripts for any available checks. The frozen grader runs automatically: it verifies correctness first and measures speed only after the implementation passes correctness checks.

## Constraints

**What you CAN do**

- Modify the existing Java implementation of `histogram` in `/app/Subject.java`.
- Optimize loops, indexing, branching, allocation, temporary storage, and data access patterns.
- Cache repeated values or computations when doing so preserves all observable results.
- Use Java standard-library functionality already available in the supplied build environment.
- Inspect and run the existing implementation as the normative reference for graded semantic-prefix, boundary, and malformed-input cases.
- Use `/app/run.sh` to exercise the entry point through the supplied service interface.
- Rely on the supplied floating-point comparison policy where applicable: `abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)`.
- Preserve exact integer values, booleans, strings, field names, and array shapes. Preserve infinities by sign and position; NaN is accepted only where the reference also produces NaN.

**What you CANNOT do**

- Do not replace the implementation with another language; this is an in-place Java optimization, not a cross-language rewrite.
- Do not change the public API, the `histogram` entry symbol, its calling convention, parameter interpretation, or return structure.
- Do not change observable behavior, including exception or result behavior for graded boundary and malformed-input cases. The implementation initially present in the workspace defines the expected behavior for those cases.
- Do not assume inputs are always well formed or restricted to typical histogram cases; the graded corpus includes semantic-prefix, boundary, and malformed-input probes.
- Do not modify behavior merely because an alternative result appears more mathematically natural or robust.
- Do not require floating-point results to be bitwise identical; use the supplied tolerance and NaN/infinity rules.
- Do not add dependencies or require build steps beyond the supplied Java environment.
- Do not write diagnostics to the JSON response stream used by the launcher.

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

