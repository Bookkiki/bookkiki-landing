#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parents[1]


def git_show(ref: str, path: str) -> Optional[bytes]:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def identity(document: dict) -> tuple[str, str, str]:
    return document["termsCode"], document["version"], document["locale"]


def immutable_document_fields(document: dict) -> dict:
    """Exclude mutable latest-route aliases from immutable policy metadata."""
    return {key: value for key, value in document.items() if key != "aliases"}


def legacy_checksums(content: bytes) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line in content.decode("utf-8").splitlines():
        if line.strip():
            digest, path = line.split(maxsplit=1)
            checksums[path] = digest
    return checksums


def fail(message: str) -> None:
    print(f"immutable policy history check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} BASE_REF", file=sys.stderr)
        return 2
    base_ref = sys.argv[1]
    current = json.loads((REPO_ROOT / "policies" / "manifest.json").read_text(encoding="utf-8"))
    current_by_id = {identity(document): document for document in current["documents"]}

    previous_manifest = git_show(base_ref, "policies/manifest.json")
    if previous_manifest is not None:
        previous = json.loads(previous_manifest)
        for document in previous["documents"]:
            key = identity(document)
            current_document = current_by_id.get(key)
            if current_document is None or immutable_document_fields(
                current_document
            ) != immutable_document_fields(document):
                fail(f"existing manifest entry was changed or removed: {key}")
            previous_source = git_show(base_ref, document["sourcePath"])
            current_source = (REPO_ROOT / document["sourcePath"]).read_bytes()
            if previous_source != current_source:
                fail(f"existing policy source was changed: {document['sourcePath']}")
        return 0

    previous_checksums = git_show(base_ref, "policies/SHA256SUMS")
    if previous_checksums is None:
        fail("base ref has neither policies/manifest.json nor policies/SHA256SUMS")
    for path, digest in legacy_checksums(previous_checksums).items():
        current_source = REPO_ROOT / path
        if not current_source.is_file():
            fail(f"existing policy source was removed: {path}")
        if hashlib.sha256(current_source.read_bytes()).hexdigest() != digest:
            fail(f"existing policy source was changed: {path}")
        if not any(
            document["sourcePath"] == path and document["sha256"] == digest
            for document in current["documents"]
        ):
            fail(f"existing checksum is missing from manifest: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
