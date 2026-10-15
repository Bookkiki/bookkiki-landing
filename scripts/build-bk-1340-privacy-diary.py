#!/usr/bin/env python3
"""Issue the 2026-10-16-1 privacy-policy revision with the diary photo disclosures (BK-1340).

2026-10-16 판(BK-1180, scripts/build-bk-1180-privacy-policy.py) 위에 아이 일기·글로 동화 만들기의 일기 사진 처리
(처리 목적, 처리 항목, 보유기간, 처리 위탁, 국외 이전, 회원 탈퇴, 변경 고지)와 일기 사진 열람 기록의 보관기간을 더한
서버 원문으로 새 판을 발행한다. 2026-10-16 판의 bytes와 manifest 항목은 건드리지 않는다.

- 직전 판 원문(2026-10-16)을 같은 절차로 렌더링하면 공개된 2026-10-16 판과 bytes가 같아야 한다. 다르면 렌더링이나
  기준 원문이 달라진 것이므로 발행을 멈춘다.
- 6항이 가리키는 국외 이전 동의서 목록은 OpenAI 동화·삽화 생성 동의서 2026-10-16 판이 들어간 새 목록(2026-10-16)으로
  바꾼다. 나머지 동의서는 2026-09-26-2 판이 현재 판이다.
- 공고일과 시행일이 같으므로 무버전 주소를 이 판으로 옮긴다. 날짜를 바꿔 다시 발행하려면 아래 상수와 원문 머리말을
  함께 고친다(같은 날 다시 내는 판은 -2부터, 다른 날이면 그 날짜를 version으로 쓴다).
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
VERSION = "2026-10-16-1"
ANNOUNCED = "2026-10-16"
EFFECTIVE = "2026-10-16"
HEADER = (
    "- 공고일: `2026년 10월 16일`",
    "- 시행일: `2026년 10월 16일`",
)
ROUTE = f"/ko-KR/policies/privacy-policy/{VERSION}"
ALIAS = "/ko-KR/policies/privacy-policy"
PREVIOUS_VERSION = "2026-10-16"
PREVIOUS_OVERSEAS_INDEX_VERSION = "2026-09-26-2"
COMMUNITY_RULES_URL = "https://www.bookkiki.com/ko-KR/policies/community-rules/2026-10-16"
COMMUNITY_LINK = "](community-rules.md)"
OVERSEAS_LINK = "](overseas-transfer-consent.md)"

# 6항이 가리킬 새 국외 이전 동의서 목록. 문서별 현재 판을 적는다.
OVERSEAS_INDEX_VERSION = "2026-10-16"
OVERSEAS_DOCUMENTS = (
    ("OpenAI 사진 캐릭터 생성", "overseas_openai_photo_character_consent", "2026-09-26-2"),
    ("Anthropic AI 인터뷰", "overseas_anthropic_interview_consent", "2026-09-26-2"),
    ("ElevenLabs 음성 답변 변환", "overseas_elevenlabs_stt_consent", "2026-09-26-2"),
    ("OpenAI 동화·삽화 생성", "overseas_openai_story_generation_consent", "2026-10-16"),
    ("OpenRouter 생성 결과 검수", "overseas_openrouter_story_review_consent", "2026-09-26-2"),
    ("ElevenLabs 질문·동화 음성 낭독", "overseas_elevenlabs_tts_consent", "2026-09-26-2"),
    ("Apple·Google Push 알림", "overseas_push_notification_consent", "2026-09-26-2"),
)

# 앞선 판의 고지가 사라지면 안 된다(BK-951·BK-962·BK-1180과 같다).
EARLIER_DISCLOSURES = (
    "Langfuse GmbH",
    "제28조의8 제1항 제3호",
    "주식회사 코리아포트원(PortOne)",
    "| Sweetbook |",
    "별도의 본인확인 업체를 이용하지 않습니다",
    "자녀 한 명의 정보만 지우려면 설정의 아이 목록에서 자녀를 고르고",
    "`contact@bookkiki.com`으로 탈퇴·삭제·열람 등을 요청할 수 있습니다.",
    "### 탈퇴 후에도 보관하는 정보",
    "아이 화면에서 누른 좋아요 포함",
    "게시판 댓글은 공개 전에 안전 검사를 위해 Anthropic",
    "이벤트 이름 43종",
    "단어 뜻과 소리 조각을 만들기 위해 Anthropic",
    "| 게시판 게시물·댓글 |",
)
# 이번 판에서 새로 들어간 일기 고지. 동의서 2026-10-16 판(BK-1336)과 같은 사실이어야 한다.
DIARY_DISCLOSURES = (
    "아이가 쓴 일기·글 사진의 글씨 읽기와 일기 동화 제공",
    "| 일기 | 아이가 쓴 일기·글을 찍은 사진(촬영 위치·기기 정보를 지운 사진)",
    "인터뷰 요약 또는 보호자가 고친 일기 글",
    "| 자녀 원본 사진(사진 캐릭터) |",
    "| 일기 사진·사진에서 읽은 글 | 회사 서버(AWS 서울 리전)에 저장한 날부터 10일이 지나면 자동 삭제",
    "일기 사진과 사진에서 읽은 글을 열람한 기록은 2년 보관한 뒤 삭제",
    "서비스 운영 정보, 일기 사진(서울 리전에 보관)",
    "일기 사진 글씨 읽기에도 같은 품질 기록이 딸려 있으며",
    "사진 속 글씨를 읽기 위해 사진(촬영 위치·기기 정보를 지운 사진)을 한 장씩 OpenAI OpCo, LLC",
    "회사는 OpenAI의 데이터 미보관 옵션을 이용하지 않습니다.",
    "회사 서버에 보관 중인 일기 사진과 사진에서 읽은 글은 탈퇴할 때 바로 삭제합니다.",
    "이번 개정(2026년 10월 16일 공고)에서 바뀐 내용과 사유는 다음과 같습니다.",
)
# 근거를 확인하지 않은 약속은 넣지 않는다.
UNSUPPORTED_CLAIMS = ("학습에 사용하지", "학습에 쓰지", "학습하지 않")


def load(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


preview = load("build-bk-870-preview.py", "bk1340_preview")
operating = load("build-bk-870-operating.py", "bk1340_operating")
bk953 = load("build-bk-953-legal-docs.py", "bk1340_bk953")
labels = load("build-bk-953-without-internal-labels.py", "bk1340_labels")
plain = load("build-bk-953-plain-wording.py", "bk1340_plain")


def published_markdown(source: str) -> str:
    """렌더러는 http(s) 링크와 국외 이전 동의서 링크만 anchor로 만든다. 게시판 이용 규칙은 공개 주소로 바꾼다."""
    for link in (COMMUNITY_LINK, OVERSEAS_LINK):
        if source.count(link) != 1:
            raise ValueError(f"expected exactly one link: {link}")
    body = source.replace(COMMUNITY_LINK, f"]({COMMUNITY_RULES_URL})")
    if ".md)" in body.replace(OVERSEAS_LINK, ""):
        raise ValueError("relative Markdown link remains")
    return body


def render(source: str, version: str, overseas_index_version: str) -> str:
    """BK-1180 판과 같은 절차로 공개 페이지를 만든다(경고 문구·문서 code·원본 해시 없음)."""
    if "DRAFT-2026-09-14" not in source:
        raise ValueError("expected the reviewed legal-copy source")
    bk953.assert_finished("privacy source", source)
    operating.VERSION = version
    route = f"/ko-KR/policies/privacy-policy/{version}"
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    content = operating.public_html(preview.privacy_page(published_markdown(source), digest), route, privacy=True)
    overseas_href = f'href="/ko-KR/consents/overseas-transfer/{version}"'
    if content.count(overseas_href) != 1:
        raise ValueError("expected exactly one overseas-transfer consent link")
    content = content.replace(
        overseas_href, f'href="/ko-KR/consents/overseas-transfer/{overseas_index_version}"'
    )
    content = bk953.without_banner(content, "privacy")
    for pattern in labels.INTERNAL_LABELS:
        content = pattern.sub("", content)
    text = bk953.visible_text(content)
    remaining = labels.REMAINING_LABEL.search(text) or plain.DEVELOPER_TERMS.search(text)
    if remaining:
        raise ValueError(f"internal or developer wording remains: {remaining.group(0)}")
    bk953.assert_finished(route, text)
    return content


def overseas_index() -> str:
    links = "\n".join(
        f'<li><a href="/ko-KR/consents/overseas-transfer/{code}/{version}">{html.escape(title)}</a></li>'
        for title, code, version in OVERSEAS_DOCUMENTS
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
    parser.add_argument("source", type=Path, help="bookkiki-server docs/policies/legal-copy/privacy-policy.md (새 판)")
    parser.add_argument("previous_source", type=Path, help="2026-10-16 판을 만든 같은 파일(직전 판)")
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    previous = args.previous_source.read_text(encoding="utf-8")

    # 기준 확인: 직전 원문이 공개된 2026-10-16 판과 같은 bytes로 렌더링돼야 한다.
    published = (ROOT / f"ko-KR/policies/privacy-policy/{PREVIOUS_VERSION}/index.html").read_text(encoding="utf-8")
    if render(previous, PREVIOUS_VERSION, PREVIOUS_OVERSEAS_INDEX_VERSION) != published:
        raise ValueError("previous source does not reproduce the published 2026-10-16 page")

    for line in HEADER:
        if line not in source:
            raise ValueError(f"announcement and effective dates changed: {line}")
    for phrase in EARLIER_DISCLOSURES:
        if phrase not in source:
            raise ValueError(f"earlier disclosure must survive this revision: {phrase}")
    for phrase in DIARY_DISCLOSURES:
        if source.count(phrase) != 1:
            raise ValueError(f"expected exactly once in the source: {phrase}")
    for claim in UNSUPPORTED_CLAIMS:
        if claim in source:
            raise ValueError(f"unsupported claim in the source: {claim}")

    for _, code, version in OVERSEAS_DOCUMENTS:
        if not (ROOT / f"ko-KR/consents/overseas-transfer/{code}/{version}/index.html").is_file():
            raise ValueError(f"overseas consent page is not published: {code}/{version}")
    operating.add_file(f"/ko-KR/consents/overseas-transfer/{OVERSEAS_INDEX_VERSION}", overseas_index())

    content = render(source, VERSION, OVERSEAS_INDEX_VERSION)
    expected_markup = (
        f'<link rel="canonical" href="https://www.bookkiki.com{ROUTE}">',
        "<li>공고일: <code>2026년 10월 16일</code></li>\n<li>시행일: <code>2026년 10월 16일</code></li>",
        f'<a href="/ko-KR/consents/overseas-transfer/{OVERSEAS_INDEX_VERSION}" rel="noopener noreferrer">'
        "개인정보 국외 이전 동의서</a>",
        '<a href="https://www.bookkiki.com/ko-KR/policies/privacy-policy/2026-10-16" rel="noopener noreferrer">'
        "2026년 10월 16일 공고 판</a>",
        "<td>일기 사진·사진에서 읽은 글</td>",
        "<td>자녀 원본 사진(사진 캐릭터)</td>",
    )
    for markup in expected_markup:
        if content.count(markup) != 1:
            raise ValueError(f"published page must contain exactly once: {markup}")
    for unexpected in ('class="warning" role="status"', "<footer>", "](", ".md", "DRAFT"):
        if unexpected in content:
            raise ValueError(f"published page must not contain: {unexpected}")

    operating.VERSION = VERSION
    path, digest = operating.add_file(ROUTE, content)
    document = operating.registration("privacy_policy", ROUTE, path, digest)
    document["announcedAt"] = ANNOUNCED
    document["effectiveAt"] = EFFECTIVE
    document["aliases"] = [ALIAS]
    operating.update_manifest([document])
    # 공고일과 시행일이 같아 무버전 주소를 바로 이 판으로 옮긴다(BK-962·BK-1180과 같은 방식).
    manifest = json.loads(operating.MANIFEST.read_text(encoding="utf-8"))
    for item in manifest["documents"]:
        if item["termsCode"] == "privacy_policy" and item["version"] != VERSION and ALIAS in item["aliases"]:
            item["aliases"] = [alias for alias in item["aliases"] if alias != ALIAS]
    operating.MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / ALIAS.lstrip("/") / "index.html").write_text(content, encoding="utf-8")
    print(ROUTE)
    print(hashlib.sha256(source.encode("utf-8")).hexdigest(), "source")
    print(digest, "page")


if __name__ == "__main__":
    main()
