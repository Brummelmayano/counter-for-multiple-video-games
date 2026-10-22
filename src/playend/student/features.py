"""Image features of every PlayEnd capture for the student's classifier: the 1000 ImageNet scores of MobileNetV2.

The ONNX model exposes only its last layer. Those scores are a linear map of the pooled features below them, so a
linear classifier trained on them sees almost the same information. The whole capture is reduced to 224x224 without
cropping, so the HUD at the edges stays in view. Written to build/student/features.npz.
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import numpy as np
import onnxruntime
from PIL import Image

from playend.common.paths import STUDENT_MODELS, STUDENT_OUTPUT
from playend.student.collect import OBSERVATIONS, frame_paths

MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
SIZE = 224


class ImageFeatures:
    def __init__(self, model: Path = STUDENT_MODELS / "mobilenetv2-12.onnx"):
        options = onnxruntime.SessionOptions()
        options.log_severity_level = 3
        self.session = onnxruntime.InferenceSession(str(model), options, providers=["CPUExecutionProvider"])
        self.input = self.session.get_inputs()[0].name

    def __call__(self, image: Image.Image) -> np.ndarray:
        pixels = np.asarray(image.convert("RGB").resize((SIZE, SIZE), Image.BILINEAR), dtype=np.float32) / 255.0
        tensor = ((pixels - MEAN) / STD).transpose(2, 0, 1)[None]
        return self.session.run(None, {self.input: tensor})[0][0]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=STUDENT_OUTPUT / "features.npz")
    args = parser.parse_args()
    with open(OBSERVATIONS, newline="", encoding="utf-8") as handle:
        rows = [(row["session_id"], int(row["frame_id"])) for row in csv.DictReader(handle)]
    extractor = ImageFeatures()
    vectors, start = [], time.time()
    paths, current = {}, None
    for count, (session, frame_id) in enumerate(rows, start=1):
        if session != current:
            paths, current = frame_paths(session), session
        vectors.append(extractor(Image.open(paths[frame_id])))
        if count % 1000 == 0:
            print(f"{count}/{len(rows)} frames, {count / (time.time() - start):.1f} frames/s", flush=True)
    np.savez_compressed(
        args.out,
        session=np.array([session for session, _ in rows]),
        frame=np.array([frame_id for _, frame_id in rows]),
        features=np.stack(vectors).astype(np.float32),
    )
    print(f"{len(rows)} frames -> {args.out}")


if __name__ == "__main__":
    main()
