#!/usr/bin/env python3
"""Issue the immutable 2026-10-16 privacy-policy revision for BK-1180.

게시판(동화 공개·좋아요·댓글·신고·숨기기)을 열면서 처리 목적·항목·보유기간, 댓글 안전 검사를 위한
Anthropic 국외 처리위탁, 동화 단어 뜻·발음(Anthropic·ElevenLabs) 처리위탁, 게시판 삭제 방법과 앱 사용 분석 이벤트 43종(실물책 선물 안내 포함)을 적은 서버 원문으로 새 판을 발행한다.
공고일과 시행일은 모두 2026-10-16이므로 무버전 주소(alias)도 이 판으로 옮긴다. 발행 형식은 2026-09-27 판과 같다(경고 문구·문서 code·원본 해시 없음).
이전 version의 bytes와 manifest 항목은 건드리지 않는다.
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
VERSION = "2026-10-16"
ANNOUNCED = "2026-10-16"
EFFECTIVE = "2026-10-16"
ALIAS = "/ko-KR/policies/privacy-policy"
ROUTE = f"/ko-KR/policies/privacy-policy/{VERSION}"
ALIAS = "/ko-KR/policies/privacy-policy"
# 국외 이전 동의서 목록은 2026-09-26-2 판이 최신이다(2026-09-27 판과 같은 주소).
OVERSEAS_INDEX_VERSION = "2026-09-26-2"
COMMUNITY_RULES_URL = "https://www.bookkiki.com/ko-KR/policies/community-rules/2026-10-16"

HEADER = (
    "- 공고일: `2026년 10월 16일`",
    "- 시행일: `2026년 10월 16일`",
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
    "게시판 댓글은 공개 전에 안전 검사를 위해 Anthropic",
    "이벤트 이름 43종",
    "단어 뜻과 소리 조각을 만들기 위해 Anthropic",
    "| 게시판 게시물·댓글 |",
)
COMMUNITY_LINK = "](community-rules.md)"
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
    if "DRAFT-2026-09-14" not in source:
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
    parser.add_argument("source", type=Path, help="bookkiki-server docs/policies/legal-copy/privacy-policy.md")
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    validate_source(source)

    preview = load("build-bk-870-preview.py", "bk1180_privacy_preview")
    operating = load("build-bk-870-operating.py", "bk1180_privacy_operating")
    bk953 = load("build-bk-953-legal-docs.py", "bk1180_bk953")
    labels = load("build-bk-953-without-internal-labels.py", "bk1180_labels")
    plain = load("build-bk-953-plain-wording.py", "bk1180_plain")
    bk953.assert_finished("privacy source", source)

    operating.VERSION = VERSION
    source_digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    draft = preview.privacy_page(published_markdown(source), source_digest)
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
        "<li>공고일: <code>2026년 10월 16일</code></li>\n<li>시행일: <code>2026년 10월 16일</code></li>",
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
    for phrase in COMMUNITY_DISCLOSURES[:3]:
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
