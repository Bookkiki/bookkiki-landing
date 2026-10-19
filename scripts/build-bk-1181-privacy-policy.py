#!/usr/bin/env python3
"""Prepare the immutable 2026-10-19 privacy-policy revision for BK-1181.

보호자가 허용한 아이의 댓글 입력과 안전 검사 국외 처리를 새 판으로 고지한다.
이전 원문은 보존하고 현재 alias만 새 판으로 옮긴다. 실행은 로컬 발행본 생성이며 공개 배포와 다르다.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-10-19"
ANNOUNCED = "2026-10-19"
EFFECTIVE = "2026-10-19"
ALIAS = "/ko-KR/policies/privacy-policy"
ROUTE = f"/ko-KR/policies/privacy-policy/{VERSION}"
# 국외 이전 동의서 목록은 2026-09-26-2 판이 최신이다(2026-09-27 판과 같은 주소).
OVERSEAS_INDEX_VERSION = "2026-09-26-2"
COMMUNITY_RULES_URL = "https://www.bookkiki.com/ko-KR/policies/community-rules/2026-10-19"

HEADER = (
    "- 공고일: `2026년 10월 19일`",
    "- 시행일: `2026년 10월 19일`",
)
# 앞선 개정본의 고지가 사라지면 안 된다(BK-951·BK-962와 같다).
EARLIER_DISCLOSURES = (
    "Langfuse GmbH",
    "제28조의8 제1항 제3호",
    "주식회사 코리아포트원(PortOne)",
    "| Sweetbook |",
    "별도의 본인확인 업체를 이용하지 않습니다",
    "1. 아이 홈에서 설정을 눌러 보호자 공간을 엽니다.\n"
    "2. 맨 아래 계정 탈퇴를 누릅니다.\n"
    '3. 삭제되는 항목을 확인하고 다음을 누른 뒤, 입력란에 "탈퇴"를 입력하고 탈퇴하기를 누릅니다.',
    "자녀 한 명의 정보만 지우려면 설정의 아이 목록에서 자녀를 고르고",
    "`contact@bookkiki.com`으로 탈퇴·삭제·열람 등을 요청할 수 있습니다.",
    "### 탈퇴 후에도 보관하는 정보",
)
REMOVED_APP_PATHS = ("설정 > 로그아웃 · 계정 탈퇴", "설정 > 자녀 프로필 관리")
# 이번 판에서 새로 들어간 게시판 고지.
COMMUNITY_DISCLOSURES = (
    "아이 화면에서 누른 좋아요 포함",
    "보호자가 댓글 작성을 허용한 아이",
    "현재 보호자 계정·현재 기기",
    "게시판 댓글은 공개 전에 안전 검사를 위해 Anthropic",
    "이벤트 이름 43종",
    "단어 뜻과 소리 조각을 만들기 위해 Anthropic",
    "| 게시판 게시물·댓글 |",
)
COMMUNITY_LINK = "](community-rules-v2.md)"
OVERSEAS_LINK = "](overseas-transfer-consent.md)"


def load(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_source(source: str) -> None:
    if "- version: `2026-10-19`" not in source:
        raise ValueError("expected the reviewed legal-copy source")
    for line in HEADER:
        if line not in source:
            raise ValueError(f"announcement and effective dates changed: {line}")
    for phrase in EARLIER_DISCLOSURES:
        if phrase not in source:
            raise ValueError(f"earlier disclosure must survive this revision: {phrase}")
    for removed in REMOVED_APP_PATHS:
        if removed in source:
            raise ValueError(f"legal-copy source still has the removed app path: {removed}")
    for phrase in COMMUNITY_DISCLOSURES:
        if phrase not in source:
            raise ValueError(f"missing community disclosure: {phrase}")
    for link in (COMMUNITY_LINK, OVERSEAS_LINK):
        if source.count(link) != 1:
            raise ValueError(f"expected exactly one link: {link}")


def published_markdown(source: str) -> str:
    """렌더러는 http(s) 링크와 국외 이전 동의서 링크만 anchor로 만든다. 게시판 이용 규칙은 공개 주소로 바꾼다."""
    body = source.replace(COMMUNITY_LINK, f"]({COMMUNITY_RULES_URL})")
    remaining = body.replace(OVERSEAS_LINK, "")
    if ".md)" in remaining:
        raise ValueError("relative Markdown link remains")
    return body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="bookkiki-server docs/policies/legal-copy/privacy-policy-v2.md")
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    validate_source(source)

    preview = load("build-bk-870-preview.py", "bk1181_privacy_preview")
    operating = load("build-bk-870-operating.py", "bk1181_privacy_operating")
    bk953 = load("build-bk-953-legal-docs.py", "bk1181_bk953")
    labels = load("build-bk-953-without-internal-labels.py", "bk1181_labels")
    plain = load("build-bk-953-plain-wording.py", "bk1181_plain")
    bk953.assert_finished("privacy source", source)

    operating.VERSION = VERSION
    source_digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    # 기존 렌더러의 내부 version 표식만 맞춘다. 아래 단계에서 내부 메타데이터는 제거되며
    # 원문 검증과 source_digest는 실제 2026-10-19 원문을 기준으로 한다.
    render_source = published_markdown(source).replace(
        "- version: `2026-10-19`", "- version: `DRAFT-2026-09-14`", 1
    )
    draft = preview.privacy_page(render_source, source_digest)
    content = operating.public_html(draft, ROUTE, privacy=True)

    overseas_href = f'href="/ko-KR/consents/overseas-transfer/{VERSION}"'
    if content.count(overseas_href) != 1:
        raise ValueError("expected exactly one overseas-transfer consent link")
    if not (ROOT / "ko-KR/consents/overseas-transfer" / OVERSEAS_INDEX_VERSION / "index.html").is_file():
        raise ValueError(f"overseas-transfer index {OVERSEAS_INDEX_VERSION} is not published")
    content = content.replace(
        overseas_href, f'href="/ko-KR/consents/overseas-transfer/{OVERSEAS_INDEX_VERSION}"'
    )

    # 2026-09-27 판과 같은 형식: 경고 문구, 문서 code·version 줄, 원본 해시 footer를 뺀다.
    content = bk953.without_banner(content, "privacy")
    for pattern in labels.INTERNAL_LABELS:
        content = pattern.sub("", content)
    text = bk953.visible_text(content)
    remaining = labels.REMAINING_LABEL.search(text) or plain.DEVELOPER_TERMS.search(text)
    if remaining:
        raise ValueError(f"internal or developer wording remains: {remaining.group(0)}")
    bk953.assert_finished(ROUTE, text)

    expected_markup = (
        f'<link rel="canonical" href="https://www.bookkiki.com{ROUTE}">',
        "<title>개인정보처리방침 | Bookkiki</title>",
        "<li>공고일: <code>2026년 10월 19일</code></li>\n<li>시행일: <code>2026년 10월 19일</code></li>",
        f'<a href="{COMMUNITY_RULES_URL}" rel="noopener noreferrer">게시판 이용 규칙</a>',
        f'<a href="/ko-KR/consents/overseas-transfer/{OVERSEAS_INDEX_VERSION}" rel="noopener noreferrer">'
        "개인정보 국외 이전 동의서</a>",
        "<td>게시판 게시물·댓글</td>",
    )
    for markup in expected_markup:
        if content.count(markup) != 1:
            raise ValueError(f"published page must contain exactly once: {markup}")
    for unexpected in ('class="warning" role="status"', "<footer>", "](", ".md", "DRAFT"):
        if unexpected in content:
            raise ValueError(f"published page must not contain: {unexpected}")
    unescaped = html.unescape(text)
    for phrase in COMMUNITY_DISCLOSURES:
        if phrase.startswith("|"):
            continue  # 표 항목은 expected_markup의 td로 검증한다.
        if phrase not in unescaped:
            raise ValueError(f"published page lost community disclosure: {phrase}")

    path, digest = operating.add_file(ROUTE, content)
    document = operating.registration("privacy_policy", ROUTE, path, digest)
    document["announcedAt"] = ANNOUNCED
    document["effectiveAt"] = EFFECTIVE
    document["aliases"] = [ALIAS]
    operating.update_manifest([document])
    # 공고일과 시행일이 같아 무버전 주소를 바로 이 판으로 옮긴다(BK-962와 같은 방식).
    manifest = json.loads(operating.MANIFEST.read_text(encoding="utf-8"))
    for item in manifest["documents"]:
        if item["version"] != VERSION and ALIAS in item["aliases"]:
            item["aliases"] = [alias for alias in item["aliases"] if alias != ALIAS]
    operating.MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / ALIAS.lstrip("/") / "index.html").write_text(content, encoding="utf-8")
    print(ROUTE)
    print(source_digest, "source")
    print(digest, "page")


if __name__ == "__main__":
    main()
