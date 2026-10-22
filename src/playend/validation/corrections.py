"""Turn proposed corrections into items of the validation tool, in a round of their own.

A round is a folder of data/validation/ with a proposals.json (written by hand or by an analysis) and, once built, an
items.json that `python -m playend.validation.server --round <folder>` shows. The author's answers go to that
folder's results.jsonl, never to the validation_results.jsonl of the first validation.

usage: python -m playend.validation.corrections corrections_2026-10-13
"""

from __future__ import annotations

import argparse
import json

from playend.common.paths import CAPTURES, VALIDATION
from playend.validation.build_items import bare_frames, frame_view, load_sessions


def build(round_name: str) -> int:
    folder = VALIDATION / round_name
    proposals = json.loads((folder / "proposals.json").read_text(encoding="utf-8"))["proposals"]
    sessions = load_sessions()
    full_name = {name[8:16]: name for name in sessions}
    for captured in CAPTURES.glob("session_*"):  # a session never annotated: its captures are shown without values
        short = captured.name[8:16]
        if short not in full_name and any(proposal["session"] == short for proposal in proposals):
            full_name[short] = captured.name
            sessions[captured.name] = {"frames": bare_frames(captured.name)}
    items = []
    for rank, proposal in enumerate(proposals):
        session = full_name[proposal["session"]]
        frames = []
        for entry in proposal["frames"]:
            # [frame, role], or [session, frame, role] for an example taken from another session
            frame_session = full_name[entry[0]] if len(entry) == 3 else session
            frames.append(frame_view(frame_session, sessions[frame_session]["frames"], *entry[-2:]))
        items.append({
            "id": proposal["id"], "kind": "correction", "session_id": session, "jeu": proposal["jeu"],
            "titre": proposal["titre"], "groupe": proposal["groupe"], "proposition": proposal["proposition"],
            "raison": proposal["raison"], "question": proposal["question"],
            "frames": [frame for frame in frames if frame is not None],
            "ordre_risque": rank, "ordre_chrono": f"{proposal['frames'][0][-2]:08d}",
        })  # fmt: skip
    (folder / "items.json").write_text(json.dumps({"items": items}, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(items)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("round", help="folder of data/validation/ that holds proposals.json")
    args = parser.parse_args()
    print(f"{build(args.round)} items written to {VALIDATION / args.round / 'items.json'}")


if __name__ == "__main__":
    main()
