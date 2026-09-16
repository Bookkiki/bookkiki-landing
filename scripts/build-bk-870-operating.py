#!/usr/bin/env python3
"""Add date-versioned BK-870 reading URLs without changing prior versions.

These public pages are not wired to consent submission or AI feature gates.
Unconfirmed supplier values stay visibly unconfirmed.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-09-15"
MANIFEST = ROOT / "policies" / "manifest.json"
SUMS = ROOT / "policies" / "SHA256SUMS"


def preview_module():
    source = ROOT / "scripts" / "build-bk-870-preview.py"
    spec = importlib.util.spec_from_file_location("bk870_preview", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load BK-870 renderer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_html(draft_html: str, public_path: str, privacy: bool = False) -> str:
    if draft_html.count("DRAFT-2026-09-14") != 1:
        raise ValueError("unexpected draft version in renderer output")
    result = draft_html.replace("DRAFT-2026-09-14", VERSION)
    result = result.replace(" · BK-870 초안 | Bookkiki", " | Bookkiki")
    result = result.replace(
        '<meta name="robots" content="noindex, nofollow">',
        f'<link rel="canonical" href="https://www.bookkiki.com{public_path}">',
    )
    warning = (
        "<p class=\"warning\" role=\"status\"><strong>정보 확인 중.</strong> "
        "수령자 연락처·처리 지역·보유기간 등 원문에 표시한 미확정 항목은 "
        "확인 후 새 버전으로 개정합니다. 이 공개 페이지를 여는 것만으로 "
        "동의 기록이 생성되거나 AI 기능이 활성화되지 않습니다.</p>"
    )
    result, count = re.subn(r'<p class="warning" role="status">.*?</p>', warning, result)
    if count != 1:
        raise ValueError("renderer warning changed")
    if privacy:
        result = result.replace(
            'href="/docs/BK-870/preview-pages/"',
            f'href="/ko-KR/consents/overseas-transfer/{VERSION}"',
        )
    else:
        result = result.replace(
            '<input type="checkbox" disabled aria-label="초안에서는 동의할 수 없습니다"> ',
            "동의 문구: ",
        )
    return result


def add_file(route: str, content: str) -> tuple[str, str]:
    path = route.lstrip("/") + "/index.html"
    destination = ROOT / path
    if destination.exists():
        if destination.read_text(encoding="utf-8") != content:
            raise ValueError(f"immutable document already exists with different bytes: {path}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    return path, hashlib.sha256(content.encode("utf-8")).hexdigest()


def registration(code: str, route: str, path: str, digest: str) -> dict:
    return {
        "termsCode": code,
        "version": VERSION,
        "locale": "ko-KR",
        "announcedAt": None,
        "effectiveAt": VERSION,
        "sha256": digest,
        "sourcePath": path,
        "publicPath": route,
        "aliases": [],
    }


def update_manifest(new_documents: list[dict]) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    existing = {
        (item["termsCode"], item["version"], item["locale"]): item
        for item in manifest["documents"]
    }
    for item in new_documents:
        key = (item["termsCode"], item["version"], item["locale"])
        if key in existing:
            if existing[key] != item:
                raise ValueError(f"immutable manifest entry differs: {key}")
        else:
            manifest["documents"].append(item)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SUMS.write_text(
        "".join(f'{item["sha256"]}  {item["sourcePath"]}\n' for item in manifest["documents"]),
        encoding="utf-8",
    )


def index_html(module) -> str:
    links = "\n".join(
        f'<li><a href="/ko-KR/consents/overseas-transfer/{code}/{VERSION}">'
        f"{html.escape(title)}</a></li>"
        for title, code in module.DOCUMENTS
    )
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>개인정보 국외 이전 문서 | Bookkiki</title></head>
<body style="font-family:system-ui,-apple-system,sans-serif;max-width:760px;margin:40px auto;padding:24px;line-height:1.8;color:#353744">
<h1>개인정보 국외 이전 문서</h1>
<p>목적과 이전받는 자에 따라 문서를 따로 확인해 주세요. 문서를 열어도 동의 기록은 생성되지 않습니다.</p>
<ul>{links}</ul></body></html>\n'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("overseas_source", type=Path)
    parser.add_argument("privacy_source", type=Path)
    args = parser.parse_args()
    module = preview_module()
    overseas = args.overseas_source.read_text(encoding="utf-8")
    privacy = args.privacy_source.read_text(encoding="utf-8")
    if "DRAFT-2026-09-14" not in overseas or "DRAFT-2026-09-14" not in privacy:
        raise ValueError("expected reviewed BK-870 source version")
    parts = module.sections(overseas)
    expected = {title for title, _ in module.DOCUMENTS} | {"철회와 삭제", "게시 차단 조건"}
    if set(parts) != expected:
        raise ValueError(f"source headings changed: {set(parts) ^ expected}")
    overseas_digest = hashlib.sha256(overseas.encode("utf-8")).hexdigest()
    privacy_digest = hashlib.sha256(privacy.encode("utf-8")).hexdigest()
    documents: list[dict] = []
    for title, code in module.DOCUMENTS:
        if parts[title].count(f"문서 code: `{code}`") != 1:
            raise ValueError(f"document code mismatch: {code}")
        route = f"/ko-KR/consents/overseas-transfer/{code}/{VERSION}"
        rendered = module.page(title, code, parts[title], parts["철회와 삭제"], overseas_digest)
        path, digest = add_file(route, public_html(rendered, route))
        documents.append(registration(code, route, path, digest))
        print(route)
    route = f"/ko-KR/policies/privacy-policy/{VERSION}"
    path, digest = add_file(
        route, public_html(module.privacy_page(privacy, privacy_digest), route, privacy=True)
    )
    documents.append(registration("privacy_policy", route, path, digest))
    print(route)
    add_file(f"/ko-KR/consents/overseas-transfer/{VERSION}", index_html(module))
    update_manifest(documents)


if __name__ == "__main__":
    main()
