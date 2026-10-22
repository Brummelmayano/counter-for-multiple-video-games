"""LoRA for the VLM reader: examples from the teacher's observations, training, and merging into the model.

prepare (on this PC): for every gameplay frame of a game with zones, the mosaic the VLM sees (playend.student.vlm)
and the answer expected, written from the teacher's observation in the format of the grammar, so the model learns the
same lines it is held to. Screens without a HUD (menus, loading, cutscenes, selection screens) are added with null
everywhere, in the zones and question of a game, as the VLM gets them when the classifier takes them for gameplay: the
model learns to read nothing where there is nothing. In every session the frames after the first four fifths of its
gameplay frames are the test set, never seen in training (blocked split for data that follows each other in time).

train and merge (on the GPU machine): an adapter of rank 8 on the linear layers of the language model only, as in
Liquid AI's guide for LFM2-VL; the image encoder and its projector stay as published, so the mmproj file the Pi
already has stays valid. The loss counts only the answer, not the image or the question.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import shutil
import time
from collections import defaultdict
from pathlib import Path

LANGUAGE_LAYERS = {"q_proj", "k_proj", "v_proj", "o_proj", "out_proj", "in_proj", "gate_proj", "up_proj", "down_proj",
                   "w1", "w2", "w3"}  # fmt: skip
TEST_SHARE = 0.2
CHECKPOINT_STEPS = 25  # optimiser steps between two checkpoints, a few minutes of training
NEGATIVES = 600  # screens without a HUD, about one example in nine
# Screens where the HUD is absent; results, final tables and pause often still show a score, so they are not used.
EMPTY_SCREENS = {"menu", "loading", "cutscene", "character_select", "team_select"}
PATTERNS = {
    "clock": r"\d{1,3}:\d{2}",
    "seconds": r"\d{1,3}",
    "seconds_or_infinity": r"\d{1,3}|∞",
    "goals": r"\d{1,2}",
    "rounds": r"\d",
    "round_number": r"\d{1,2}",
    "wins": r"\d{1,3}",
    "count": r"\d{1,3}",
    "code": r"[A-Z]{3,4}",
    "name": r"[A-Za-zÀ-ÖØ-öø-ſ][A-Za-z0-9À-ÖØ-öø-ſ .()'-]{0,30}",
}


def answer(family: str, values: dict) -> str:
    """The expected answer: one `field: value` line per field, null when the teacher has no value in that format."""
    from playend.student.vlm import FIELDS

    lines = []
    for field, kind, _ in FIELDS[family][1]:
        value = values.get(field)
        text = "∞" if value == "∞" else str(value) if value is not None else ""
        lines.append(f"{field}: {text if text and re.fullmatch(PATTERNS[kind], text) else 'null'}")
    return "\n".join(lines) + "\n"


def prepare(out: Path) -> dict:
    from PIL import Image

    from playend.student.collect import OBSERVATIONS, frame_paths
    from playend.student.package import hud_values
    from playend.student.vlm import FIELDS, prompt, vlm_mosaic

    gameplay, empty = defaultdict(list), []
    with open(OBSERVATIONS, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["screen_type"] == "gameplay" and row["game_family"] in FIELDS:
                gameplay[row["session_id"]].append(row)
            elif row["screen_type"] in EMPTY_SCREENS:
                empty.append(row)
    rng = random.Random(2026)
    negatives = rng.sample(empty, min(NEGATIVES, len(empty)))
    for row in negatives:  # the game whose zones the VLM would get: the frame's own, or one taken at random
        row["family_shown"] = row["game_family"] if row["game_family"] in FIELDS else rng.choice(sorted(FIELDS))
    first_test = {
        session: int(rows[round(len(rows) * (1 - TEST_SHARE))]["frame_id"]) for session, rows in gameplay.items()
    }
    (out / "images").mkdir(parents=True, exist_ok=True)
    examples, paths = [], {}
    rows = [row for session_rows in gameplay.values() for row in session_rows] + negatives
    for row in sorted(rows, key=lambda row: (row["session_id"], int(row["frame_id"]))):
        session, frame_id = row["session_id"], int(row["frame_id"])
        family = row.get("family_shown", row["game_family"])
        if session not in paths:
            paths[session] = frame_paths(session)
        name = f"{session[8:14]}_{frame_id:05d}.png"
        image = out / "images" / name
        if not image.exists():
            vlm_mosaic(Image.open(paths[session][frame_id]).convert("RGB"), family).save(image)
        values = {} if "family_shown" in row else hud_values(json.loads(row["observation_json"]))
        examples.append({
            "session": session, "frame_id": frame_id, "family": family, "image": f"images/{name}",
            "screen": row["screen_type"], "split": "test" if frame_id >= first_test.get(session, 10**9) else "train",
            "prompt": prompt(family), "answer": answer(family, values),
        })  # fmt: skip
    with open(out / "examples.jsonl", "w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example, ensure_ascii=False) + "\n")
    return {f"{split} {kind}": sum(e["split"] == split and (e["screen"] == "gameplay") == (kind == "gameplay")
                                   for e in examples)
            for split in ("train", "test") for kind in ("gameplay", "empty")}  # fmt: skip


def read_examples(folder: Path, split: str) -> list[dict]:
    """The examples of one split, or every example with split "all" (the adapter that goes on the Pi)."""
    lines = (folder / "examples.jsonl").read_text(encoding="utf-8").splitlines()
    return [example for example in map(json.loads, lines) if split in ("all", example["split"])]


def best_device(torch) -> str:
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        return "xpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def conversation(example: dict, image, with_answer: bool) -> list[dict]:
    messages = [{"role": "user", "content": [{"type": "image", "image": image},
                                             {"type": "text", "text": example["prompt"]}]}]  # fmt: skip
    if with_answer:
        messages.append({"role": "assistant", "content": [{"type": "text", "text": example["answer"]}]})
    return messages


def training_dtype(torch, device: str):
    """bfloat16 where the card computes in it, float32 elsewhere (the processor, older cards such as the T4)."""
    if device == "cuda" and not torch.cuda.is_bf16_supported():
        return torch.float32
    return torch.float32 if device == "cpu" else torch.bfloat16


def save_checkpoint(model, optimiser, state: dict, folder: Path, torch) -> None:
    """Adapter, optimiser and position, written beside the last checkpoint then swapped in, so a cut keeps one whole."""
    partial = folder.with_name(folder.name + ".part")
    shutil.rmtree(partial, ignore_errors=True)
    model.save_pretrained(partial / "adapter")
    torch.save(optimiser.state_dict(), partial / "optimiser.pt")
    (partial / "state.json").write_text(json.dumps(state), encoding="utf-8")
    shutil.rmtree(folder, ignore_errors=True)
    partial.rename(folder)


def train(
    examples: Path,
    model_dir: Path,
    out: Path,
    epochs: int,
    rate: float,
    accumulation: int,
    limit: int | None,
    split: str = "train",
):
    import torch
    from peft import LoraConfig, get_peft_model, set_peft_model_state_dict
    from PIL import Image
    from safetensors.torch import load_file
    from transformers import AutoModelForImageTextToText, AutoProcessor

    device = best_device(torch)
    dtype = training_dtype(torch, device)
    processor = AutoProcessor.from_pretrained(model_dir)
    model = AutoModelForImageTextToText.from_pretrained(model_dir, dtype=dtype).to(device)
    targets = [name for name, module in model.named_modules()
               if isinstance(module, torch.nn.Linear) and "language_model" in name
               and name.rsplit(".", 1)[-1] in LANGUAGE_LAYERS]  # fmt: skip
    if not targets:
        raise SystemExit("no linear layer of the language model found: send the list of the model's modules")
    model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
                                             target_modules=targets))  # fmt: skip
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    optimiser = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=rate)
    train_set = read_examples(examples, split)[:limit]
    out.mkdir(parents=True, exist_ok=True)
    checkpoint = out / "checkpoint"
    state = {"epoch": 0, "examples_done": 0, "step": 0, "seconds": 0.0}
    if (checkpoint / "state.json").exists():  # a run cut by a power failure: go on from its last checkpoint
        state = json.loads((checkpoint / "state.json").read_text(encoding="utf-8"))
        set_peft_model_state_dict(model, load_file(checkpoint / "adapter" / "adapter_model.safetensors"))
        optimiser.load_state_dict(torch.load(checkpoint / "optimiser.pt", map_location=device))
        print(f"resuming at epoch {state['epoch'] + 1}, example {state['examples_done']}", flush=True)
    log = (out / "training_log.jsonl").open("a", encoding="utf-8")
    print(f"device {device} ({dtype}), {len(targets)} layers adapted, {trainable / 1e6:.2f} M trained parameters, "
          f"{len(train_set)} examples, {epochs} epoch(s)", flush=True)  # fmt: skip
    model.train()
    started, running = time.time() - state["seconds"], []
    for epoch in range(state["epoch"], epochs):
        order = list(range(len(train_set)))
        random.Random(epoch).shuffle(order)
        for count, index in enumerate(order, start=1):
            if epoch == state["epoch"] and count <= state["examples_done"]:
                continue
            example = train_set[index]
            image = Image.open(examples / example["image"]).convert("RGB")
            options = {"tokenize": True, "return_dict": True, "return_tensors": "pt"}
            full = processor.apply_chat_template(conversation(example, image, True), **options)
            question = processor.apply_chat_template(conversation(example, image, False), add_generation_prompt=True,
                                                     **options)  # fmt: skip
            inputs = {key: value.to(device) for key, value in full.items()}
            if "pixel_values" in inputs:
                inputs["pixel_values"] = inputs["pixel_values"].to(dtype)
            labels = inputs["input_ids"].clone()
            labels[:, : question["input_ids"].shape[1]] = -100
            loss = model(**inputs, labels=labels).loss
            (loss / accumulation).backward()
            running.append(loss.item())
            if count % accumulation == 0 or count == len(order):
                optimiser.step()
                optimiser.zero_grad()
                state["step"] += 1
                record = {"epoch": epoch, "step": state["step"], "examples": count,
                          "loss": sum(running) / len(running), "seconds": round(time.time() - started, 1)}  # fmt: skip
                log.write(json.dumps(record) + "\n")
                log.flush()
                if state["step"] % 10 == 0:
                    print(f"epoch {epoch + 1} step {state['step']}: loss {record['loss']:.4f}, "
                          f"{record['seconds']:.0f} s", flush=True)  # fmt: skip
                running = []
                if state["step"] % CHECKPOINT_STEPS == 0 or count == len(order):
                    state |= {"epoch": epoch + (count == len(order)), "examples_done": 0 if count == len(order)
                              else count, "seconds": time.time() - started}  # fmt: skip
                    save_checkpoint(model, optimiser, state, checkpoint, torch)
    partial = out / "adapter.part"
    model.save_pretrained(partial)
    partial.rename(out / "adapter")
    summary = {"device": device, "dtype": str(dtype), "split": split, "epochs": epochs, "rate": rate,
               "accumulation": accumulation, "examples": len(train_set), "layers": targets,
               "trained_parameters": trainable, "seconds": round(time.time() - started, 1)}  # fmt: skip
    (out / "training.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    shutil.rmtree(checkpoint, ignore_errors=True)


def merge(model_dir: Path, adapter: Path, out: Path):
    """The model with the adapter merged in, written beside then renamed, so a cut never leaves a half model."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForImageTextToText, AutoProcessor

    partial = out.with_name(out.name + ".part")
    shutil.rmtree(partial, ignore_errors=True)
    model = AutoModelForImageTextToText.from_pretrained(model_dir, dtype=torch.float32)
    model = PeftModel.from_pretrained(model, adapter).merge_and_unload()
    model.save_pretrained(partial, safe_serialization=True)
    AutoProcessor.from_pretrained(model_dir).save_pretrained(partial)
    for name in ("chat_template.jinja", "chat_template.json"):
        if (model_dir / name).exists() and not (partial / name).exists():
            (partial / name).write_bytes((model_dir / name).read_bytes())
    shutil.rmtree(out, ignore_errors=True)
    partial.rename(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="step", required=True)
    step = sub.add_parser("prepare", help="write the mosaics and the examples (on the PC with the PlayEnd frames)")
    step.add_argument("--out", type=Path, required=True)
    step = sub.add_parser("train", help="train the adapter")
    step.add_argument("--examples", type=Path, required=True)
    step.add_argument("--model", type=Path, required=True)
    step.add_argument("--out", type=Path, required=True)
    step.add_argument("--epochs", type=int, default=2)
    step.add_argument("--rate", type=float, default=2e-4)
    step.add_argument("--accumulation", type=int, default=8)
    step.add_argument("--limit", type=int, help="first examples only, to check the installation")
    step.add_argument("--split", choices=["train", "all"], default="train",
                      help="all: every example, test included, for the adapter that goes on the Pi")  # fmt: skip
    step = sub.add_parser("merge", help="merge the adapter into the model")
    step.add_argument("--model", type=Path, required=True)
    step.add_argument("--adapter", type=Path, required=True)
    step.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.step == "prepare":
        print(prepare(args.out))
    elif args.step == "train":
        train(args.examples, args.model, args.out, args.epochs, args.rate, args.accumulation, args.limit, args.split)
    else:
        merge(args.model, args.adapter, args.out)


if __name__ == "__main__":
    main()
