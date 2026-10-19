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

_DISPATCH = {'is_sukun': ('pyarabic.araby', 'is_sukun'), 'is_shadda': ('pyarabic.araby', 'is_shadda'), 'is_tatweel': ('pyarabic.araby', 'is_tatweel'), 'is_tanwin': ('pyarabic.araby', 'is_tanwin'), 'is_tashkeel': ('pyarabic.araby', 'is_tashkeel'), 'is_haraka': ('pyarabic.araby', 'is_haraka'), 'is_shortharaka': ('pyarabic.araby', 'is_shortharaka'), 'is_ligature': ('pyarabic.araby', 'is_ligature'), 'is_hamza': ('pyarabic.araby', 'is_hamza'), 'is_alef': ('pyarabic.araby', 'is_alef'), 'is_yehlike': ('pyarabic.araby', 'is_yehlike'), 'is_wawlike': ('pyarabic.araby', 'is_wawlike'), 'is_teh': ('pyarabic.araby', 'is_teh'), 'is_small': ('pyarabic.araby', 'is_small'), 'is_weak': ('pyarabic.araby', 'is_weak'), 'is_moon': ('pyarabic.araby', 'is_moon'), 'is_sun': ('pyarabic.araby', 'is_sun'), 'order': ('pyarabic.araby', 'order'), 'name': ('pyarabic.araby', 'name'), 'arabicrange': ('pyarabic.araby', 'arabicrange'), 'has_shadda': ('pyarabic.araby', 'has_shadda'), 'is_vocalized': ('pyarabic.araby', 'is_vocalized'), 'is_vocalizedtext': ('pyarabic.araby', 'is_vocalizedtext'), 'is_arabicstring': ('pyarabic.araby', 'is_arabicstring'), 'is_arabicrange': ('pyarabic.araby', 'is_arabicrange'), 'is_arabicword': ('pyarabic.araby', 'is_arabicword'), 'first_char': ('pyarabic.araby', 'first_char'), 'second_char': ('pyarabic.araby', 'second_char'), 'last_char': ('pyarabic.araby', 'last_char'), 'secondlast_char': ('pyarabic.araby', 'secondlast_char'), 'strip_harakat': ('pyarabic.araby', 'strip_harakat'), 'strip_lastharaka': ('pyarabic.araby', 'strip_lastharaka'), 'strip_tashkeel': ('pyarabic.araby', 'strip_tashkeel'), 'strip_small': ('pyarabic.araby', 'strip_small'), 'strip_tatweel': ('pyarabic.araby', 'strip_tatweel'), 'strip_shadda': ('pyarabic.araby', 'strip_shadda'), 'strip_diacritics': ('pyarabic.araby', 'strip_diacritics'), 'normalize_ligature': ('pyarabic.araby', 'normalize_ligature'), 'normalize_hamza': ('pyarabic.araby', 'normalize_hamza'), 'normalize_teh': ('pyarabic.araby', 'normalize_teh')}


def entry(op, *args):
    if op not in _DISPATCH:
        raise ValueError("unknown operation: %s" % op)
    module_name, symbol = _DISPATCH[op]
    return getattr(importlib.import_module(module_name), symbol)(*args)
