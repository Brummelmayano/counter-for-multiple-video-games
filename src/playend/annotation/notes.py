"""The note recorded with every observation: a marker, the free reading, then " || " and the summary of the saved
values (build_lot.summary).

Notes written before 2026-10-04 name the annotating model in their marker ("[Lecture Claude] "). Newer notes do not:
the model that read the image is recorded in its metadata (annotator_model).
"""

READING = "[Lecture] "
CORRECTION = "[Correction] "
READING_MARKERS = (READING, "[Lecture Claude] ")
CORRECTION_MARKERS = (CORRECTION, "[Correction Claude] ")


def strip_markers(note: str, markers: tuple[str, ...]) -> str:
    for marker in markers:
        note = note.replace(marker, "")
    return note
