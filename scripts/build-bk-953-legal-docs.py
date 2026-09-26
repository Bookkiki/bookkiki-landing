#!/usr/bin/env python3
"""Issue the 2026-09-26 consent pages and the 2026-09-26-1 privacy policy for BK-953.

앱이 여는 선택 기능 동의서·국외 이전 동의서에 내부 검토 표기가 남아 있었고, 원문으로 만든
공개 페이지에는 "정보 확인 중" 안내가 자동으로 붙었다. 미완성 표기와 이 안내를 모두 없앤 판을
발행하고 개인정보처리방침의 현재 주소(alias)를 새 판으로 옮긴다. 비활성 OpenRouter 문서는
"현재 사용하지 않음"을 적어 함께 발행한다. 이전 version의 bytes는 건드리지 않는다.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSENT_VERSION = "2026-09-26"
PRIVACY_VERSION = "2026-09-26-1"
PUBLISHED_ON = "2026-09-26"
PRIVACY_ALIAS = "/ko-KR/policies/privacy-policy"

COLLECTION_DOCUMENTS = (
    ("사진 캐릭터 생성", "optional_photo_character_consent"),
    ("음성 답변 변환", "optional_interview_stt_consent"),
    ("AI 인터뷰", "optional_ai_interview_consent"),
    ("AI 동화·삽화 생성", "optional_ai_story_generation_consent"),
    ("생성 결과 안전·품질 검수", "optional_openrouter_story_review_consent"),
    ("질문·동화 음성 낭독", "optional_tts_consent"),
    ("Push 알림", "optional_push_notification_consent"),
)
OVERSEAS_DOCUMENTS = (
    ("OpenAI 사진 캐릭터 생성", "overseas_openai_photo_character_consent"),
    ("Anthropic AI 인터뷰", "overseas_anthropic_interview_consent"),
    ("ElevenLabs 음성 답변 변환", "overseas_elevenlabs_stt_consent"),
    ("OpenAI 동화·삽화 생성", "overseas_openai_story_generation_consent"),
    ("OpenRouter 생성 결과 검수", "overseas_openrouter_story_review_consent"),
    ("ElevenLabs 질문·동화 음성 낭독", "overseas_elevenlabs_tts_consent"),
    ("Apple·Google Push 알림", "overseas_push_notification_consent"),
)

# 공개 문서에 남으면 안 되는 미완성 표기. 대괄호 표기는 문구와 관계없이 막는다.
BRACKET_MARKER = re.compile(r"\[[^\]\n]{0,80}(필요|확정|검증|확인|TODO|TBD)[^\]\n]{0,80}\]")
FORBIDDEN_PHRASES = ("정보 확인 중", "미확정", "확정 필요", "검증 필요", "게시해야", "확인해 기재", "별도로 고지합니다")
WARNING_BANNER = re.compile(r'\n?[ \t]*<p class="warning" role="status">.*?</p>', re.S)


def load(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def visible_text(page: str) -> str:
    page = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S)
    return re.sub(r"<[^>]+>", " ", page)


def assert_finished(label: str, text: str) -> None:
    marker = BRACKET_MARKER.search(text)
    if marker:
        raise ValueError(f"{label}: unfinished marker remains: {marker.group(0)}")
    for phrase in FORBIDDEN_PHRASES:
        if phrase in text:
            raise ValueError(f"{label}: unfinished phrase remains: {phrase}")


def without_banner(page: str, label: str) -> str:
    stripped, count = WARNING_BANNER.subn("", page)
    if count != 1:
        raise ValueError(f"{label}: expected exactly one warning banner, found {count}")
    return stripped


def publish_consents(source: str, documents, route_prefix: str, common_heading: str,
                     extra_headings: tuple[str, ...], preview, operating) -> list[dict]:
    parts = preview.sections(source)
    expected = {title for title, _ in documents} | {common_heading} | set(extra_headings)
    if set(parts) != expected:
        raise ValueError(f"{route_prefix}: source headings changed: {set(parts) ^ expected}")
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    registered: list[dict] = []
    for title, code in documents:
        if parts[title].count(f"문서 code: `{code}`") != 1:
            raise ValueError(f"document code mismatch: {code}")
        assert_finished(code, parts[title] + parts[common_heading])
        route = f"{route_prefix}/{code}/{CONSENT_VERSION}"
        rendered = preview.page(title, code, parts[title], parts[common_heading], digest)
        content = without_banner(operating.public_html(rendered, route), code)
        assert_finished(route, visible_text(content))
        path, page_digest = operating.add_file(route, content)
        document = operating.registration(code, route, path, page_digest)
        document["announcedAt"] = PUBLISHED_ON
        document["effectiveAt"] = PUBLISHED_ON
        registered.append(document)
        print(f"{route}\t{page_digest}")
    return registered


def overseas_index() -> str:
    links = "\n".join(
        f'<li><a href="/ko-KR/consents/overseas-transfer/{code}/{CONSENT_VERSION}">{title}</a></li>'
        for title, code in OVERSEAS_DOCUMENTS
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
    parser.add_argument("collection_source", type=Path)
    parser.add_argument("overseas_source", type=Path)
    parser.add_argument("privacy_source", type=Path)
    args = parser.parse_args()
    collection = args.collection_source.read_text(encoding="utf-8")
    overseas = args.overseas_source.read_text(encoding="utf-8")
    privacy = args.privacy_source.read_text(encoding="utf-8")
    for label, source in (("collection", collection), ("overseas", overseas), ("privacy", privacy)):
        if "DRAFT-2026-09-14" not in source:
            raise ValueError(f"{label}: expected the reviewed legal-copy source")
    if "공고일: `2026년 9월 26일`" not in privacy or "OpenRouter(현재 사용하지 않음)" not in privacy:
        raise ValueError("privacy: expected the 2026-09-26 source with OpenRouter disclosed")
    assert_finished("privacy source", privacy)

    preview = load("build-bk-870-preview.py", "bk953_preview")
    operating = load("build-bk-870-operating.py", "bk953_operating")

    operating.VERSION = CONSENT_VERSION
    preview.DOCUMENTS = OVERSEAS_DOCUMENTS
    documents: list[dict] = []
    documents += publish_consents(
        collection, COLLECTION_DOCUMENTS, "/ko-KR/consents/personal-information-collection",
        "공통 철회 안내", (), preview, operating,
    )
    documents += publish_consents(
        overseas, OVERSEAS_DOCUMENTS, "/ko-KR/consents/overseas-transfer",
        "철회와 삭제", ("게시 차단 조건",), preview, operating,
    )
    operating.add_file(f"/ko-KR/consents/overseas-transfer/{CONSENT_VERSION}", overseas_index())

    operating.VERSION = PRIVACY_VERSION
    route = f"/ko-KR/policies/privacy-policy/{PRIVACY_VERSION}"
    source_digest = hashlib.sha256(privacy.encode("utf-8")).hexdigest()
    content = operating.public_html(preview.privacy_page(privacy, source_digest), route, privacy=True)
    content = content.replace(
        f'href="/ko-KR/consents/overseas-transfer/{PRIVACY_VERSION}"',
        f'href="/ko-KR/consents/overseas-transfer/{CONSENT_VERSION}"',
    )
    content = without_banner(content, "privacy")
    assert_finished(route, visible_text(content))
    path, digest = operating.add_file(route, content)
    privacy_document = operating.registration("privacy_policy", route, path, digest)
    privacy_document["announcedAt"] = PUBLISHED_ON
    privacy_document["effectiveAt"] = PUBLISHED_ON
    documents.append(privacy_document)
    print(f"{route}\t{digest}")
    operating.update_manifest(documents)

    # 현재 주소를 새 판으로 옮긴다. aliases만 바뀌고 이전 version의 증빙 필드는 그대로다.
    manifest = json.loads(operating.MANIFEST.read_text(encoding="utf-8"))
    for item in manifest["documents"]:
        if item["termsCode"] != "privacy_policy":
            continue
        if item["version"] == PRIVACY_VERSION:
            item["aliases"] = [PRIVACY_ALIAS]
        elif PRIVACY_ALIAS in item["aliases"]:
            item["aliases"] = [alias for alias in item["aliases"] if alias != PRIVACY_ALIAS]
    operating.MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / PRIVACY_ALIAS.lstrip("/") / "index.html").write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
