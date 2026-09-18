#!/usr/bin/env python3
"""Republish the purpose-specific consent pages with every review marker resolved.

BK-876에서 확정한 값으로 선택 기능 수집·이용 동의서와 국외 이전 동의서를 다시 발행한다.
OpenRouter 문서는 발행 대상에서 뺀다. 운영 두 API node 모두 key가 없어
`OpenRouterStoryPageJudgeAdapter`가 비활성이고 Worker에도 호출이 없다. 이 목적으로
나가는 데이터가 없으므로 하지 않는 처리를 공개 문서에 적지 않는다. 활성화하려면 이 목록에
다시 넣어 새 version을 발행한 뒤 앱 동의도 함께 되살려야 한다.

이전 version의 bytes는 건드리지 않는다.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-09-18"

# OpenRouter를 제외한 선택 기능 6종.
COLLECTION_DOCUMENTS = (
    ("사진 캐릭터 생성", "optional_photo_character_consent"),
    ("음성 답변 변환", "optional_interview_stt_consent"),
    ("AI 인터뷰", "optional_ai_interview_consent"),
    ("AI 동화·삽화 생성", "optional_ai_story_generation_consent"),
    ("질문·동화 음성 낭독", "optional_tts_consent"),
    ("Push 알림", "optional_push_notification_consent"),
)

# OpenRouter를 제외한 국외 이전 6종.
OVERSEAS_DOCUMENTS = (
    ("OpenAI 사진 캐릭터 생성", "overseas_openai_photo_character_consent"),
    ("Anthropic AI 인터뷰", "overseas_anthropic_interview_consent"),
    ("ElevenLabs 음성 답변 변환", "overseas_elevenlabs_stt_consent"),
    ("OpenAI 동화·삽화 생성", "overseas_openai_story_generation_consent"),
    ("ElevenLabs 질문·동화 음성 낭독", "overseas_elevenlabs_tts_consent"),
    ("Apple·Google Push 알림", "overseas_push_notification_consent"),
)

# 공개 문서에 남으면 안 되는 내부 검토 표기.
FORBIDDEN = (
    "출시 전 확정 필요",
    "구현 검증 필요",
    "계약 및 구현 검증 필요",
    "외부 법률 검토 필요",
    "log lifecycle 검증 필요",
    "연락처 확정 필요",
    "실제 처리 지역 확인 필요",
    "처리 국가 확정 필요",
)


def load(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(source: str, label: str) -> None:
    if "DRAFT-2026-09-14" not in source:
        raise ValueError(f"{label}: expected the reviewed legal-copy source")
    for marker in FORBIDDEN:
        if marker in source:
            raise ValueError(f"{label}: unresolved review marker remains: {marker}")
    if "openrouter" in source.lower() or "OpenRouter" in source:
        raise ValueError(f"{label}: OpenRouter must be removed from the source")


def publish(module_name: str, source: str, documents, route_prefix: str,
            common_heading: str, operating, preview, check: bool,
            extra_headings: tuple[str, ...] = ()) -> list[dict]:
    parts = preview.sections(source)
    expected = {title for title, _ in documents} | {common_heading} | set(extra_headings)
    if set(parts) != expected:
        raise ValueError(f"{module_name}: source headings changed: {set(parts) ^ expected}")
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    registered: list[dict] = []
    for title, code in documents:
        if parts[title].count(f"문서 code: `{code}`") != 1:
            raise ValueError(f"document code mismatch: {code}")
        route = f"{route_prefix}/{code}/{VERSION}"
        rendered = preview.page(title, code, parts[title], parts[common_heading], digest)
        content = operating.public_html(rendered, route)
        if check:
            print(f"{route}\t{hashlib.sha256(content.encode('utf-8')).hexdigest()}")
            continue
        path, page_digest = operating.add_file(route, content)
        registered.append(operating.registration(code, route, path, page_digest))
        print(f"{route}\t{page_digest}")
    return registered


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("collection_source", type=Path)
    parser.add_argument("overseas_source", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    collection = args.collection_source.read_text(encoding="utf-8")
    overseas = args.overseas_source.read_text(encoding="utf-8")
    verify(collection, "collection-use")
    verify(overseas, "overseas-transfer")

    preview = load("build-bk-870-preview.py", "bk876_preview")
    operating = load("build-bk-870-operating.py", "bk876_operating")
    operating.VERSION = VERSION
    preview.DOCUMENTS = OVERSEAS_DOCUMENTS

    documents: list[dict] = []
    documents += publish(
        "collection-use", collection, COLLECTION_DOCUMENTS,
        "/ko-KR/consents/personal-information-collection", "공통 철회 안내",
        operating, preview, args.check,
    )
    documents += publish(
        "overseas-transfer", overseas, OVERSEAS_DOCUMENTS,
        "/ko-KR/consents/overseas-transfer", "철회와 삭제",
        operating, preview, args.check, extra_headings=("게시 차단 조건",),
    )
    if not args.check:
        operating.update_manifest(documents)


if __name__ == "__main__":
    main()
