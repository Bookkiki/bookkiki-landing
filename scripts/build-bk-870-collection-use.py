#!/usr/bin/env python3
"""Generate immutable purpose-specific collection/use pages from the Server copy."""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import re
from pathlib import Path

from importlib.machinery import SourceFileLoader


ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-09-15"
DOCUMENTS = (
    ("사진 캐릭터 생성", "optional_photo_character_consent"),
    ("음성 답변 변환", "optional_interview_stt_consent"),
    ("AI 인터뷰", "optional_ai_interview_consent"),
    ("AI 동화·삽화 생성", "optional_ai_story_generation_consent"),
    ("생성 결과 안전·품질 검수", "optional_openrouter_story_review_consent"),
    ("질문·동화 음성 낭독", "optional_tts_consent"),
    ("Push 알림", "optional_push_notification_consent"),
)


def load_script(name: str, module_name: str):
    source = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(source)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operating_html(draft_html: str, route: str, unverified: bool) -> str:
    if draft_html.count("DRAFT-2026-09-14") != 1:
        raise ValueError("unexpected draft version in rendered page")
    result = draft_html.replace("DRAFT-2026-09-14", VERSION)
    result = result.replace(" · BK-870 초안 | Bookkiki", " | Bookkiki")
    result = result.replace(
        '<meta name="robots" content="noindex, nofollow">',
        f'<link rel="canonical" href="https://www.bookkiki.com{route}">',
    )
    notice = (
        '<strong>구현 검증 중인 내용이 포함된 선택 기능별 개인정보 수집·이용 안내.</strong> '
        '원문에 표시된 [구현 검증 필요] 항목은 실제 운영 동작 확인 후 새 버전으로 정정합니다. '
        if unverified else '<strong>선택 기능별 개인정보 수집·이용 안내.</strong> '
    )
    result, warnings = re.subn(
        r'<p class="warning" role="status">.*?</p>',
        '<p class="warning" role="status">'
        + notice +
        '이 원문을 열어보는 것만으로 동의가 기록되지 않습니다. '
        '해당 기능의 동의 화면에서 별도로 선택할 수 있습니다.</p>',
        result,
    )
    if warnings != 1:
        raise ValueError("renderer warning changed")
    result = result.replace(
        "각 기능의 국외 이전은 별도로 동의받아야 합니다. 회사 저장소의 삭제기한과 공급자 보유기간은 다릅니다.",
        "각 선택 기능의 개인정보 수집·이용은 별도로 동의받습니다. 국외 이전 동의는 별도 원문을 확인해 주세요.",
    )
    result = result.replace(
        '<input type="checkbox" disabled aria-label="초안에서는 동의할 수 없습니다"> ',
        "동의 문구: ",
    )
    return result


def index_html() -> str:
    links = "\n".join(
        f'<li><a href="/ko-KR/consents/personal-information-collection/{code}/{VERSION}">'
        f"{html.escape(title)}</a></li>"
        for title, code in DOCUMENTS
    )
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>선택 기능 개인정보 수집·이용 동의서 | Bookkiki</title></head>
<body style="font-family:system-ui,-apple-system,sans-serif;max-width:760px;margin:40px auto;padding:24px;line-height:1.8;color:#353744">
<h1>선택 기능 개인정보 수집·이용 동의서</h1>
<p>기능별 문서를 따로 확인해 주세요. 문서를 열어도 동의 기록은 생성되지 않습니다.</p>
<ul>{links}</ul></body></html>\n'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--allow-unverified", action="store_true")
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    if "DRAFT-2026-09-14" not in source:
        raise ValueError("expected reviewed source version")
    unverified = "[구현 검증 필요]" in source or "[출시 전 확정 필요" in source
    if unverified and not args.allow_unverified:
        raise ValueError("unverified operating deletion statement remains in source")
    preview = load_script("build-bk-870-preview.py", "bk870_preview_collection")
    operating = load_script("build-bk-870-operating.py", "bk870_operating_collection")
    parts = preview.sections(source)
    expected = {title for title, _ in DOCUMENTS} | {"공통 철회 안내"}
    if set(parts) != expected:
        raise ValueError(f"source headings changed: {set(parts) ^ expected}")
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    documents = []
    for title, code in DOCUMENTS:
        if parts[title].count(f"문서 code: `{code}`") != 1:
            raise ValueError(f"document code mismatch: {code}")
        route = f"/ko-KR/consents/personal-information-collection/{code}/{VERSION}"
        rendered = preview.page(title, code, parts[title], parts["공통 철회 안내"], digest)
        path, page_digest = operating.add_file(route, operating_html(rendered, route, unverified))
        documents.append(operating.registration(code, route, path, page_digest))
        print(route)
    operating.add_file(
        f"/ko-KR/consents/personal-information-collection/{VERSION}", index_html()
    )
    operating.update_manifest(documents)


if __name__ == "__main__":
    main()
