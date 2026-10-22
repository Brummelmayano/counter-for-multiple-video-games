"""Record a correction trace: corrected contract-2.1 observations stored in corrections/<trace_id>/, never in a lot.

The base of each corrected frame is its effective observation (lot file or previous correction, see
traces.py). A 2.0 base is first upgraded in memory (secondary_counters=null); the correction then sets
only the fields it names. The JSON and the "Valeurs JSON" part of the note are generated from the same values,
and the free-text reading must not cite an "a–b" pair different from score.a/score.b (same rule as
playend.annotation.build_lot). An existing trace folder is never overwritten.

Spec file (JSON):
{
  "trace_id": "20260929_01_...",          # folder name; traces are applied in this order
  "title": "...", "reason": "why this trace exists",
  "session": "session_<id>",              # default session of the frames (optional)
  "confirmed_unchanged": [610, 624],      # frames re-read whose observation was already right (listed in README only)
  "frames": [
    {"id": 55, "session": "session_<id>", "reason": "optional, per frame",
     "obs": "free-text reading of the image (required)",
     "set": {"state.phase": "active", "result": {...}},      # any dotted path of the observation
     "cnt": [{"kind": ..., "side": ..., "value": ..., "total": ..., "label": ...}],   # -> secondary_counters
     "s": [a, b] | null, "c": "12:34" | null, "pd": [type, number, total],          # same shortcuts as the lots
     "method": "...", "image_input": "..."}   # optional, when the frame was not read on zoomed crops
  ]
}
"method" and "image_input" may also be given once for the whole trace; by default the metadata say that the frame was
read on the complete image plus zoomed crops.
The corrector recorded in the metadata is $ANNOTATOR_MODEL, the model that really re-read the images.

usage: python -m playend.corrections.build SPEC.json [--dry-run]
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from playend.annotation.build_lot import PAIR, set_path, summary, to_seconds
from playend.annotation.notes import CORRECTION
from playend.common.files import sha256, write_jsonl
from playend.common.paths import CORRECTIONS, relative, resolve
from playend.common.provenance import annotator_model
from playend.contract.contract import upgrade_v20, validate_observation
from playend.corrections.traces import effective

METHOD = "correction_trace_zoomed_hud_plus_full_frame"
IMAGE_INPUT = "complete_original_frame_plus_zoomed_crops"


def flatten(obj, prefix=""):
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            out.update(flatten(value, f"{prefix}{key}."))
        return out
    return {prefix[:-1]: obj}


def apply(base, frame):
    obs = copy.deepcopy(base)
    if "s" in frame:
        if frame["s"] is None:
            obs["score"].update(a=None, b=None, type=None)
        else:
            obs["score"]["a"], obs["score"]["b"] = frame["s"]
    if "c" in frame:
        display = frame["c"]
        obs["clock"] = (
            {"visible": False, "display": None, "value_seconds": None, "direction": None}
            if display is None
            else {"visible": True, "display": display, "value_seconds": to_seconds(display), "direction": "unknown"}
        )
    if "pd" in frame:
        obs["period"] = dict(zip(("type", "number", "total"), frame["pd"]))
    for dotted, value in frame.get("set", {}).items():
        set_path(obs, dotted, copy.deepcopy(value))
    if "cnt" in frame:
        obs["secondary_counters"] = copy.deepcopy(frame["cnt"])
    return obs


def main():
    parser = argparse.ArgumentParser(description="Record a correction trace from its reading spec.")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="check the spec without writing anything")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    trace_id = spec["trace_id"]
    out_dir = CORRECTIONS / trace_id
    if out_dir.exists() and not args.dry_run:
        raise SystemExit(f"{relative(out_dir)} exists: a recorded trace is never overwritten")
    problems, records, bases = [], [], {}
    seen = set()
    for frame in spec["frames"]:
        session = frame.get("session", spec.get("session"))
        fid = frame["id"]
        if (session, fid) in seen:
            problems.append(f"{session} {fid}: corrected twice in one trace")
            continue
        seen.add((session, fid))
        if session not in bases:
            bases[session] = effective(session)
        entry = bases[session].get(fid)
        if entry is None:
            problems.append(f"{session} {fid}: frame not annotated")
            continue
        base_path = resolve(entry["annotation_path"])
        if sha256(base_path) != entry["annotation_sha256"]:
            problems.append(f"{session} {fid}: base observation changed since recording")
        base = json.loads(base_path.read_text(encoding="utf-8"))
        base_meta = json.loads(resolve(entry["metadata_path"]).read_text(encoding="utf-8"))
        if sha256(resolve(base_meta["image_path"])) != base_meta["image_sha256"]:
            problems.append(f"{session} {fid}: image hash mismatch")
        upgraded_from = base["schema_version"]
        if upgraded_from == "2.0":
            base = upgrade_v20(base)
        obs = apply(base, frame)
        errors = validate_observation(obs)
        if errors:
            problems.append(f"{session} {fid}: contract errors {errors}")
        before, after = flatten(base), flatten(obs)
        changed = sorted(k for k in after if k != "schema_version" and before.get(k) != after[k])
        if not changed and upgraded_from != "2.0":
            problems.append(f"{session} {fid}: correction changes nothing")
        elif not changed:
            changed = ["schema_version"]  # contract upgrade only: the re-reading confirmed the upgraded values
        text = (frame.get("obs") or "").strip()
        if not text:
            problems.append(f"{session} {fid}: empty reading")
        pairs = {(int(x), int(y)) for x, y in PAIR.findall(text)}
        declared = (obs["score"]["a"], obs["score"]["b"])
        if pairs and declared not in pairs:
            problems.append(f"{session} {fid}: reading mentions {sorted(pairs)} but JSON score is {declared}")
        reading = {
            "annotation_method": frame.get("method", spec.get("method", METHOD)),
            "image_input": frame.get("image_input", spec.get("image_input", IMAGE_INPUT)),
        }
        reason = frame.get("reason") or spec["reason"]
        records.append((session, fid, entry, base_meta, upgraded_from, obs, changed, text, reason, reading))
    if problems:
        raise SystemExit("\n".join(problems))
    if args.dry_run:
        print(f"dry run: {len(records)} corrections valid")
        return
    annotator = annotator_model()
    manifest = []
    for session, fid, entry, base_meta, upgraded_from, obs, changed, text, reason, reading in records:
        folder = out_dir / "observations" / session
        folder.mkdir(parents=True, exist_ok=True)
        obs_path = folder / f"frame_{fid:08d}.observation.json"
        meta_path = folder / f"frame_{fid:08d}.metadata.json"
        obs_path.write_text(json.dumps(obs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        note = f"{CORRECTION}{text} || {summary(obs)}"
        meta = {
            "session_id": session,
            "frame_id": fid,
            "image_path": base_meta["image_path"],
            "image_sha256": base_meta["image_sha256"],
            "schema_version": obs["schema_version"],
            "schema_upgraded_from": upgraded_from if upgraded_from != obs["schema_version"] else None,
            "annotator_model": annotator,
            **reading,
            "correction_trace": trace_id,
            "correction_reason": reason,
            "corrected_fields": changed,
            "unchanged_fields_source": f"repris sans relecture de l'observation de base "
            f"({base_meta['annotator_model']})",
            "base_annotation_path": entry["annotation_path"],
            "base_annotation_sha256": entry["annotation_sha256"],
            "base_annotator_model": base_meta["annotator_model"],
            "base_annotation_note": base_meta.get("annotation_note"),
            "review_status": "proposed_pending_human_review",
            "validation_errors": [],
            "annotation_note": note,
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest.append(
            {
                "session_id": session,
                "frame_id": fid,
                "image_sha256": base_meta["image_sha256"],
                "base_annotation_path": entry["annotation_path"],
                "base_annotation_sha256": entry["annotation_sha256"],
                "annotation_path": relative(obs_path),
                "annotation_sha256": sha256(obs_path),
                "metadata_path": relative(meta_path),
                "corrected_fields": changed,
                "reason": reason,
                "review_status": "proposed_pending_human_review",
                "schema_version": obs["schema_version"],
            }
        )
    write_jsonl(out_dir / "correction_manifest.jsonl", manifest)
    (out_dir / "reading_spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_readme(out_dir, spec, manifest, annotator)
    print(f"{trace_id}: {len(manifest)} corrected observations -> {relative(out_dir)}")


def ranges(ids):
    ids, out = sorted(ids), []
    for i in ids:
        if out and i == out[-1][1] + 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    return ", ".join(f"{x}" if x == y else f"{x}–{y}" for x, y in out)


def write_readme(out_dir, spec, manifest, annotator):
    lines = [
        f"# Trace de correction {spec['trace_id']}",
        "",
        spec.get("title", ""),
        "",
        f"- Correcteur : {annotator}",
        f"- Raison : {spec['reason']}",
        "- Les lots d'origine ne sont pas modifiés : chaque observation corrigée (contrat 2.1) est ici, avec la "
        "référence et l'empreinte de l'observation qu'elle remplace (`correction_manifest.jsonl`).",
        "- Statut : `proposed_pending_human_review`.",
        "",
    ]
    by_session = {}
    for m in manifest:
        by_session.setdefault(m["session_id"], []).append(m)
    if len(manifest) <= 40:
        lines += ["| Session | Image | Champs corrigés | Raison |", "|---|---|---|---|"]
        for m in manifest:
            lines.append(
                f"| {m['session_id'][8:14]} | {m['frame_id']} | {', '.join(m['corrected_fields'])} | {m['reason']} |"
            )
    else:
        lines += ["| Session | Images corrigées | Nombre | Champs corrigés |", "|---|---|---|---|"]
        for session, items in by_session.items():
            fields = sorted({f for m in items for f in m["corrected_fields"]})
            lines.append(
                f"| {session[8:14]} | {ranges(m['frame_id'] for m in items)} | {len(items)} | {', '.join(fields)} |"
            )
    if spec.get("confirmed_unchanged"):
        lines += [
            "",
            f"Relues sans changement (observation déjà exacte) : images {ranges(spec['confirmed_unchanged'])}.",
        ]
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
