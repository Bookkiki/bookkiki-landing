#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "policies" / "manifest.json"
SHA256SUMS_PATH = REPO_ROOT / "policies" / "SHA256SUMS"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_FIELDS = {
    "termsCode",
    "version",
    "locale",
    "announcedAt",
    "effectiveAt",
    "sha256",
    "sourcePath",
    "publicPath",
    "aliases",
}


def fail(message: str) -> None:
    raise ValueError(message)


def load_manifest() -> dict:
    with MANIFEST_PATH.open(encoding="utf-8") as file:
        manifest = json.load(file)
    if manifest.get("schemaVersion") != 1:
        fail("policies/manifest.json schemaVersion must be 1")
    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        fail("policies/manifest.json documents must be a non-empty list")
    return manifest


def parse_date(value: object, field: str, identity: tuple[str, str, str]) -> None:
    if value is None and field == "announcedAt":
        return
    if not isinstance(value, str):
        fail(f"{identity}: {field} must be an ISO date or null")
    try:
        date.fromisoformat(value)
    except ValueError:
        fail(f"{identity}: invalid {field}: {value}")


def local_file_for_route(route: str) -> Path:
    route_path = PurePosixPath(route)
    if not route.startswith("/") or ".." in route_path.parts:
        fail(f"invalid public route: {route}")
    return REPO_ROOT.joinpath(*route_path.parts[1:], "index.html")


def parse_sha256sums() -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line in SHA256SUMS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, path = line.split(maxsplit=1)
        checksums[path] = digest
    return checksums


def validate_document(document: dict, identities: set[tuple[str, str, str]]) -> None:
    missing = REQUIRED_FIELDS - document.keys()
    extra = document.keys() - REQUIRED_FIELDS
    if missing or extra:
        fail(f"manifest fields mismatch; missing={sorted(missing)}, extra={sorted(extra)}")

    identity = (document["termsCode"], document["version"], document["locale"])
    if any(not isinstance(value, str) or not value.strip() for value in identity):
        fail(f"invalid document identity: {identity}")
    if identity in identities:
        fail(f"duplicate document identity: {identity}")
    identities.add(identity)

    parse_date(document["announcedAt"], "announcedAt", identity)
    parse_date(document["effectiveAt"], "effectiveAt", identity)
    if not SHA256_PATTERN.fullmatch(document["sha256"]):
        fail(f"{identity}: sha256 must be 64 lowercase hexadecimal characters")

    source_path = PurePosixPath(document["sourcePath"])
    if source_path.is_absolute() or ".." in source_path.parts:
        fail(f"{identity}: sourcePath must stay inside the repository")
    source_file = REPO_ROOT.joinpath(*source_path.parts)
    if not source_file.is_file():
        fail(f"{identity}: missing source file {document['sourcePath']}")
    actual_digest = hashlib.sha256(source_file.read_bytes()).hexdigest()
    if actual_digest != document["sha256"]:
        fail(f"{identity}: sha256 mismatch for {document['sourcePath']}")

    public_file = local_file_for_route(document["publicPath"])
    if public_file.resolve() != source_file.resolve():
        fail(f"{identity}: publicPath does not resolve to sourcePath")

    aliases = document["aliases"]
    if not isinstance(aliases, list) or any(not isinstance(alias, str) for alias in aliases):
        fail(f"{identity}: aliases must be a list of routes")
    for alias in aliases:
        alias_file = local_file_for_route(alias)
        if not alias_file.is_file():
            fail(f"{identity}: missing alias file for {alias}")
        if alias_file.read_bytes() != source_file.read_bytes():
            fail(f"{identity}: alias content differs from immutable source: {alias}")


def validate_manifest(manifest: dict) -> None:
    identities: set[tuple[str, str, str]] = set()
    for document in manifest["documents"]:
        if not isinstance(document, dict):
            fail("each manifest document must be an object")
        validate_document(document, identities)

    manifest_checksums = {
        document["sourcePath"]: document["sha256"] for document in manifest["documents"]
    }
    file_checksums = parse_sha256sums()
    if manifest_checksums != file_checksums:
        fail("policies/SHA256SUMS must exactly match policies/manifest.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--routes", action="store_true")
    args = parser.parse_args()

    try:
        manifest = load_manifest()
        validate_manifest(manifest)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"policy manifest check failed: {error}", file=sys.stderr)
        return 1

    if args.routes:
        for document in manifest["documents"]:
            for route in [document["publicPath"], *document["aliases"]]:
                print(f"{document['sourcePath']}\t{route}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
