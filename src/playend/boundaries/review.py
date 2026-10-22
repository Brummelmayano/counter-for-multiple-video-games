"""Write session_<id>/REVIEW.md, the human review sheet of a session, from units.json and labels_proposed.jsonl.

usage: python -m playend.boundaries.review session_<id>      (run playend.boundaries.build_labels first)
Optional keys of units.json used here: rules, non_countable_notes, time_segments, uncertain_frames, points_to_confirm.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from playend.annotation.lots import source_rows
from playend.common.files import read_jsonl
from playend.common.paths import BOUNDARIES, resolve
from playend.corrections.traces import trace_dirs


def image_links(session: str) -> dict[int, str]:
    """Link from the session's REVIEW.md to each frame image of its lots (the capture image when a lot holds a
    broken symlink instead of a copy)."""
    folder = BOUNDARIES / session
    return {
        fid: Path(os.path.relpath(resolve(row["image_path"]), folder)).as_posix()
        for fid, row in source_rows(session).items()
    }


def link(links, fid):
    return f"[{fid}]({links[fid]})" if fid in links else str(fid)


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the session's REVIEW.md from units.json and its labels.")
    parser.add_argument("session", help="session_<id>")
    session = parser.parse_args().session
    folder = BOUNDARIES / session
    spec = json.loads((folder / "units.json").read_text(encoding="utf-8"))
    labels = read_jsonl(folder / "labels_proposed.jsonl")
    links = image_links(session)
    units, segments = spec["units"], spec.get("time_segments", [])
    out = [
        f"# Relecture des frontières — {session}",
        "",
        "Parties proposées à partir de la relecture chronologique des observations. **À valider par un "
        "humain** "
        "avant l'entraînement du GRU : ouvrir les images citées, puis répondre « validé » ou indiquer les corrections.",
        "",
    ]
    out += ["## Parties", ""]
    if units:
        out += [
            "| Partie | Jeu / match | Images | Début | Fin établie à | Type | Score vu | Confiance |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for u in units:
            end, start = u.get("end_established_at"), u.get("start_established_at")
            if start is not None and u.get("start_status") == "author":
                start = f"{start} (auteur)"
            out.append(
                f"| {u['unit_id']} | {u['game']} — {u['description']} | {u['first_frame']}–{u['last_frame']} | "
                f"{start if start is not None else '—'} | {end if end is not None else '—'} | {u['termination']} | "
                f"{u.get('final_score_seen') or '—'} | "
                f"{u.get('label_confidence', 1.0)} |"
            )
    else:
        out.append("Aucune partie comptable dans cette session.")
    out.append("")
    if units:
        out += ["## Preuves à vérifier", ""]
        for u in units:
            ids = [u["first_frame"], u["last_frame"]] + (
                [u["end_established_at"]] if u.get("end_established_at") else []
            )
            ids = list(dict.fromkeys(ids))
            out.append(
                f"- **{u['unit_id']}** — {u['evidence']}. Images : début, dernière en partie, fin établie → "
                + ", ".join(link(links, i) for i in ids)
            )
        out.append("")
    if segments:
        out += [
            "## Passages facturés au temps (`billing_mode = temps`, aucune frontière)",
            "",
            "| Images | Jeu | Raison |",
            "|---|---|---|",
        ]
        for s in segments:
            out.append(
                f"| {link(links, s['first_frame'])}–{link(links, s['last_frame'])} | {s['game']} | {s['reason']} |"
            )
        out.append("")
    if spec.get("non_countable_notes"):
        out += ["## Hors partie (non comptable)", ""] + [f"- {n}" for n in spec["non_countable_notes"]] + [""]
    if spec.get("uncertain_frames"):
        out += ["## Intervalles masqués (`boundary_applicable = false`)", ""]
        for item in spec["uncertain_frames"]:
            last = item.get("last_frame", item["first_frame"])
            rng = link(links, item["first_frame"]) + (f"–{link(links, last)}" if last != item["first_frame"] else "")
            out.append(f"- {rng} : {item['reason']}")
        out.append("")
    if spec.get("rules"):
        out += ["## Règles appliquées", ""] + [f"- {k} : {v}" for k, v in spec["rules"].items()] + [""]
    ends = sum(label["unit_end_boundary"] for label in labels)
    learned = sum(label["boundary_applicable"] for label in labels)
    modes = {mode: sum(label["billing_mode"] == mode for label in labels) for mode in ("partie", "temps", "hors_jeu")}
    out += [
        f"Étiquettes par intervalle : `labels_proposed.jsonl` ({len(labels)} intervalles, {ends} frontières, "
        f"{learned} appris : "
        "la fin vaut 0 partout ailleurs, y compris dans les menus et écrans noirs). "
        f"`billing_mode` : partie {modes['partie']}, temps {modes['temps']}, hors_jeu {modes['hors_jeu']}.",
        "",
    ]
    corrections = [
        (trace.name, row)
        for trace in trace_dirs()
        for row in read_jsonl(trace / "correction_manifest.jsonl")
        if row["session_id"] == session
    ]
    if corrections:
        out += [
            "## Observations corrigées par des traces séparées",
            "",
            "Les lots ne sont pas modifiés : `observation_manifest.jsonl` pointe vers l'observation corrigée "
            "(`data/annotations/corrections/<trace>/`).",
            "",
        ]
        by_trace = {}
        for name, row in corrections:
            by_trace.setdefault(name, []).append(row)
        for name, items in by_trace.items():
            fields = sorted({f for r in items for f in r["corrected_fields"]})
            if len(items) <= 10:
                for r in items:
                    out.append(
                        f"- `{name}`, image {link(links, r['frame_id'])} ({', '.join(r['corrected_fields'])}) : "
                        f"{r['reason']}"
                    )
            else:
                ids = sorted(r["frame_id"] for r in items)
                out.append(
                    f"- `{name}` : {len(items)} images ({ids[0]}–{ids[-1]}), champs {', '.join(fields)} — "
                    f"{items[0]['reason']}"
                )
        out.append("")
    out += (
        ["## Points à confirmer", ""] + ([f"- {p}" for p in spec.get("points_to_confirm", [])] or ["- Aucun."]) + [""]
    )
    (folder / "REVIEW.md").write_text("\n".join(out), encoding="utf-8")
    print(f"{folder.name}/REVIEW.md written")


if __name__ == "__main__":
    main()
