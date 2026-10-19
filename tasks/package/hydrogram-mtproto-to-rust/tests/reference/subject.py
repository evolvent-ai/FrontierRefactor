import importlib
import os
import sys

# THE SCRIPT'S OWN DIRECTORY MOVES BEHIND THE STANDARD LIBRARY. Python puts it at
# sys.path[0] before this file runs -- that is the interpreter, not a call we make -- and a
# real package whose tree contains `string/`, `types/` or `json/` then shadows the stdlib
# module of that name. Measured three times in one night: `algorithms/string/` shadowed
# `string`, so the package's own `from string import ascii_lowercase` resolved to itself
# and every probe died with `ImportError: cannot import name ... from partially
# initialized module 'string' (most likely due to a circular import)`. Filed each time as
# `will-not-repeat-itself (material)`: a reproducible refusal, for a reason that was ours.
#
# It stays ON the path -- the subject lives there and has to be importable -- but after
# the stdlib, so the standard library answers first and the workspace answers for what it
# does not have.
# BOTH THIS DIRECTORY AND ITS PARENT, because which one holds the package depends on the
# language's `dispatcher_dir`: python puts the dispatcher BESIDE the package, so the
# importable root is the parent, while go puts it in a `frfd/` subpackage. Appending only
# this directory cut the subject off -- `ModuleNotFoundError: No module named 'boltons'`
# on a corpus of 200 probes that had just stopped failing for the shadowing reason.
_HERE = os.path.dirname(os.path.abspath(__file__))
_UP = os.path.dirname(_HERE)
for _entry in ('', '.', _HERE, _UP):
    while _entry in sys.path:
        sys.path.remove(_entry)
for _entry in (_HERE, _UP):
    if _entry and _entry not in sys.path:
        sys.path.append(_entry)

# The package's dependencies, installed inside the tree. APPENDED: the package's own
# modules must shadow anything here, never the other way round.
# BESIDE THE DISPATCHER *AND* ONE LEVEL UP. The installer runs where the MANIFEST is,
# which for a python project is the repository root -- so `.frf-vendor` lands at the
# workspace root while this file sits at `workspace/<package_name>/`. Looking only
# beside itself found nothing, and the subject then failed on `ModuleNotFoundError:
# No module named 'numpy'` with an install that had reported success.
for _base in (_HERE, _UP):
    _VENDOR = os.path.join(_base, '.frf-vendor') if _base else ""
    if _VENDOR and os.path.isdir(_VENDOR) and _VENDOR not in sys.path:
        sys.path.append(_VENDOR)

_DISPATCH = {'get_type_hint': ('compiler.api.compiler', 'get_type_hint'), 'remove_whitespaces': ('compiler.api.compiler', 'remove_whitespaces'), 'get_docstring_arg_type': ('compiler.api.compiler', 'get_docstring_arg_type'), 'get_references': ('compiler.api.compiler', 'get_references')}


def entry(op, *args):
    if op not in _DISPATCH:
        raise ValueError("unknown operation: %s" % op)
    module_name, symbol = _DISPATCH[op]
    return getattr(importlib.import_module(module_name), symbol)(*args)
