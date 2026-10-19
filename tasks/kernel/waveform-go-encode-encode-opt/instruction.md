# Waveform Go Encode Encode Optimization

## Task Facts

* **Scale:** `kernel`
* **Task form:** in-place performance refactoring
* **Source language:** `go`
* **Workspace:** `/app`
* **Entry point:** `Encode`
* **Factory dispatch marker:** `serve Encode`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/bridge.go`, `/app/serve.go`, `/app/subject.go`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `env GOSUMDB=off GOFLAGS=-mod=mod GOTOOLCHAIN=auto go build -o ./serve.bin ./serve.go ./bridge.go ./subject.go`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. For each floating-point result, abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference). Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position. NaN is accepted only at matching NaN positions.

Improve the runtime performance of the existing Go implementation of `Encode` from `mautrix/telegram` in place, preserving its observable behavior, calling convention, and public API.

## Workspace

- `/app/subject.go`: entry source containing the `Encode` implementation to optimize.
- `/app/serve.go`: service launcher used to invoke the entry point.
- `/app/bridge.go`: bridge code connecting service requests to the subject implementation.
- `/app/run.sh`: JSON-lines service command used to run the built subject.
- `/app/task-interface.json`: task interface and invocation metadata.
- `/app`: build directory and location for implementation and build-input deliverables.
- Entry point: `Encode`.
- Invocation operation: `serve` with the `Encode` entry call.
- Parameter shape: one `int64` array.

## Build & Test

Build the Go service from `/app` with:

```sh
env GOSUMDB=off GOFLAGS=-mod=mod GOTOOLCHAIN=auto go build -o ./serve.bin ./serve.go ./bridge.go ./subject.go
```

This produces `/app/serve.bin` from the service launcher, bridge, and subject sources.

Run the project service with:

```sh
/app/run.sh
```

The service accepts JSON-lines requests and invokes the subject through the supplied entry interface. No separate self-check command is supplied; inspect the source and available project-native checks for an appropriate confidence check. The harness runs the frozen correctness suite automatically before measuring performance.

The graded corpus includes semantic-prefix, boundary, and malformed-input cases. The implementation currently present in the workspace is the normative reference for the expected result of every case; it is runnable and must be used as the behavior baseline when validating an optimization.

Correctness is checked before speed. Floating-point results are compared with `abs(candidate - reference) <= 1e-12 + 1e-09 * abs(reference)`. Integer values, booleans, strings, field names, and array shapes must match exactly. Infinities must match in sign and position, and NaN is accepted only at matching positions.

## Constraints

**What you CAN do**

- Optimize the existing `Encode` implementation in Go under `/app`.
- Reduce allocations, copying, redundant conversions, and unnecessary work while preserving all observable results.
- Use Go profiling, compiler diagnostics, inlining-friendly code, preallocation, and efficient iteration where they improve this computation without changing its contract.
- Keep changes focused on the selected `Encode` kernel and the build inputs required to compile it.
- Compare optimized results with the existing runnable implementation, including semantic-prefix, boundary, and malformed-input inputs.

**What you CANNOT do**

- Do not change the public API, calling convention, parameter kinds, or return structure of `Encode`.
- Do not change observable behavior, including behavior for semantic-prefix, boundary, or malformed-input cases.
- Do not replace the implementation with another language or add a cross-language rewrite; this is an in-place Go optimization.
- Do not modify the JSON-lines request/response mechanism as a substitute for optimizing `Encode`.
- Do not introduce assumptions about inputs or omit validation and edge-case handling that the normative implementation provides.
- Do not alter unrelated project behavior, command-line behavior, or filesystem behavior.
- Do not add dependency installation steps or rely on unavailable external services.
- Do not demand bitwise-identical floating-point output where the supplied comparison policy permits its stated tolerance.

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

