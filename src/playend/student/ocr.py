"""Text reader of the student: PP-OCRv6 tiny with ONNX Runtime, NumPy and Pillow only.

The same code runs on the Raspberry Pi and on a PC, so both read the same text. Detection follows the DB
post-processing of PaddleOCR with upright boxes, which suit the horizontal text of a game HUD. Settings come from the
inference.yml files published with the models.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import onnxruntime
from PIL import Image

from playend.common.paths import STUDENT_MODELS

DET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
DET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
DET_THRESH, BOX_THRESH, UNCLIP_RATIO = 0.2, 0.4, 1.4
DET_LONG_SIDE = 1280  # larger images are reduced to this; HUD mosaics are read at their own size, as measured
MIN_BOX_SIDE = 3
REC_HEIGHT, REC_MIN_WIDTH = 48, 320
TEXT_SCORE = 0.5


@dataclass
class Line:
    text: str
    score: float
    box: tuple[float, float, float, float]  # x0, y0, x1, y1 in pixels of the image read

    @property
    def centre(self) -> tuple[float, float]:
        return (self.box[0] + self.box[2]) / 2, (self.box[1] + self.box[3]) / 2


def components(mask: np.ndarray) -> list[tuple[slice, slice, np.ndarray]]:
    """Bounding slices and pixel mask of each 8-connected component: OpenCV on the Pi, SciPy elsewhere."""
    try:
        import cv2

        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
        found = []
        for label in range(1, count):
            x, y, w, h = stats[label, :4]
            rows, cols = slice(y, y + h), slice(x, x + w)
            found.append((rows, cols, labels[rows, cols] == label))
        return found
    except ImportError:
        from scipy import ndimage

        labels, _ = ndimage.label(mask, structure=np.ones((3, 3), dtype=int))
        return [
            (rows, cols, labels[rows, cols] == label)
            for label, (rows, cols) in enumerate(ndimage.find_objects(labels), start=1)
        ]


def bgr(image: Image.Image) -> np.ndarray:
    """The models were trained on OpenCV images, whose channels are in BGR order."""
    return np.asarray(image.convert("RGB"), dtype=np.float32)[:, :, ::-1]


class TextReader:
    def __init__(self, models: Path = STUDENT_MODELS, size: str = "tiny"):
        options = onnxruntime.SessionOptions()
        options.log_severity_level = 3
        # Without the arena, the buffers of a whole-capture detection are given back: 100 MB less at the peak, which
        # the Pi's 512 MB need, for the same text and a reading 14 % slower.
        options.enable_cpu_mem_arena = False
        providers = ["CPUExecutionProvider"]
        self.detector = onnxruntime.InferenceSession(str(models / f"ppocrv6_{size}_det/inference.onnx"), options,
                                                     providers=providers)  # fmt: skip
        self.recogniser = onnxruntime.InferenceSession(str(models / f"ppocrv6_{size}_rec/inference.onnx"), options,
                                                       providers=providers)  # fmt: skip
        keys = (models / f"ppocrv6_{size}_rec/keys.txt").read_text(encoding="utf-8").split("\n")[:-1]
        self.characters = ["", *keys, " "]  # index 0 is the CTC blank, the last class is the space

    def read(self, image: Image.Image) -> list[Line]:
        lines = []
        for box in self.detect(image):
            text, score = self.recognise(image.crop(tuple(round(value) for value in box)))
            if text and score >= TEXT_SCORE:
                lines.append(Line(text, score, box))
        return sorted(lines, key=lambda line: (round(line.box[1] / 10), line.box[0]))

    def detect(self, image: Image.Image) -> list[tuple[float, float, float, float]]:
        width, height = image.size
        ratio = min(1.0, DET_LONG_SIDE / max(width, height))
        size_x = max(32, round(width * ratio / 32) * 32)
        size_y = max(32, round(height * ratio / 32) * 32)
        pixels = bgr(image.resize((size_x, size_y), Image.BILINEAR)) / 255.0
        tensor = ((pixels - DET_MEAN) / DET_STD).transpose(2, 0, 1)[None].astype(np.float32)
        probability = self.detector.run(None, {"x": tensor})[0][0, 0]
        boxes = []
        for rows, cols, mask in components(probability > DET_THRESH):
            box_height, box_width = rows.stop - rows.start, cols.stop - cols.start
            if min(box_width, box_height) < MIN_BOX_SIDE or probability[rows, cols][mask].mean() < BOX_THRESH:
                continue
            grow = box_width * box_height * UNCLIP_RATIO / (2 * (box_width + box_height))
            if min(box_width, box_height) + 2 * grow < MIN_BOX_SIDE + 2:
                continue
            boxes.append((
                max(0.0, (cols.start - grow) * width / size_x),
                max(0.0, (rows.start - grow) * height / size_y),
                min(float(width), (cols.stop + grow) * width / size_x),
                min(float(height), (rows.stop + grow) * height / size_y),
            ))  # fmt: skip
        return boxes

    def recognise(self, crop: Image.Image) -> tuple[str, float]:
        width, height = crop.size
        if not width or not height:
            return "", 0.0
        resized_width = math.ceil(REC_HEIGHT * width / height)
        padded_width = max(REC_MIN_WIDTH, resized_width)
        pixels = bgr(crop.resize((resized_width, REC_HEIGHT), Image.BILINEAR)) / 255.0
        tensor = np.zeros((1, 3, REC_HEIGHT, padded_width), dtype=np.float32)
        tensor[0, :, :, :resized_width] = ((pixels - 0.5) / 0.5).transpose(2, 0, 1)
        probabilities = self.recogniser.run(None, {"x": tensor})[0][0]
        best, confidence = probabilities.argmax(axis=1), probabilities.max(axis=1)
        kept = [step for step in range(len(best)) if best[step] and (step == 0 or best[step] != best[step - 1])]
        if not kept:
            return "", 0.0
        return "".join(self.characters[best[step]] for step in kept), float(confidence[kept].mean())


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--size", default="tiny", choices=["tiny", "small"])
    args = parser.parse_args()
    reader = TextReader(size=args.size)
    for path in args.images:
        lines = reader.read(Image.open(path))
        print(f"{path.name}: " + " | ".join(f"{line.text} ({line.score:.2f})" for line in lines))


if __name__ == "__main__":
    main()
