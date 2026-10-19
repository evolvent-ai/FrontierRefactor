# Codecharta Visualization to Go

## Task Facts

* **Scale:** `package`
* **Task form:** cross-language reimplementation
* **Source language:** `typescript`
* **Workspace:** `/app`
* **Target language:** `go`
* **Entry point:** `entry`
* **Factory dispatch marker:** `serve`
* **Declared package operations:** `viewIdForLink`, `getAsApiVersion`, `loadMaskImage`, `interpolateColor`, `colorForWord`, `toExportApiVersion`, `downloadPng`, `shapeMaskFromSvg`, `settingCountLabel`, `formatShare`, `getXMLmodel`
* **Delivered source paths:** `/app/run.sh`, `/app/task-interface.json`, `/app/implementation/main.go`, `/app/original/commitlint.config.js`, `/app/original/Ideas/dependency-cruiser.2.0.refined.cjs`, `/app/original/codecharta/commitlint.config.js`, `/app/original/gh-pages/astro.config.mjs`, `/app/original/visualization/cli.js`, `/app/original/analysis/node-wrapper/install.js`, `/app/original/codecharta/Ideas/dependency-cruiser.2.0.refined.cjs`, `/app/original/codecharta/gh-pages/astro.config.mjs`, `/app/original/codecharta/visualization/cli.js`, `/app/original/gh-pages/scripts/fix-showcase-image-names.mjs`, `/app/original/gh-pages/src/content.config.ts`, `/app/original/visualization/app/app.config.spec.ts`, `/app/original/visualization/conf/jestEnvironment.js`, `/app/original/visualization/electron/main.js`, `/app/original/visualization/mocks/changelogMock.js`, `/app/original/visualization/script/appBuild.js`, `/app/original/codecharta/analysis/node-wrapper/install.js`
* **Deliverables:** `/app/run.sh`, `implementation and build inputs under /app`
* **Build commands:** `/app/build.sh`
* **Delivered interface:** Run /app/run.sh as a JSON-lines service. Requests contain id, op="run", call="entry", and args (an array of positional arguments). Return one JSON object per request, preserving id: {"id": id, "ok": true, "value": result} or {"id": id, "ok": false, "error": message}. Do not write diagnostics to the response stream. The evaluator builds the target sources in /app/implementation with its trusted offline toolchain and executes that product directly. /app/run.sh and /app/build.sh are development entrypoints; replacing them does not replace the graded program. Put implementation sources and build inputs under /app/implementation. The first element of args selects the package operation; remaining elements are its positional arguments. Preserve all declared operations.

Reimplement the selected CodeCharta visualization package operations from TypeScript/JavaScript in Go, preserving observable behavior while improving runtime performance.

## Workspace

- `/app/implementation/` is the target Go source directory and must contain all implementation sources and build inputs required by the trusted offline toolchain.
- `/app/implementation/main.go` is the supplied Go entry source.
- `/app/task-interface.json` defines the package interface, operation dispatch, argument shapes, and result contract.
- `/app/run.sh` is the development launcher for the JSON-lines service.
- `/app/build.sh` builds the Go implementation for local development.
- `/app/original/visualization/app/codeCharta/routing/routePaths.js` contains the `viewIdForLink` reference.
- `/app/original/visualization/app/codeCharta/stores/fileStore/loaders/ccJson/util/fileValidator.js` contains the `getAsApiVersion` reference.
- `/app/original/visualization/app/codeCharta/renderer/wordCloud/util/wordCloudMask.js` contains the `loadMaskImage` reference.
- `/app/original/visualization/app/codeCharta/renderer/wordCloud/util/color.util.js` contains the `interpolateColor` reference.
- `/app/original/visualization/app/codeCharta/renderer/wordCloud/util/wordCloudWordColor.js` contains the `colorForWord` reference.
- `/app/original/visualization/app/codeCharta/util/apiVersion.js` contains the `toExportApiVersion` reference.
- `/app/original/visualization/app/codeCharta/features/screenshot/services/pngScreenshot.js` contains the `downloadPng` reference.
- `/app/original/visualization/app/codeCharta/features/domainBar/util/shapeMaskSvg.js` contains the `shapeMaskFromSvg` reference.
- `/app/original/visualization/app/codeCharta/features/scenarios/components/scenarioSettingsPicker/settingCountLabel.js` contains the `settingCountLabel` reference.
- `/app/original/visualization/app/codeCharta/features/domainWordOccurrences/util/formatShare.js` contains the `formatShare` reference.
- `/app/original/visualization/app/codeCharta/features/3dPrint/3DExports/generateXML/build3mfModel.js` contains the `getXMLmodel` reference.

## Build & Test

From `/app`, build the implementation with the supplied development build entry point:

```sh
./build.sh
```

Start the supplied JSON-lines development service with:

```sh
./run.sh
```

The harness calls `entry` through this service. Each request has `op: "run"`, `call: "entry"`, and positional `args`; the first argument selects one of the 11 package operations. The request/response envelope is only the invocation mechanism, not behavior under test.

No project-native self-check command was supplied. Inspect the original source and available project configuration for applicable checks instead of inventing a test command. The frozen grading suite runs automatically; it checks behavioral correctness first and measures speed only after correctness passes.

## Constraints

**What you CAN do**

- Replace the selected TypeScript/JavaScript package behavior with an idiomatic Go implementation under `/app/implementation`.
- Modify or add Go source files and build inputs under `/app/implementation`.
- Update `/app/run.sh` or other development entrypoints when useful, provided the graded implementation remains buildable directly from `/app/implementation`.
- Optimize parsing, string processing, color calculations, XML generation, allocation patterns, and dispatch while preserving observable results.
- Use Go standard-library facilities for JSON, XML, image decoding, URL handling, numeric conversion, hashing, and string processing where they match the reference behavior.
- Run the original implementation to establish expected behavior for valid, boundary, and malformed inputs.
- Preserve the package-level `entry` dispatch convention and all declared operations:
  `viewIdForLink`, `getAsApiVersion`, `loadMaskImage`, `interpolateColor`, `colorForWord`, `toExportApiVersion`, `downloadPng`, `shapeMaskFromSvg`, `settingCountLabel`, `formatShare`, and `getXMLmodel`.
- Return JSON-safe results matching the reference implementation's observable values, types, formatting, and errors.

**What you CANNOT do**

- Do not keep the implementation in TypeScript or JavaScript; this is a cross-language rewrite and the graded implementation must be Go.
- Do not remove, rename, or alter the calling convention of any declared package operation.
- Do not optimize only one entry operation; package coverage includes all 11 operations across 85 probes.
- Do not assume normal inputs only. The graded corpus explicitly contains 66 valid, 8 boundary, and 11 error cases. The runnable implementation already present in the workspace is the normative reference for each case.
- Do not invent behavior for browser-oriented operations such as image loading or PNG download. Reproduce the observable result or error exposed through the package interface.
- Do not replace `/app/run.sh` or `/app/build.sh` as a way to bypass the graded build. The evaluator uses a trusted offline toolchain to build sources in `/app/implementation` and executes that product directly.
- Do not require network access, dependency downloads, external services, or tools unavailable to the trusted offline Go build.
- Do not emit diagnostics to the JSON-lines response stream while using the development launcher.
- Do not change outputs merely because a different representation is more idiomatic in Go; preserve JavaScript-visible distinctions in result structure, scalar types, string formatting, ordering where observable, and error behavior.
- Do not claim performance success before correctness. Behavioral equivalence is checked first, and performance is measured only for a correct implementation.

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

We run **82 probe(s)** against your submission and compare what comes back with what the reference produced. For each we look at:

* **the value the call returned**

That is **82 graded observation(s)** in total.

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

