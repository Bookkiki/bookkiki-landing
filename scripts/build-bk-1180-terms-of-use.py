#!/usr/bin/env python3
"""Issue the immutable 2026-10-16 terms-of-use revision for BK-1180.

공개 이용약관은 서버 legal-copy Markdown이 아니라 Next.js로 렌더링한 HTML 계보(2026-09-03 → 2026-09-18)다.
BK-892와 같이 2026-09-18 원문에서 문장을 치환해 새 version을 만든다. 치환은 화면 HTML과 React payload
사본 양쪽에 적용하고, payload의 본문 길이 표시(`5:T<hex>,`)를 다시 계산한다.

- 제5조에 게시판 기능을 더하고, 제7조 뒤에 제7조의2(게시판)를 넣는다(목차 포함).
- 부칙의 시행일을 2026년 10월 16일로 바꾸고, 대표 전화번호를 빼고, 사업자등록번호를 적는다.
  사업장 주소는 약관에 적지 않는다.
- 공고일과 시행일은 모두 2026-10-16이므로 무버전 주소(alias)도 이 판으로 옮긴다. 지금 alias가 가리키는 2026-09-03 판도 함께 바로잡힌다.

2026-09-18 원문의 bytes와 manifest 항목은 건드리지 않는다.
"""

from __future__ import annotations

import html
import importlib.util
import json
import re
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_VERSION = "2026-09-18"
VERSION = "2026-10-16"
ANNOUNCED = "2026-10-16"
EFFECTIVE = "2026-10-16"
ALIAS = "/ko-KR/policies/terms-of-use"
ROUTE_PREFIX = "/ko-KR/policies/terms-of-use"
ROUTE = f"{ROUTE_PREFIX}/{VERSION}"
BASE_EFFECTIVE_TEXT = "2026년 9월 25일"
EFFECTIVE_TEXT = "2026년 10월 16일"
COMMUNITY_RULES_URL = "https://www.bookkiki.com/ko-KR/policies/community-rules/2026-10-16"

ARTICLE_7_2_ITEMS = (
    "회원은 게시판 이름을 정하고 게시판 이용 규칙에 동의한 뒤 자신이 만든 동화를 앱 안 게시판에 올리거나 "
    "다른 회원의 동화에 댓글을 쓸 수 있습니다. 게시판 이용 규칙"
    f'(<a href="{COMMUNITY_RULES_URL}">{COMMUNITY_RULES_URL}</a>)은 이 약관의 일부로 적용됩니다.',
    "회원은 회사가 게시판에 올린 동화와 댓글을 앱 안 게시판에서 다른 회원에게 보여 주는 데 필요한 범위에서 "
    "복제·전송·표시하는 것을 허락합니다. 이 허락은 회원이 동화를 내리거나 댓글을 지우면 끝나며, "
    "회사는 게시물을 앱 밖으로 배포하거나 광고·홍보에 쓰지 않습니다.",
    "회원은 아이나 다른 사람의 개인정보, 다른 사람의 권리를 침해하는 내용, 욕설·괴롭힘, 성적·폭력적·혐오 표현, "
    "광고·도배 등 게시판 이용 규칙이 금지한 내용을 올려서는 안 됩니다.",
    "회사는 신고와 안전 검사에 따라 게시판 이용 규칙에 어긋나는 게시물을 가리거나 지우고 댓글을 가릴 수 있으며, "
    "규칙을 어긴 회원의 게시판 이용을 7일, 30일 또는 기한 없이 정지할 수 있습니다. "
    "회원은 제12조에 따라 이의를 제기할 수 있습니다.",
    "게시물과 댓글의 공개·보관·삭제 기준은 게시판 이용 규칙과 개인정보처리방침을 따릅니다.",
)
ARTICLE_7_2 = (
    '    <section id="article-7-2">\n'
    "      <h2>제7조의2 (게시판)</h2>\n"
    "      <ol>\n"
    + "".join(f"        <li>{item}</li>\n" for item in ARTICLE_7_2_ITEMS)
    + "      </ol>\n"
    "    </section>\n\n"
)
SERVICE_ITEM = "보호자가 만든 동화를 앱 안에서 다른 회원과 나누고 좋아요·댓글을 주고받는 게시판"
BUSINESS_NUMBER = "사업자등록번호: 525-43-01349"

# 본문(<article>) 안의 치환. 화면 HTML과 payload의 본문 사본에 각각 정확히 한 번 있어야 한다.
ARTICLE_REPLACEMENTS = (
    (
        "<li>생성 작업의 진행 상태와 완료·실패 등 서비스 관련 알림 제공</li>\n"
        "        <li>그 밖에 회사가 서비스 화면에서 안내하는 기능</li>",
        "<li>생성 작업의 진행 상태와 완료·실패 등 서비스 관련 알림 제공</li>\n"
        f"        <li>{SERVICE_ITEM}</li>\n"
        "        <li>그 밖에 회사가 서비스 화면에서 안내하는 기능</li>",
    ),
    (
        '    <section id="article-8">',
        ARTICLE_7_2 + '    <section id="article-8">',
    ),
    (
        f"<p>이 약관은 {BASE_EFFECTIVE_TEXT}부터 시행합니다.</p>",
        f"<p>이 약관은 {EFFECTIVE_TEXT}부터 시행합니다.</p>",
    ),
    (
        '\n      <p>대표 전화번호: <a href="tel:+821084514280">010-8451-4280</a></p>',
        "",
    ),
    (
        "<p>사업자등록번호·사업장 주소: 사업자 등록 절차 완료 후 본 페이지에 반영합니다.</p>",
        f"<p>{BUSINESS_NUMBER}</p>",
    ),
)
# 목차(<nav>)는 화면에 두 번(넓은 화면·모바일), payload에는 dangerouslySetInnerHTML 문자열로 두 번 있다.
NAV_REPLACEMENTS = (
    (
        '<li><a href="#article-7">회원의 의무</a></li>\n        <li><a href="#article-8">',
        '<li><a href="#article-7">회원의 의무</a></li>\n'
        '        <li><a href="#article-7-2">게시판</a></li>\n'
        '        <li><a href="#article-8">',
    ),
)
# 머리말·제목·설명 문구의 version과 시행일. (이전 문구, 새 문구, 예상 횟수)
PAGE_REPLACEMENTS = (
    (
        f"서비스 이용약관 ({BASE_VERSION}) | BookKiki",
        f"서비스 이용약관 ({VERSION}) | BookKiki",
        2,
    ),
    (
        f"https://www.bookkiki.com{ROUTE_PREFIX}/{BASE_VERSION}",
        f"https://www.bookkiki.com{ROUTE_PREFIX}/{VERSION}",
        2,
    ),
    # meta description·머리말 문구와 그 payload 사본(부칙은 위에서 이미 바꿨다).
    (BASE_EFFECTIVE_TEXT, EFFECTIVE_TEXT, 4),
)
LEFTOVERS = (
    BASE_VERSION,
    BASE_EFFECTIVE_TEXT,
    "9월 25일",
    "8451",
    "tel:",
    "대표 전화번호",
    "사업장 주소",
    "사업자 등록 절차",
    "반영합니다",
)
NEW_VISIBLE_TEXT = (
    SERVICE_ITEM,
    "제7조의2 (게시판)",
    *(re.sub(r"<[^>]+>", "", item) for item in ARTICLE_7_2_ITEMS),
    f"이 약관은 {EFFECTIVE_TEXT}부터 시행합니다.",
    BUSINESS_NUMBER,
    "운영자: Bookkiki",
    "대표자: 황채원",
    "전자우편: contact@bookkiki.com",
    f"{EFFECTIVE_TEXT}부터 시행하는 BookKiki 서비스 이용약관입니다.",
)
ARTICLE = re.compile(r"(<article[^>]*>)(.*?)(</article>)", re.S)
LENGTH_MARKER = re.compile(r"5:T([0-9a-f]+),")
# payload 문자열 안에서 HTML 해석을 막기 위해 Next.js가 유니코드 escape로 바꾸는 문자.
HTML_UNSAFE = ("&", "<", ">", chr(0x2028), chr(0x2029))
BACKSLASH = chr(92)


def load(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def flight_escape(value: str) -> str:
    """Next.js가 React payload 문자열을 <script> 안에 넣을 때의 escape(JSON 문자열 + HTML 안전 문자)."""
    escaped = json.dumps(value, ensure_ascii=False)[1:-1]
    for char in HTML_UNSAFE:
        escaped = escaped.replace(char, BACKSLASH + f"u{ord(char):04x}")
    return escaped


def nav_escape(value: str) -> str:
    """목차는 dangerouslySetInnerHTML의 JSON 문자열이 다시 payload 문자열에 들어 있다."""
    return flight_escape(json.dumps(value, ensure_ascii=False)[1:-1])


def replace_exact(text: str, old: str, new: str, count: int, label: str) -> str:
    found = text.count(old)
    if found != count:
        raise ValueError(f"{label}: expected {count} occurrence(s), found {found}: {old[:80]}")
    return text.replace(old, new)


def article_of(page: str) -> str:
    matches = ARTICLE.findall(page)
    if len(matches) != 1:
        raise ValueError(f"expected one <article>, found {len(matches)}")
    return matches[0][1]


def check_payload_copy(page: str, article: str) -> None:
    """payload의 본문 사본이 화면 본문과 같고 길이 표시가 맞는지 확인한다."""
    markers = LENGTH_MARKER.findall(page)
    if len(markers) != 1:
        raise ValueError(f"expected one React payload length marker, found {len(markers)}")
    if int(markers[0], 16) != len(article.encode("utf-8")):
        raise ValueError("React payload length marker does not match the article")
    chunk = f'self.__next_f.push([1,"{flight_escape(article)}"])'
    if page.count(chunk) != 1:
        raise ValueError("React payload article copy differs from the visible article")


def revise(source: str) -> str:
    check_payload_copy(source, article_of(source))
    revised = source
    for old, new in ARTICLE_REPLACEMENTS:
        revised = replace_exact(revised, old, new, 1, "article html")
        revised = replace_exact(revised, flight_escape(old), flight_escape(new), 1, "article payload")
    for old, new in NAV_REPLACEMENTS:
        revised = replace_exact(revised, old, new, 2, "navigation html")
        revised = replace_exact(revised, nav_escape(old), nav_escape(new), 2, "navigation payload")
    for old, new, count in PAGE_REPLACEMENTS:
        revised = replace_exact(revised, old, new, count, "page")

    article = article_of(revised)
    marker = LENGTH_MARKER.search(revised)
    if marker is None:
        raise ValueError("missing React payload length marker")
    revised = revised.replace(marker.group(0), f"5:T{len(article.encode('utf-8')):x},", 1)
    check_payload_copy(revised, article)
    return revised


def visible_text(page: str) -> str:
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", body)))


def validate(page: str, bk953) -> None:
    for leftover in LEFTOVERS:
        if leftover in page:
            raise ValueError(f"revised page still contains: {leftover}")
    text = visible_text(page)
    bk953.assert_finished(ROUTE, text)
    for phrase in NEW_VISIBLE_TEXT:
        if text.count(phrase) != 1:
            raise ValueError(f"revised page must show exactly once: {phrase}")
    if re.search(r"01[016789]-?\d{3,4}-?\d{4}", text):
        raise ValueError("a phone number remains")
    article = article_of(page)
    if article.index('id="article-7"') > article.index('id="article-7-2"') or article.index(
        'id="article-7-2"'
    ) > article.index('id="article-8"'):
        raise ValueError("제7조의2 must sit between 제7조 and 제8조")


def main() -> None:
    operating = load("build-bk-870-operating.py", "bk1180_terms_operating")
    bk953 = load("build-bk-953-legal-docs.py", "bk1180_terms_bk953")
    operating.VERSION = VERSION

    manifest = json.loads(operating.MANIFEST.read_text(encoding="utf-8"))
    bases = [
        item for item in manifest["documents"]
        if (item["termsCode"], item["version"], item["locale"]) == ("terms_of_service", BASE_VERSION, "ko-KR")
    ]
    if len(bases) != 1:
        raise ValueError(f"expected one terms_of_service {BASE_VERSION} manifest entry")
    base_path = ROOT / bases[0]["sourcePath"]
    # newline 변환 없이 원문 bytes 그대로 읽는다.
    source = base_path.read_bytes().decode("utf-8")

    revised = revise(source)
    validate(revised, bk953)

    path, digest = operating.add_file(ROUTE, revised)
    document = operating.registration("terms_of_service", ROUTE, path, digest)
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
    (ROOT / ALIAS.lstrip("/") / "index.html").write_text(revised, encoding="utf-8")
    print(ROUTE)
    print(digest)


if __name__ == "__main__":
    main()
