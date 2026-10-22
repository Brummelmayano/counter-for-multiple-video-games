"""Correction traces: corrected observations stored beside the lots, never inside them.

A lot is never modified once recorded. A correction is a trace folder <trace_id>/ in the corrections
directory holding, for each corrected frame, a complete contract-2.1 observation, its metadata (who
corrected what, why, from which base file and hash) and one row of correction_manifest.jsonl. Traces
are applied in trace_id order; each row names the observation it corrects (base_annotation_path +
base_annotation_sha256), which must be the frame's effective observation at that point: the lot's own
file, or the previous correction of that frame.

effective(session) gives, per frame, the observation every consumer must read (boundary labels,
session timeline, coverage check).
"""

from __future__ import annotations

import json
from pathlib import Path

from playend.annotation.build_lot import summary
from playend.annotation.lots import session_lots
from playend.common.files import read_jsonl, sha256
from playend.common.paths import CORRECTIONS, resolve
from playend.contract.contract import validate_observation


def trace_dirs() -> list[Path]:
    return sorted(p.parent for p in CORRECTIONS.glob("*/correction_manifest.jsonl"))


def lot_entries(session: str) -> dict[int, dict]:
    """Observation recorded in the lots, per frame (no correction applied)."""
    out = {}
    for lot in session_lots(session):
        for entry in read_jsonl(lot / "annotation_manifest.jsonl"):
            out[entry["frame_id"]] = {
                "frame_id": entry["frame_id"],
                "annotation_path": entry["annotation_path"],
                "annotation_sha256": entry["annotation_sha256"],
                "metadata_path": entry["metadata_path"],
                "review_status": entry["review_status"],
                "lot": lot.name,
                "corrected_by": None,
            }
    return out


def effective(session: str, problems: list[str] | None = None) -> dict[int, dict]:
    """Per frame: the lot entry, replaced by the last correction applied to it (with 'corrected_by' = trace id).
    Inconsistencies are appended to `problems` when given, raised otherwise."""
    current = lot_entries(session)

    def fail(message):
        if problems is None:
            raise SystemExit(message)
        problems.append(message)

    for trace in trace_dirs():
        for row in read_jsonl(trace / "correction_manifest.jsonl"):
            if row["session_id"] != session:
                continue
            fid = row["frame_id"]
            base = current.get(fid)
            if base is None:
                fail(f"{trace.name}: frame {fid} corrected but not annotated in any lot")
                continue
            if row["base_annotation_path"] != base["annotation_path"]:
                fail(
                    f"{trace.name}: frame {fid} corrects {row['base_annotation_path']}, "
                    f"but the effective observation is {base['annotation_path']}"
                )
                continue
            if row["base_annotation_sha256"] != base["annotation_sha256"]:
                fail(f"{trace.name}: frame {fid} base observation hash differs from the one recorded")
            current[fid] = {
                "frame_id": fid,
                "annotation_path": row["annotation_path"],
                "annotation_sha256": row["annotation_sha256"],
                "metadata_path": row["metadata_path"],
                "review_status": row["review_status"],
                "lot": base["lot"],
                "corrected_by": trace.name,
                "corrected_fields": row["corrected_fields"],
            }
    return current


def check(session: str) -> tuple[list[str], int]:
    """Verify every correction of a session: chain, hashes, contract, note/JSON agreement. Returns (problems, count)."""
    problems: list[str] = []
    count = 0
    effective(session, problems)
    for trace in trace_dirs():
        for row in read_jsonl(trace / "correction_manifest.jsonl"):
            if row["session_id"] != session:
                continue
            count += 1
            fid = row["frame_id"]
            path = resolve(row["annotation_path"])
            if sha256(path) != row["annotation_sha256"]:
                problems.append(f"{trace.name}: frame {fid} corrected observation changed since recording")
            obs = json.loads(path.read_text(encoding="utf-8"))
            errors = validate_observation(obs)
            if errors:
                problems.append(f"{trace.name}: frame {fid} contract errors {errors}")
            meta = json.loads(resolve(row["metadata_path"]).read_text(encoding="utf-8"))
            if not (meta.get("annotation_note") or "").endswith(summary(obs)):
                problems.append(f"{trace.name}: frame {fid} note summary disagrees with corrected JSON")
            status = meta.get("review_status")
            if status != "proposed_pending_human_review" and row["review_status"] != status:
                problems.append(f"{trace.name}: frame {fid} review status mismatch")
    return problems, count
