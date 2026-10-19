#!/usr/bin/env bash
# Harbor entry point: run the verifier, then flatten its report into the reward.json the harness
# reads. Exits with the verifier's own status.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
export REWARD_PATH=/logs/verifier/reward_detail.json
mkdir -p /logs/verifier
rm -f /logs/verifier/reward.json "$REWARD_PATH"

# UNPACK THE REFERENCE TREE BEFORE THE VERIFIER RUNS. Repo tasks ship tests/reference as a
# tarball so that mode bits (executable run.sh, traversable directories) arrive intact across
# container image layers, which do not guarantee exact mode preservation for individual files.
# The directory form is removed after packing at emit time, so this is the only way the verifier
# can see the reference. It is idempotent: if the directory already exists from a prior run in
# the same container, tar exits cleanly and nothing is overwritten.
if [ -f "$HERE/reference.tar.gz" ] && [ ! -d "$HERE/reference" ]; then
    tar xzf "$HERE/reference.tar.gz" -C "$HERE"
fi

python3 "$HERE/verify.py" --task-root "$HERE" --workspace /app
rc=$?

python3 - "$REWARD_PATH" <<'PY'
import json, sys
source = sys.argv[1]
try:
    detail = json.load(open(source))
except Exception:
    # No report at all is a zero, and an HONEST zero: the verifier failed to answer, which is not
    # the same as the submission being wrong, so the note says which happened.
    detail = {"reward": 0.0, "note": "the verifier produced no report"}
    json.dump(detail, open(source, "w"), indent=2)
flat = {
    "reward": float(detail.get("reward", 0.0) or 0.0),
    "correct": int(bool(detail.get("correct", False))),
    "correctness_passed": int(detail.get("correctness_passed", 0) or 0),
    "correctness_total": int(detail.get("correctness_total", 0) or 0),
    "speedup": float(detail.get("speedup", 0.0) or 0.0),
}
if "timing_valid" in detail:
    flat["timing_valid"] = int(bool(detail["timing_valid"]))
json.dump(flat, open("/logs/verifier/reward.json", "w"), indent=2)
# BESIDE reward.json RATHER THAN IN THE WORKSPACE, for a reason that holds however the harness
# mounts things: /logs/verifier is where reward.json is already written and collected from, so a
# second artefact there is collected by the same mechanism, while /app is the directory the
# SUBMISSION owns and works in.
#
# WHAT THIS DETAIL CONTAINS is the per-probe correctness breakdown -- which probes passed and which
# did not. In `inplace` mode /app is candidate-writable, so writing it there published that
# breakdown to the submission, in a directory the submission can also rewrite.
#
# NAMED FOR WHAT IT IS, and deliberately not for what Harbor's rubric reviewer delivers. This file
# is the per-probe correctness breakdown. It has one writer -- this line -- and no reader in the
# factory; grading reads reward.json, written just above. It lives beside that reward rather than in
# /app because /app is candidate-writable in `inplace` mode, so writing it there would publish the
# breakdown to the thing being graded, in a directory that thing can also rewrite.
#
# THIS COMMENT SHIPS. It is inside the emitted test.sh, which a rubric reviewer reads while judging
# the task, so it must not spell the reviewer's own deliverable name either -- that string appearing
# here is the confusion this rename exists to remove. The full account is in the commit.
try:
    json.dump(detail, open("/logs/verifier/correctness-detail.json", "w"), indent=2)
except OSError as exc:
    pass
print("[test.sh] reward.json:", flat)
PY
flatten_rc=$?
if [ "$flatten_rc" -ne 0 ]; then exit "$flatten_rc"; fi
exit $rc
