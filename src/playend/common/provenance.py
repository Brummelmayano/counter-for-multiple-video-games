"""Who reads the frames.

Every lot and every correction records the model that actually looked at the images. The name comes from the
ANNOTATOR_MODEL environment variable and is never guessed: a missing name stops the tool before anything is written.
"""

import os


def annotator_model() -> str:
    name = os.environ.get("ANNOTATOR_MODEL", "").strip()
    if not name:
        raise SystemExit(
            'ANNOTATOR_MODEL is not set: export ANNOTATOR_MODEL="<model name> (<model id>, <tool>)", '
            "naming the model that really reads the frames"
        )
    return name
