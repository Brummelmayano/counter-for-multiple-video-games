"""croissant.json: the package described for software (Croissant 1.1 with the Responsible AI vocabulary).

The descriptive parts (summary, creators, RAI answers, provenance) are written by hand in
docs/dataset/croissant_metadata.json. This module adds what is computed from the package: one file object per CSV with
its SHA-256, one record set per table with its fields, types, keys and references, the labels and the folds.
"""

from __future__ import annotations

import json
from pathlib import Path

from playend.common.files import sha256
from playend.common.paths import REPO
from playend.dataset.columns import TABLES

METADATA = REPO / "docs" / "dataset" / "croissant_metadata.json"

# The standard Croissant 1.1 context, as written by mlcroissant, plus the PROV-O prefix used for provenance.
CONTEXT = {
    "@language": "en",
    "@vocab": "https://schema.org/",
    "arrayShape": "cr:arrayShape",
    "citeAs": "cr:citeAs",
    "column": "cr:column",
    "conformsTo": "dct:conformsTo",
    "containedIn": "cr:containedIn",
    "cr": "http://mlcommons.org/croissant/",
    "rai": "http://mlcommons.org/croissant/RAI/",
    "data": {"@id": "cr:data", "@type": "@json"},
    "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
    "dct": "http://purl.org/dc/terms/",
    "description": {"@container": "@language"},
    "equivalentProperty": "cr:equivalentProperty",
    "examples": {"@id": "cr:examples", "@type": "@json"},
    "extract": "cr:extract",
    "field": "cr:field",
    "fileProperty": "cr:fileProperty",
    "fileObject": "cr:fileObject",
    "fileSet": "cr:fileSet",
    "format": "cr:format",
    "includes": "cr:includes",
    "isArray": "cr:isArray",
    "isLiveDataset": "cr:isLiveDataset",
    "jsonPath": "cr:jsonPath",
    "key": "cr:key",
    "md5": "cr:md5",
    "name": {"@container": "@language"},
    "parentField": "cr:parentField",
    "path": "cr:path",
    "prov": "http://www.w3.org/ns/prov#",
    "recordSet": "cr:recordSet",
    "references": "cr:references",
    "regex": "cr:regex",
    "repeated": "cr:repeated",
    "replace": "cr:replace",
    "samplingRate": "cr:samplingRate",
    "sc": "https://schema.org/",
    "separator": "cr:separator",
    "source": "cr:source",
    "subField": "cr:subField",
    "transform": "cr:transform",
}
DATA_TYPES = {
    "string": "sc:Text",
    "object": "sc:Text",
    "integer": "sc:Integer",
    "number": "sc:Float",
    "boolean": "sc:Boolean",
}
TABLE_DESCRIPTIONS = {
    "observations": "One row per screenshot: what was read on it, its full description as JSON, provenance and labels.",
    "sessions": "One row per capture session.",
    "units": "One row per game played (unit), with its first and last screenshots and the screenshot proving its end.",
    "time_segments": "One row per stretch of play billed by time (game or mode without an end).",
    "splits": "Cross-validation fold of each session; a session lies entirely in one fold.",
    "features": "The 262 GRU input features of each screenshot (encoding 4.0), in the order of "
    "dictionary/feature_spec.json.",
}
KEYS = {
    "observations": ["session_id", "frame_id"],
    "sessions": ["session_id"],
    "units": ["session_id", "unit_id"],
    "time_segments": ["session_id", "first_frame"],
    "splits": ["session_id"],
    "features": ["session_id", "frame_id"],
}
LABELS = {("observations", "unit_end_boundary"), ("observations", "billing_mode")}
FOLDS = 5


def file_object(folder: Path, path: str, encoding: str, description: str) -> dict:
    return {
        "@type": "cr:FileObject",
        "@id": path,
        "name": path,
        "description": description,
        "contentUrl": path,
        "encodingFormat": encoding,
        "contentSize": f"{(folder / path).stat().st_size} B",
        "sha256": sha256(folder / path),
    }


def field(table: str, column: str, data_type: str, description: str) -> dict:
    out = {
        "@type": "cr:Field",
        "@id": f"{table}/{column}",
        "name": column,
        "description": description,
        "dataType": [data_type, "cr:Label"] if (table, column) in LABELS else data_type,
        "source": {"fileObject": {"@id": f"data/{table}.csv"}, "extract": {"column": column}},
    }
    # Written {"field": {"@id": ...}}: the form read by mlcroissant, the reference implementation.
    if column == "session_id" and table != "sessions":
        out["references"] = {"field": {"@id": "sessions/session_id"}}
    if table == "splits" and column == "fold":
        out["references"] = {"field": {"@id": "folds/name"}}
    return out


def record_set(table: str, fields: list[dict]) -> dict:
    keys = [{"@id": f"{table}/{column}"} for column in KEYS[table]]
    return {
        "@type": "cr:RecordSet",
        "@id": table,
        "name": table,
        "description": TABLE_DESCRIPTIONS[table],
        "key": keys[0] if len(keys) == 1 else keys,
        "field": fields,
    }


def folds_record_set() -> dict:
    return {
        "@type": "cr:RecordSet",
        "@id": "folds",
        "name": "folds",
        "description": "The five cross-validation folds. Each fold is held out once for testing while the others are "
        "used for training; splits.csv gives the fold of each session.",
        "dataType": "cr:Split",
        "key": {"@id": "folds/name"},
        "field": [{"@type": "cr:Field", "@id": "folds/name", "name": "name", "dataType": "sc:Integer"}],
        "data": [{"folds/name": fold} for fold in range(1, FOLDS + 1)],
    }


def slug(name: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


def provenance(meta: dict) -> dict:
    steps = meta["provenance"]["activities"]
    agents = {name for activity in steps for name in activity["agents"]}
    people = {creator["name"] for creator in meta["creator"]}
    activities = []
    for activity in steps:
        entry = {"@type": "prov:Activity", "@id": activity["id"], "prov:label": activity["label"]}
        if "started" in activity:
            entry["prov:startedAtTime"] = activity["started"]
            entry["prov:endedAtTime"] = activity["ended"]
        entry["prov:wasAssociatedWith"] = [{"@id": slug(name)} for name in activity["agents"]]
        activities.append(entry)
    return {
        "prov:wasDerivedFrom": {
            "@type": "prov:Entity",
            "@id": "playend-screenshots",
            "prov:label": meta["provenance"]["derivedFrom"],
        },
        "prov:wasGeneratedBy": activities,
        "prov:wasAssociatedWith": [
            {"@type": "prov:Person" if name in people else "prov:SoftwareAgent", "@id": slug(name), "name": name}
            for name in sorted(agents)
        ],
    }


def croissant(folder: Path, feature_names: list[str]) -> dict:
    meta = json.loads(METADATA.read_text(encoding="utf-8"))
    affiliation = {"@type": "sc:Organization", "name": meta["affiliation"]}
    creators = []
    for creator in meta["creator"]:
        person = {
            "@type": "sc:Person",
            "name": creator["name"],
            "sameAs": f"https://orcid.org/{creator['orcid']}",
            "affiliation": affiliation,
        }
        if "email" in creator:
            person["email"] = creator["email"]
        creators.append(person)
    distribution = [
        file_object(folder, f"data/{table}.csv", "text/csv", TABLE_DESCRIPTIONS[table])
        for table in [*TABLES, "features"]
    ]
    distribution.append(
        file_object(
            folder,
            "dictionary/feature_spec.json",
            "application/json",
            "Order and encoding of the features (version 4.0).",
        )
    )
    record_sets = [
        record_set(table, [field(table, name, DATA_TYPES[kind], english) for name, kind, _, _, english, _ in columns])
        for table, columns in TABLES.items()
    ]
    feature_fields = [
        field("features", "session_id", "sc:Text", "Capture session, as in observations.csv."),
        field("features", "frame_id", "sc:Integer", "Rank of the screenshot in its session."),
    ]
    feature_fields += [
        field("features", name, "sc:Float", "GRU input feature, defined in dictionary/feature_spec.json.")
        for name in feature_names
    ]
    record_sets += [record_set("features", feature_fields), folds_record_set()]
    out = {
        "@context": CONTEXT,
        "@type": "sc:Dataset",
        "conformsTo": ["http://mlcommons.org/croissant/1.1", "http://mlcommons.org/croissant/RAI/1.0"],
        "name": meta["name"],
        "alternateName": meta["alternateName"],
        "description": meta["description"],
        "license": meta["license"],
        "datePublished": meta["datePublished"],
        "version": meta["version"],
        "sdVersion": "1.0",
        "inLanguage": meta["inLanguage"],
        "keywords": meta["keywords"],
        "creator": creators,
        "publisher": affiliation,
        "isAccessibleForFree": True,
        "citeAs": meta["citeAs"],
    }
    if meta["url"]:
        out["url"] = meta["url"]  # the concept DOI, which leads to the latest version
    if meta.get("identifier"):
        out["identifier"] = meta["identifier"]  # the DOI of this version
    out |= {f"rai:{key}": value for key, value in meta["rai"].items()}
    out |= provenance(meta)
    out |= {"distribution": distribution, "recordSet": record_sets}
    return out
