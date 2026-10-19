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

_DISPATCH = {'binary_search': ('algorithms.searching.binary_search', 'binary_search'), 'binary_search_recursive': ('algorithms.searching.binary_search', 'binary_search_recursive'), 'binary_search_left_bound': ('algorithms.searching.binary_search', 'binary_search_left_bound'), 'linear_search': ('algorithms.searching.linear_search', 'linear_search'), 'mad': ('algorithms.hashing.mad_compression', 'mad'), 'factorial': ('algorithms.math.factorial', 'factorial'), 'factorial_for_loop': ('algorithms.math.factorial', 'factorial_for_loop'), 'fib': ('algorithms.math.fibonacci', 'fib'), 'fib_for_loop': ('algorithms.math.fibonacci', 'fib_for_loop'), 'bubble_sort': ('algorithms.sorting.bubble_sort', 'bubble_sort'), 'counting_sort': ('algorithms.sorting.counting_sort', 'counting_sort'), 'heapsort': ('algorithms.sorting.heapsort', 'heapsort'), 'heap_sort_heapq': ('algorithms.sorting.heapsort', 'heap_sort_heapq'), 'insertion_sort': ('algorithms.sorting.insertion_sort', 'insertion_sort'), 'merge': ('algorithms.sorting.mergesort', 'merge'), 'mergesort': ('algorithms.sorting.mergesort', 'mergesort'), 'quicksort': ('algorithms.sorting.quicksort', 'quicksort'), 'quicksort_in_place': ('algorithms.sorting.quicksort', 'quicksort_in_place'), 'selection_sort': ('algorithms.sorting.selection_sort', 'selection_sort'), 'selection_sort_in_place': ('algorithms.sorting.selection_sort', 'selection_sort_in_place')}


def entry(op, *args):
    if op not in _DISPATCH:
        raise ValueError("unknown operation: %s" % op)
    module_name, symbol = _DISPATCH[op]
    return getattr(importlib.import_module(module_name), symbol)(*args)
