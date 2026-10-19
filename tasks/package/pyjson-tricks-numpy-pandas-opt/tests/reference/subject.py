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

_DISPATCH = {'strip_comment_line_with_symbol': ('json_tricks.comment', 'strip_comment_line_with_symbol'), 'strip_comments': ('json_tricks.comment', 'strip_comments'), 'json_date_time_hook': ('json_tricks.decoders', 'json_date_time_hook'), 'json_complex_hook': ('json_tricks.decoders', 'json_complex_hook'), 'json_bytes_hook': ('json_tricks.decoders', 'json_bytes_hook'), 'numeric_types_hook': ('json_tricks.decoders', 'numeric_types_hook'), 'noenum_hook': ('json_tricks.decoders', 'noenum_hook'), 'pathlib_hook': ('json_tricks.decoders', 'pathlib_hook'), 'nopathlib_hook': ('json_tricks.decoders', 'nopathlib_hook'), 'slice_hook': ('json_tricks.decoders', 'slice_hook'), 'json_set_hook': ('json_tricks.decoders', 'json_set_hook'), 'pandas_hook': ('json_tricks.decoders', 'pandas_hook'), 'nopandas_hook': ('json_tricks.decoders', 'nopandas_hook'), 'json_numpy_obj_hook': ('json_tricks.decoders', 'json_numpy_obj_hook'), 'json_nonumpy_obj_hook': ('json_tricks.decoders', 'json_nonumpy_obj_hook'), 'fallback_ignore_unknown': ('json_tricks.encoders', 'fallback_ignore_unknown'), 'json_date_time_encode': ('json_tricks.encoders', 'json_date_time_encode'), 'enum_instance_encode': ('json_tricks.encoders', 'enum_instance_encode'), 'noenum_instance_encode': ('json_tricks.encoders', 'noenum_instance_encode'), 'class_instance_encode': ('json_tricks.encoders', 'class_instance_encode'), 'json_complex_encode': ('json_tricks.encoders', 'json_complex_encode'), 'bytes_encode': ('json_tricks.encoders', 'bytes_encode'), 'numeric_types_encode': ('json_tricks.encoders', 'numeric_types_encode'), 'pathlib_encode': ('json_tricks.encoders', 'pathlib_encode'), 'slice_encode': ('json_tricks.encoders', 'slice_encode'), 'json_set_encode': ('json_tricks.encoders', 'json_set_encode'), 'pandas_encode': ('json_tricks.encoders', 'pandas_encode'), 'nopandas_encode': ('json_tricks.encoders', 'nopandas_encode'), 'numpy_encode': ('json_tricks.encoders', 'numpy_encode'), 'nonumpy_encode': ('json_tricks.encoders', 'nonumpy_encode'), 'dumps': ('json_tricks.nonp', 'dumps'), 'dump': ('json_tricks.nonp', 'dump'), 'loads': ('json_tricks.nonp', 'loads'), 'load': ('json_tricks.nonp', 'load'), 'filtered_wrapper': ('json_tricks.utils', 'filtered_wrapper'), 'get_scalar_repr': ('json_tricks.utils', 'get_scalar_repr'), 'encode_scalars_inplace': ('json_tricks.utils', 'encode_scalars_inplace'), 'encode_intenums_inplace': ('json_tricks.utils', 'encode_intenums_inplace'), 'get_module_name_from_object': ('json_tricks.utils', 'get_module_name_from_object'), 'nested_index': ('json_tricks.utils', 'nested_index')}


def entry(op, *args):
    if op not in _DISPATCH:
        raise ValueError("unknown operation: %s" % op)
    module_name, symbol = _DISPATCH[op]
    return getattr(importlib.import_module(module_name), symbol)(*args)
