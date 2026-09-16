#!/usr/bin/env python3
"""Issue an immutable privacy-policy revision for the one-year order PDF decision."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from importlib.machinery import SourceFileLoader
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-09-15-1"


def load(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    if "DRAFT-2026-09-14" not in source or "배송 완료일부터 1년" not in source:
        raise ValueError("expected the revised one-year source copy")
    if "[계약 및 구현 검증 필요]" not in source:
        raise ValueError("supplier-copy deletion must remain visibly unverified")
    preview = load("build-bk-870-preview.py", "bk889_privacy_preview")
    operating = load("build-bk-870-operating.py", "bk889_privacy_operating")
    operating.VERSION = VERSION
    route = f"/ko-KR/policies/privacy-policy/{VERSION}"
    source_digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    draft = preview.privacy_page(source, source_digest)
    content = operating.public_html(draft, route, privacy=True).replace(
        f'href="/ko-KR/consents/overseas-transfer/{VERSION}"',
        'href="/ko-KR/consents/overseas-transfer/2026-09-15"',
    )
    path, digest = operating.add_file(route, content)
    document = operating.registration("privacy_policy", route, path, digest)
    document["effectiveAt"] = "2026-09-15"
    operating.update_manifest([document])
    print(route)


if __name__ == "__main__":
    main()
