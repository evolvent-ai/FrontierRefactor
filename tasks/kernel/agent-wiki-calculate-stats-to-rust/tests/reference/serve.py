"""Serve a Python subject over the wire. Written into the task; not imported by the factory.

The subject supplies `entry(args) -> value`, raising to refuse. Everything else is this file.
"""
import json
import base64
import sys
import time

def _json_default(value):
    """Canonical wire forms for common Python results outside JSON's native types."""
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=lambda item: repr(item))
    if isinstance(value, (bytes, bytearray)):
        return {"__frf_bytes__": base64.b64encode(bytes(value)).decode("ascii")}
    raise TypeError("Object of type %s is not JSON serializable" % type(value).__name__)


def serve(entry, stdin=sys.stdin, stdout=sys.stdout):
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except (ValueError, RecursionError):
            # RecursionError as well as ValueError, because a line nested deeply enough exhausts
            # the decoder's stack rather than being rejected as malformed -- and RecursionError is
            # not a ValueError, so it escapes and kills the process. That is not a skipped line: it
            # is the end of the corpus, and every probe behind it is lost.
            continue                                  # an unreadable line is not a call
        if not isinstance(request, dict):
            continue                                  # a bare value is not a request either
        rid, op, args = request.get("id"), request.get("op", "run"), request.get("args", [])
        # AN ARGS FIELD OF THE WRONG SHAPE IS A REFUSAL, AND IT IS OURS RATHER THAN THE SUBJECT'S.
        # Passing it through unchecked does not merely fail, it MISATTRIBUTES: a string arrives as
        # its characters, so `{"args": "not-a-list"}` was reported as "entry() takes 1 positional
        # argument but 10 were given" -- a sentence about the subject's signature, describing a
        # defect in the request. That message would be frozen into an expectation as though the
        # subject had refused, which is the reading a candidate is then graded against.
        #
        # A MISSING field keeps the empty default: the factory always sends `args`, so its absence is
        # a hand-written line rather than a malformed call.
        if "args" in request and not isinstance(request["args"], list):
            reply = {"id": rid, "ok": False,
                     "error": "the arguments must be a JSON array"}
        elif op == "time":
            # TIMED HERE, on this side of the pipe. Measuring from the factory would charge the
            # subject for process startup and JSON transport, which for a quick subject is most of
            # what the clock would see.
            repeats = int(request.get("repeats", 1))
            failed = False
            started = time.perf_counter()
            for _ in range(repeats):
                try:
                    entry(args)
                except Exception:
                    failed = True
                    break
            elapsed = time.perf_counter() - started
            reply = {"id": rid, "ok": not failed, "seconds": elapsed}
        else:
            try:
                reply = {"id": rid, "ok": True, "value": entry(args)}
            except Exception as exc:
                # A REFUSAL IS AN ANSWER. How the subject rejects bad input is behaviour a
                # reimplementation must reproduce, so this is reported rather than raised.
                # The TYPE and MESSAGE only -- never a traceback. A traceback carries absolute
                # paths from the machine that ran it, which would be frozen into the expectation and
                # then be impossible for any other machine to reproduce.
                reply = {"id": rid, "ok": False,
                         "error": "%s: %s" % (type(exc).__name__, exc)}

        stdout.write(json.dumps(reply, default=_json_default,
                                separators=(",", ":"), sort_keys=True) + "\n")
        stdout.flush()


# THE SAME INTEGER-RENDERING CEILING THE GENERATOR RAISES. A corpus may legitimately contain an
# integer wider than CPython's 4300-digit print limit -- the prompt asks for inputs large enough to
# time -- and this code has to render exactly those probes back onto the wire. Left at the default,
# a task that froze successfully would fail at grading time with
# `Exceeds the limit (4300) for integer string conversion`, which describes our interpreter rather
# than the submission.
try:
    sys.set_int_max_str_digits(200000)
except AttributeError:                                    # pragma: no cover -- Python < 3.11
    pass

if __name__ == "__main__":
    # THE WORKSPACE GOES AFTER THE STANDARD LIBRARY, NOT BEFORE IT. `sys.path.insert(0, ".")` makes
    # the subject's own directory shadow every stdlib module of the same name, and real packages
    # have such directories: `algorithms/string/` shadows `string`, so that package's own
    # `from string import ascii_lowercase` resolved to itself and every probe died with
    # `ImportError: cannot import name 'ascii_lowercase' from partially initialized module 'string'
    # (most likely due to a circular import)`. Three package candidates were refused for it across
    # one night's runs, filed as `will-not-repeat-itself (material)` -- the subject refused every
    # probe, reproducibly, for a reason that was ours.
    #
    # `.` still has to be on the path or the subject cannot be imported at all. What changes is the
    # position: appended, so the standard library answers first and the workspace answers for
    # everything the standard library does not have. This is the same rule the dispatcher already
    # applies to the vendor directory, and for the same reason.
    if "." not in sys.path:
        sys.path.append(".")
    import importlib

    # WHICH SYMBOL, from the command line. A shim that could only serve a function literally called
    # `entry` could only serve a subject somebody had written for it -- and the whole point is to
    # serve real code, where the function is called `camel_to_snake` and lives beside its own
    # imports. The name travels as an argument rather than being edited into this file, so the
    # template stays data and one copy serves every subject.
    _module = sys.argv[1] if len(sys.argv) > 1 else "subject"
    _symbol = sys.argv[2] if len(sys.argv) > 2 else "entry"
    _entry = getattr(importlib.import_module(_module.removesuffix(".py")), _symbol)

    # The wire always passes ONE argument: the list of arguments. A real function takes them
    # spread out, so the adaptation happens here rather than in every subject -- which would mean
    # editing somebody else's code to serve it, and then grading the edit.
    serve(lambda args: _entry(*args))
