# Trimesh Triangle Loading Optimization

## Task Facts

* **Scale:** `package`
* **Task form:** in-place performance refactoring
* **Source language:** `python`
* **Workspace:** `/app`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `unit_conversion`, `to_inch`, `has_module`, `transform_to_matrices`, `hex_to_rgba`
* **Delivered source paths:** `/app/Makefile`, `/app/README.md`, `/app/pyproject.toml`, `/app/run.sh`, `/app/task-interface.json`, `/app/examples/convexify.py`, `/app/helpers/run_typecheck.py`, `/app/trimesh/__init__.py`, `/app/helpers/notebook_viewer/compile.py`, `/app/trimesh/exchange/__init__.py`, `/app/trimesh/interfaces/__init__.py`, `/app/trimesh/path/__init__.py`, `/app/trimesh/ray/__init__.py`, `/app/trimesh/resources/__init__.py`, `/app/trimesh/scene/__init__.py`, `/app/trimesh/viewer/__init__.py`, `/app/trimesh/visual/__init__.py`, `/app/trimesh/voxel/__init__.py`, `/app/examples/docker/render/render.py`, `/app/trimesh/exchange/gltf/__init__.py`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Improve the runtime performance of the existing Python `trimesh` package operations in place while preserving their public API and observable behavior.

## Workspace

- `/app/subject.py` — defines the `entry` symbol used to dispatch package operations.
- `/app/serve.py` — JSON-lines service launcher used by the harness.
- `/app/run.sh` — service entry point executed by the harness from `/app`.
- `/app/task-interface.json` — machine-readable interface definition.
- `/app/trimesh/` — existing Python package implementation.
- `/app/trimesh/units.py` — implementation source for `unit_conversion(current, desired)` and `to_inch(unit)`.
- `/app/trimesh/util.py` — implementation source for `has_module(name)`.
- `/app/trimesh/path/exchange/svg_io.py` — implementation source for `transform_to_matrices(transform)`.
- `/app/trimesh/visual/color.py` — implementation source for `hex_to_rgba(color)`.
- `/app/trimesh/exchange/load.py` and `/app/trimesh/exchange/` — mesh-loading implementation and format handlers relevant to the package.
- `/app/pyproject.toml` — Python project and tooling configuration.
- `/app/Makefile` and `/app/README.md` — project documentation and any project-native development targets that may be available.

The harness starts `/app/run.sh` with `python3 ./serve.py subject entry`. Requests use the JSON-lines service to select one of these operations through `entry`: `unit_conversion`, `to_inch`, `has_module`, `transform_to_matrices`, or `hex_to_rgba`. The request envelope is only the harness transport; grading observes the results of the package operations.

## Build & Test

No build commands or project-native self-check commands were supplied. Inspect `/app/Makefile`, `/app/pyproject.toml`, and `/app/README.md` for applicable checks before making changes; do not assume an undocumented command exists.

The harness runs `/app/run.sh` automatically. Correctness is checked before performance is measured, and submissions that change observable behavior are not eligible for speed evaluation.

## Constraints

**What you CAN do**

- Optimize the existing Python implementation in place under `/app`.
- Modify implementation and build inputs under `/app`, including `/app/subject.py`, `/app/run.sh`, and relevant modules in `/app/trimesh/`.
- Reduce repeated parsing, allocation, conversion, import lookup, intermediate-array creation, and Python-level iteration where profiling shows measurable cost.
- Use existing Python standard-library facilities, NumPy vectorization, local caching, precomputed constants, and package-local helpers when they preserve current semantics.
- Specialize internal paths for common inputs while retaining the existing fallback behavior for every supported input.
- Profile the full dispatch path and the declared operations before optimizing so changes target measured bottlenecks.
- Add focused internal tests or benchmarks for development confidence without changing the exposed interface.

**What you CANNOT do**

- Replace the implementation with another language; the solution must remain Python.
- Change the public API, operation names, function signatures, `entry` calling convention, or JSON-safe result structure.
- Change observable behavior, including return values, result types, exception behavior, accepted inputs, parsing rules, import-detection semantics, or side effects.
- Remove or bypass any declared operation: `unit_conversion`, `to_inch`, `has_module`, `transform_to_matrices`, and `hex_to_rgba` must all remain available.
- Treat `serve` as an installed executable; it is an internal invocation marker, while `/app/run.sh` is the supplied launcher.
- Write diagnostics or benchmark output to the JSON-lines response stream.
- Introduce dependency installation or network access as part of the build or runtime path.
- Invent new floating-point equivalence rules or assume bitwise equality where the existing implementation does not require it; preserve the implementation’s current numerical behavior and result structure.

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

