#!/usr/bin/env python3
"""Issue the 2026-10-16 AI story generation consent pages with the diary photo section (BK-1336).

아이 일기 모드에서 일기 사진을 OpenAI로 보내 글씨를 읽고 회사 서버에 10일 보관한 뒤 삭제하는 처리를
알리기 위해 `optional_ai_story_generation_consent`와 `overseas_openai_story_generation_consent` 두 문서만
새 판으로 발행한다. 원문은 bookkiki-server `docs/policies/legal-copy`의 두 파일이며, 렌더링·내부 표기 제거·
개발자식 표현 검사는 2026-09-26-2 판(build-bk-953-plain-wording.py)과 같다.

원문에서 일기 절을 빼고 2026-09-26-2로 렌더링하면 기존 판과 bytes가 같아야 한다. 다르면 일기 절 밖의 문장도
바뀐 것이므로 발행을 멈춘다. 다른 동의서·개인정보처리방침·국외 이전 문서 목록과 이전 version의 bytes는
건드리지 않는다.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-10-16"
PREVIOUS_VERSION = "2026-09-26-2"
PUBLISHED_ON = "2026-10-16"
DIARY_HEADING = "### 아이의 일기·글로 동화를 만드는 경우"
# 두 문서의 일기 절은 모두 이 문장으로 끝난다.
DIARY_END = "사진을 보내고 싶지 않으면 일기 글을 직접 입력할 수 있습니다.\n\n"
DOCUMENTS = (
    (
        "/ko-KR/consents/personal-information-collection",
        "AI 동화·삽화 생성",
        "optional_ai_story_generation_consent",
        "공통 철회 안내",
    ),
    (
        "/ko-KR/consents/overseas-transfer",
        "OpenAI 동화·삽화 생성",
        "overseas_openai_story_generation_consent",
        "철회와 삭제",
    ),
)


def load(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


labels = load("build-bk-953-without-internal-labels.py", "bk1336_labels")
bk953 = load("build-bk-953-legal-docs.py", "bk1336_bk953")
plain = load("build-bk-953-plain-wording.py", "bk1336_plain")
preview = load("build-bk-870-preview.py", "bk1336_preview")
operating = load("build-bk-870-operating.py", "bk1336_operating")


def without_diary(source: str, code: str) -> str:
    start = source.find(DIARY_HEADING)
    if start < 0 or source.count(DIARY_HEADING) != 1:
        raise ValueError(f"{code}: expected exactly one diary section")
    end = source.find(DIARY_END, start)
    if end < 0:
        raise ValueError(f"{code}: diary section end not found")
    return source[:start] + source[end + len(DIARY_END):]


def render(source: str, prefix: str, title: str, code: str, common: str, version: str) -> tuple[str, str]:
    if "DRAFT-2026-09-14" not in source:
        raise ValueError(f"{code}: expected the reviewed legal-copy source")
    parts = preview.sections(source)
    if parts[title].count(f"문서 code: `{code}`") != 1:
        raise ValueError(f"document code mismatch: {code}")
    operating.VERSION = version
    route = f"{prefix}/{code}/{version}"
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    rendered = preview.page(title, code, parts[title], parts[common], digest)
    page = bk953.without_banner(operating.public_html(rendered, route), code)
    for pattern in labels.INTERNAL_LABELS:
        page = pattern.sub("", page)
    text = bk953.visible_text(page)
    bk953.assert_finished(route, text)
    remaining = labels.REMAINING_LABEL.search(text) or plain.DEVELOPER_TERMS.search(text)
    if remaining:
        raise ValueError(f"{route}: internal or developer wording remains: {remaining.group(0)}")
    return route, page


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("collection_source", type=Path)
    parser.add_argument("overseas_source", type=Path)
    args = parser.parse_args()
    sources = (
        args.collection_source.read_text(encoding="utf-8"),
        args.overseas_source.read_text(encoding="utf-8"),
    )

    registered: list[dict] = []
    for source, (prefix, title, code, common) in zip(sources, DOCUMENTS):
        previous_route, previous_page = render(
            without_diary(source, code), prefix, title, code, common, PREVIOUS_VERSION
        )
        previous_path = ROOT / previous_route.lstrip("/") / "index.html"
        if previous_path.read_text(encoding="utf-8") != previous_page:
            raise ValueError(f"{code}: source differs from {PREVIOUS_VERSION} outside the diary section")

        route, page = render(source, prefix, title, code, common, VERSION)
        path, page_digest = operating.add_file(route, page)
        document = operating.registration(code, route, path, page_digest)
        document["announcedAt"] = PUBLISHED_ON
        document["effectiveAt"] = PUBLISHED_ON
        registered.append(document)
        print(f"{route}\t{page_digest}")
    operating.VERSION = VERSION
    operating.update_manifest(registered)


if __name__ == "__main__":
    main()
