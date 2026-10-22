"""Presets and frame helpers for writing a lot's reading spec, grouped by genre.

A preset is a partial observation that a frame merges by name; a helper such as play(199, 1, 0, "12:34") returns one
frame of the spec. Short parameter names keep the specs compact: i = frame id, a and b = score, c = clock, t = timer,
obs = free reading, st = dotted overrides, p = preset name.

Usage, with the package installed:
    python - <<'EOF'
    from playend.annotation.presets import *
    run_lot(run, lo, hi, frames)
    EOF
The annotator written in the spec is $ANNOTATOR_MODEL. Conventions by genre: docs/conventions/.
"""

from .base import *
from .battle_royale import *
from .combat import *
from .football import *
from .mission import *
from .racing import *
from .screens import *
