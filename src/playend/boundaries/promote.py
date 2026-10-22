"""After an explicit human review of REVIEW.md, copy labels_proposed.jsonl to labels_human_verified.jsonl.

Run it only when the reviewer has actually checked the session. It records who validated, when, and the SHA-256
of the proposed file. An existing verified file is replaced only with --replace, after a new review of the same
session; the note then keeps the date and note of the review it replaces (the older file stays in git).

usage: python -m playend.boundaries.promote session_<id> --reviewer "Nom" [--note "corrections faites…"] [--replace]
"""

import argparse
import datetime

from playend.common.files import read_jsonl, sha256, write_jsonl
from playend.common.paths import BOUNDARIES


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("session")
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--note", default="")
    parser.add_argument("--replace", action="store_true", help="replace an earlier verified file (needs --note)")
    args = parser.parse_args()
    folder = BOUNDARIES / args.session
    src, dst = folder / "labels_proposed.jsonl", folder / "labels_human_verified.jsonl"
    note = args.note
    if dst.exists():
        if not args.replace:
            raise SystemExit(f"refusing to overwrite {dst} (use --replace after a new review)")
        if not note:
            raise SystemExit("--replace needs a --note that says what the new review changed")
        earlier = read_jsonl(dst)[0]
        note += f" ; remplace la validation du {earlier['reviewed_at_utc']} ({earlier['review_note']})"
    digest = sha256(src)
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    labels = read_jsonl(src)
    for label in labels:
        label.update(
            review_status="human_verified",
            reviewed_by=args.reviewer,
            reviewed_at_utc=stamp,
            proposed_labels_sha256=digest,
            review_note=note or None,
        )
    write_jsonl(dst, labels)
    print(f"{len(labels)} labels promoted to human_verified by {args.reviewer} -> {dst.name}")


if __name__ == "__main__":
    main()
