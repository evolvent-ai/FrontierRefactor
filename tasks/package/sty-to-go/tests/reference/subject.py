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
_VENDOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.frf-vendor')
if os.path.isdir(_VENDOR) and _VENDOR not in sys.path:
    sys.path.append(_VENDOR)

_DISPATCH = {'mute': ('sty.lib', 'mute'), 'unmute': ('sty.lib', 'unmute'), 'sgr': ('sty.renderfunc', 'sgr'), 'eightbit_fg': ('sty.renderfunc', 'eightbit_fg'), 'eightbit_bg': ('sty.renderfunc', 'eightbit_bg'), 'rgb_fg': ('sty.renderfunc', 'rgb_fg'), 'rgb_bg': ('sty.renderfunc', 'rgb_bg')}


def entry(op, *args):
    if op not in _DISPATCH:
        raise ValueError("unknown operation: %s" % op)
    module_name, symbol = _DISPATCH[op]
    return getattr(importlib.import_module(module_name), symbol)(*args)
