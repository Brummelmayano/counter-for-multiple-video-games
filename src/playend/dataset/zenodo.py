"""Deposit the PlayEnd package on Zenodo through its REST API.

Zenodo does not keep folders, so the package is uploaded as one zip that keeps its tree. The steps are separate
because the reserved DOI must be written into the data card and croissant.json before the package is zipped:

  reserve     first release only: create a draft and reserve its DOI (nothing is public yet)
  newversion  later releases: open a new version of the published record, under the same concept DOI, drop the files
              it inherits and reserve the DOI of the new version (nothing is public yet)
  upload      zip build/playend_v<version> and upload it, then send the metadata
  publish     publish the draft: this cannot be undone, a published record can never be deleted

The version comes from docs/dataset/croissant_metadata.json ("1.1.0" gives build/playend_v1.1). The personal access
token (scopes deposit:write and deposit:actions) is read from ~/.zenodo_token or $ZENODO_TOKEN. Each version keeps its
draft's id and DOI in build/zenodo_deposition_v<version>.json (build/zenodo_deposition.json for 1.0).

usage: python -m playend.dataset.zenodo {reserve,newversion,upload,status,publish}
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import shutil
import urllib.error
import urllib.request
from pathlib import Path

from playend.common.paths import REPO

API = "https://zenodo.org/api"
TOKEN_FILE = Path.home() / ".zenodo_token"
METADATA = REPO / "docs" / "dataset" / "croissant_metadata.json"
DESCRIPTION = REPO / "docs" / "dataset" / "zenodo_description.html"
PAPER_DOI = "10.1109/ACCESS.2025.3542425"
VERSION = ".".join(json.loads(METADATA.read_text(encoding="utf-8"))["version"].split(".")[:2])
PACKAGE = REPO / "build" / f"playend_v{VERSION}"
FIRST_STATE = REPO / "build" / "zenodo_deposition.json"
STATE = FIRST_STATE if VERSION == "1.0" else REPO / "build" / f"zenodo_deposition_v{VERSION}.json"


def token() -> str:
    value = os.environ.get("ZENODO_TOKEN") or (TOKEN_FILE.read_text().strip() if TOKEN_FILE.exists() else "")
    if not value:
        raise SystemExit(f"no Zenodo token: put it in {TOKEN_FILE} or in $ZENODO_TOKEN")
    return value


def call(method: str, url: str, body: dict | None = None, data: bytes | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token()}"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    elif data is not None:
        headers["Content-Type"] = "application/octet-stream"
    request = urllib.request.Request(url if url.startswith("http") else API + url, data, headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as error:
        raise SystemExit(f"Zenodo answered {error.code}: {error.read().decode()[:2000]}") from error


def metadata() -> dict:
    # The reserved DOI is kept by asking for it again: a "doi" value would be taken for a DOI assigned elsewhere.
    meta = json.loads(METADATA.read_text(encoding="utf-8"))
    creators = []
    for person in meta["creator"]:
        given, _, family = person["name"].rpartition(" ")
        creators.append({"name": f"{family}, {given}", "affiliation": meta["affiliation"], "orcid": person["orcid"]})
    return {
        "upload_type": "dataset",
        "title": meta["alternateName"],
        "creators": creators,
        "description": DESCRIPTION.read_text(encoding="utf-8"),
        "access_right": "open",
        "license": "cc-by-nc-4.0",
        "keywords": meta["keywords"],
        "version": meta["version"],
        "language": "eng",
        "publication_date": meta["datePublished"],
        "prereserve_doi": True,
        "dates": [
            {
                "type": "Collected",
                "start": meta["rai"]["dataCollectionTimeframe"][0],
                "end": meta["rai"]["dataCollectionTimeframe"][1],
                "description": "Exact days unknown: the capture device had no reliable calendar clock.",
            }
        ],
        "related_identifiers": [
            {"identifier": PAPER_DOI, "relation": "cites", "scheme": "doi", "resource_type": "publication-article"}
        ],
    }


def reserve() -> None:
    if STATE.exists():
        raise SystemExit(f"{STATE} exists: a draft was already reserved")
    draft = call("POST", "/deposit/depositions", {"metadata": {"prereserve_doi": True}})
    state = {
        "id": draft["id"],
        "doi": draft["metadata"]["prereserve_doi"]["doi"],
        "bucket": draft["links"]["bucket"],
        "draft": draft["links"]["html"],
        "reserved": datetime.date.today().isoformat(),
    }
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    print(f"draft {state['id']}, reserved DOI {state['doi']}\n{state['draft']}")


def new_version() -> None:
    if STATE.exists():
        raise SystemExit(f"{STATE} exists: the draft of version {VERSION} was already opened")
    published = json.loads(FIRST_STATE.read_text())
    record = call("POST", f"/deposit/depositions/{published['id']}/actions/newversion")
    draft = call("GET", record["links"]["latest_draft"])
    for inherited in draft.get("files", []):  # the new version starts with a copy of the previous files
        call("DELETE", f"/deposit/depositions/{draft['id']}/files/{inherited['id']}")
    meta = {key: value for key, value in draft["metadata"].items() if key != "doi"}
    draft = call("PUT", f"/deposit/depositions/{draft['id']}", {"metadata": meta | {"prereserve_doi": True}})
    state = {
        "id": draft["id"],
        "doi": draft["metadata"]["prereserve_doi"]["doi"],
        "bucket": draft["links"]["bucket"],
        "draft": draft["links"]["html"],
        "new_version_of": published["doi"],
        "reserved": datetime.date.today().isoformat(),
    }
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    print(f"draft {state['id']} for version {VERSION}, reserved DOI {state['doi']}\n{state['draft']}")


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def upload() -> None:
    state = json.loads(STATE.read_text())
    card = (PACKAGE / "README.md").read_text(encoding="utf-8")
    if state["doi"] not in card or state["doi"] not in (PACKAGE / "croissant.json").read_text(encoding="utf-8"):
        raise SystemExit("the reserved DOI is not in README.md and croissant.json yet: update them and re-export")
    archive = Path(shutil.make_archive(str(PACKAGE), "zip", root_dir=PACKAGE.parent, base_dir=PACKAGE.name))
    sent = call("PUT", f"{state['bucket']}/{archive.name}", data=archive.read_bytes())
    if sent.get("checksum") != f"md5:{md5(archive)}":
        raise SystemExit(f"upload checksum differs: {sent.get('checksum')}")
    call("PUT", f"/deposit/depositions/{state['id']}", {"metadata": metadata()})
    print(f"uploaded {archive.name} ({archive.stat().st_size} bytes, {sent['checksum']}) and metadata")


def status() -> None:
    state = json.loads(STATE.read_text())
    draft = call("GET", f"/deposit/depositions/{state['id']}")
    meta = draft["metadata"]
    print(f"state: {draft['state']}, submitted: {draft['submitted']}, DOI: {state['doi']}")
    print(f"title: {meta.get('title')}\nlicense: {meta.get('license')}, version: {meta.get('version')}")
    print("creators:", [(c["name"], c.get("orcid")) for c in meta.get("creators", [])])
    print("files:", [(f["filename"], f["filesize"], f["checksum"]) for f in draft.get("files", [])])
    print(draft["links"]["html"])


def publish() -> None:
    state = json.loads(STATE.read_text())
    draft = call("GET", f"/deposit/depositions/{state['id']}")
    if draft["metadata"].get("prereserve_doi", {}).get("doi") != state["doi"] or not draft.get("files"):
        raise SystemExit("the draft lost its reserved DOI or has no file: check it with status before publishing")
    record = call("POST", f"/deposit/depositions/{state['id']}/actions/publish")
    print(f"published: {record['links'].get('record_html') or record['links']['html']}\nDOI: {record['doi']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Deposit the PlayEnd package on Zenodo.")
    parser.add_argument("step", choices=["reserve", "newversion", "upload", "status", "publish"])
    steps = {"reserve": reserve, "newversion": new_version, "upload": upload, "status": status, "publish": publish}
    steps[parser.parse_args().step]()


if __name__ == "__main__":
    main()
