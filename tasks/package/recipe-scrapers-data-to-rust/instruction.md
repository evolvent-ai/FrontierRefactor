# Recipe Scrapers Data to Rust

## Task Facts

* **Scale:** `package`
* **Task form:** cross-language reimplementation
* **Source language:** `python`
* **Workspace:** `/app`
* **Target language:** `rust`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `levenshtein_distance`, `find_json`, `find_instructions`, `parse_instructions`, `fix_json_ld_property_keys`, `strip_tags`, `stripper`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/original/generate.py`, `/app/implementation/src/main.rs`, `/app/original/recipe_scrapers/__init__.py`, `/app/original/scripts/reorder_json_keys.py`, `/app/original/templates/scraper.py`, `/app/original/tests/__init__.py`, `/app/original/recipe_scrapers/plugins/__init__.py`, `/app/original/recipe_scrapers/settings/__init__.py`, `/app/original/tests/library/__init__.py`, `/app/implementation/src/subject.rs`, `/app/original/recipe_scrapers/__version__.py`, `/app/original/scripts/update_test.py`, `/app/original/recipe_scrapers/plugins/_interface.py`, `/app/original/recipe_scrapers/settings/default.py`, `/app/original/tests/library/test_exceptions.py`, `/app/original/recipe_scrapers/_abstract.py`, `/app/original/recipe_scrapers/plugins/best_image.py`, `/app/original/recipe_scrapers/settings/template.py`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Reimplement the Python recipe-scraping data operations in Rust, preserving observable reference behaviour while improving performance through the cross-language rewrite.

## Workspace

- `/app/implementation/src/main.rs` contains the Rust entry point and must expose the `entry` dispatch symbol.
- `/app/implementation/src/subject.rs` contains existing Rust implementation context; keep implementation sources and all build inputs under `/app/implementation`.
- `/app/original/recipe_scrapers/dagelijksekost.py` is the Python reference for `levenshtein_distance`, `find_json`, `find_instructions`, and `parse_instructions`.
- `/app/original/recipe_scrapers/tineno.py` is the Python reference for `fix_json_ld_property_keys`.
- `/app/original/recipe_scrapers/plugins/html_tags_stripper.py` is the Python reference for `strip_tags` and `stripper`.
- `/app/task-interface.json` describes the harness interface and operation dispatch.
- `/app/build.sh` is the development build entry point.
- `/app/run.sh` runs the JSON-lines service used to call the implementation.

The exposed package operations are `levenshtein_distance`, `find_json`, `find_instructions`, `parse_instructions`, `fix_json_ld_property_keys`, `strip_tags`, and `stripper`. Requests select the operation as the first positional argument in `args`; remaining positional arguments must be passed to the corresponding Rust implementation through `entry`.

## Build & Test

Build the Rust implementation from `/app`:

```sh
/app/build.sh
```

Run the implementation's JSON-lines service for local checks:

```sh
/app/run.sh
```

No dedicated self-check command is supplied. Inspect the Rust and reference sources for available project-native checks, and compare service results with the runnable Python reference when validating behaviour. The harness automatically checks correctness first and measures speed only after the implementation passes those correctness checks.

## Constraints

**What you CAN do**

- Replace the Python implementations with Rust implementations under `/app/implementation`.
- Use Rust standard-library algorithms and data structures, including efficient Unicode-aware string processing, JSON parsing, maps, and dynamic programming for the Levenshtein operation.
- Factor shared parsing, HTML stripping, and JSON-key handling logic where that preserves the seven operation contracts.
- Optimize allocation, repeated parsing, traversal, and string processing after matching the reference results.
- Use `/app/original/recipe_scrapers` as the normative behavioural reference for the selected operations, including its handling of valid, boundary, and error inputs.

**What you CANNOT do**

- Do not implement the task in Python or another language; the graded implementation must remain Rust and must be buildable by the evaluator's trusted offline toolchain.
- Do not reduce the package to a single operation. Preserve all seven declared operations and their positional calling conventions through `entry`.
- Do not change observable behaviour from the Python reference. The graded corpus contains 200 probes: 186 valid cases, 7 boundary cases, and 7 error cases across the operations. The existing runnable implementation is authoritative for expected results, including malformed and boundary inputs.
- Do not place required implementation sources or build inputs outside `/app/implementation`; changing `/app/run.sh` or `/app/build.sh` does not replace the graded Rust product.
- Do not treat the JSON-lines request and response envelope as subject behaviour. Use it only as the harness mechanism: requests contain `id`, `op="run"`, `call="entry"`, and positional `args`, and responses preserve the request `id`.
- Do not write diagnostics into the service response stream.
- Do not add dependency installation or network-dependent build steps; the evaluator builds offline.

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

