#!/usr/bin/env python3
"""Publish immutable OpenAI interview notices from the latest published pages (BK-796).

Only the interview recipient, its retention disclosure, and revision navigation change.
Existing versioned HTML and manifest evidence fields are never overwritten.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-10-26"
DATE_LABEL = "2026년 10월 26일"
PREVIOUS_POLICY = "2026-10-24"
OVERSEAS_CODE = "overseas_openai_interview_consent"
COLLECTION_CODE = "optional_ai_interview_consent"
OVERSEAS_ROUTE = f"/ko-KR/consents/overseas-transfer/{OVERSEAS_CODE}/{VERSION}"
COLLECTION_ROUTE = f"/ko-KR/consents/personal-information-collection/{COLLECTION_CODE}/{VERSION}"
POLICY_ROUTE = f"/ko-KR/policies/privacy-policy/{VERSION}"
NOTICE_ROUTE = f"/ko-KR/notices/ai-interview-openai/{VERSION}"
INDEX_ROUTE = f"/ko-KR/consents/overseas-transfer/{VERSION}"
RETENTION = (
    "회사는 OpenAI에 응답을 대화 이력으로 보관하지 않도록 요청합니다. "
    "OpenAI는 부정 이용 감시를 위해 요청 기록을 최대 30일 보관할 수 있으며, "
    "정책 위반 조사나 법률상 의무가 있으면 예외가 적용될 수 있습니다. "
    "빠른 응답을 위해 요청 내용을 처리한 임시 자료는 암호화되어 최대 24시간 보관될 수 있습니다. "
    "회사는 OpenAI의 데이터 미보관 옵션을 이용하지 않습니다."
)
RECONSENT = (
    "AI 인터뷰를 이용하려면 OpenAI 전송 내용을 확인하고 개인정보 수집·이용과 국외 이전에 각각 다시 동의해 주세요. "
    "기존 Anthropic 전송 동의를 OpenAI 전송 동의로 바꾸어 사용하지 않습니다. "
    "동의하지 않으면 새 AI 인터뷰를 이용할 수 없지만 회원가입과 이미 만든 동화 열람은 이용할 수 있습니다. "
    "동의는 설정 &gt; AI 처리·알림 동의에서 언제든 철회할 수 있습니다."
)
INTERVIEW_PARAGRAPH = (
    "AI 인터뷰의 질문 생성, 대화 요약과 답변 안전 분류를 위해 이전 인터뷰 질문·답변, 요약할 문답과 "
    "안전 분류할 답변을 OpenAI OpCo, LLC(privacy@openai.com)에 암호화 전송합니다. "
    "데이터는 미국 및 OpenAI 재수탁자 처리 국가에서 처리됩니다. "
    "보호자가 OpenAI 전송에 동의한 뒤 AI 인터뷰의 각 처리 요청 때 전송하며, 자녀 프로필 정보를 따로 넣지 않습니다. "
    "다만 입력한 답변에 자녀 정보가 들어갈 수 있으므로 문답도 개인정보로 보호합니다. "
    + RETENTION
)


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"expected one occurrence: {old[:100]}")
    return text.replace(old, new, 1)


def read_route(route: str) -> str:
    return (ROOT / route.lstrip("/") / "index.html").read_text(encoding="utf-8")


def write_immutable(route: str, text: str) -> str:
    destination = ROOT / route.lstrip("/") / "index.html"
    if destination.exists() and destination.read_text(encoding="utf-8") != text:
        raise ValueError(f"immutable page already exists with different bytes: {route}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def registration(code: str, route: str, digest: str, aliases: list[str] | None = None) -> dict:
    return {
        "termsCode": code, "version": VERSION, "locale": "ko-KR",
        "announcedAt": VERSION, "effectiveAt": VERSION, "sha256": digest,
        "sourcePath": route.lstrip("/") + "/index.html", "publicPath": route,
        "aliases": aliases or [],
    }


def overseas_page() -> str:
    previous_route = "/ko-KR/consents/overseas-transfer/overseas_anthropic_interview_consent/2026-09-26-2"
    page = read_route(previous_route)
    page = replace_once(page, previous_route, OVERSEAS_ROUTE)
    page = page.replace("Anthropic AI 인터뷰", "OpenAI AI 인터뷰")
    page = replace_once(page, "<ul>\n</ul>", f"<p>공고일·시행일: {DATE_LABEL}</p>")
    page = replace_once(page, "Anthropic, PBC (privacy@anthropic.com)", "OpenAI OpCo, LLC (privacy@openai.com)")
    page = replace_once(page, "미국(주 서버), 유럽경제지역, 영국 및 Anthropic 재수탁자 소재 국가", "미국 및 OpenAI 재수탁자 처리 국가")
    page = replace_once(page, "보호자가 AI 인터뷰 시작을 확정한 뒤 각 처리 요청 시 암호화 전송", "보호자가 OpenAI 전송에 동의한 뒤 AI 인터뷰의 각 처리 요청 시 암호화 전송")
    old_retention = page[page.index("<td>회사는 별도 계약 없이 Anthropic"):page.index("</td>", page.index("<td>회사는 별도 계약 없이 Anthropic")) + 5]
    page = replace_once(page, old_retention, f"<td>{RETENTION}</td>")
    page = replace_once(page, "위 Anthropic 처리가", "위 OpenAI 처리가")
    page = replace_once(page, "Anthropic에 보내는 요청에는", "OpenAI에 보내는 요청에는")
    old_reference = '<p>Anthropic의 보관 기준은 <a href="https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data" rel="noopener noreferrer">Anthropic의 API 데이터 보유 안내</a>에서 확인할 수 있습니다.</p>'
    new_reference = '<p>보유기간은 <a href="https://developers.openai.com/api/docs/guides/your-data" rel="noopener noreferrer">OpenAI의 API 데이터 관리 안내</a>에서, 재수탁자와 처리 국가는 <a href="https://openai.com/policies/sub-processor-list/" rel="noopener noreferrer">OpenAI의 재수탁자 목록</a>에서 확인할 수 있습니다.</p>'
    page = replace_once(page, old_reference, new_reference)
    page = replace_once(page, "<h2>철회와 삭제</h2>", f'<h2>이전 동의와 변경 안내</h2>\n<p>{RECONSENT}</p>\n<p><a href="{NOTICE_ROUTE}">AI 인터뷰 처리 업체 변경 안내</a>에서 변경 전후 내용을 확인할 수 있습니다.</p>\n<h2>철회와 삭제</h2>')
    return page


def collection_page() -> str:
    previous_route = f"/ko-KR/consents/personal-information-collection/{COLLECTION_CODE}/2026-09-26-2"
    page = replace_once(read_route(previous_route), previous_route, COLLECTION_ROUTE)
    page = replace_once(page, "<h1>AI 인터뷰</h1>", f"<h1>AI 인터뷰</h1>\n<p>공고일·시행일: {DATE_LABEL}</p>")
    marker = '<p class="consent-line">'
    additional = f'<p>질문 생성, 대화 요약과 답변 안전 분류를 위해 인터뷰 문답을 OpenAI에 보냅니다. 자녀 프로필 정보를 요청에 따로 넣지는 않지만 입력한 답변에는 자녀 정보가 들어갈 수 있습니다. 받는 자와 처리 국가·보유기간은 <a href="{OVERSEAS_ROUTE}">OpenAI AI 인터뷰 국외 이전 동의서</a>에서 확인해 주세요.</p>\n<p>{RECONSENT}</p>\n'
    return replace_once(page, marker, additional + marker)


def privacy_page() -> str:
    page = read_route(f"/ko-KR/policies/privacy-policy/{PREVIOUS_POLICY}")
    page = replace_once(page, f'https://www.bookkiki.com/ko-KR/policies/privacy-policy/{PREVIOUS_POLICY}', f'https://www.bookkiki.com{POLICY_ROUTE}')
    page = page.replace("<code>2026년 10월 24일</code>", f"<code>{DATE_LABEL}</code>")
    page = replace_once(page, 'href="/ko-KR/consents/overseas-transfer/2026-10-16"', f'href="{INDEX_ROUTE}"')
    marker = "<p>AI 인터뷰와 동화·삽화 생성에는"
    page = replace_once(page, marker, f'<p>{INTERVIEW_PARAGRAPH}</p>\n<p>{RECONSENT} 자세한 내용은 <a href="{OVERSEAS_ROUTE}">OpenAI AI 인터뷰 국외 이전 동의서</a>를 확인해 주세요.</p>\n' + marker)
    old_start = '<p>이번 개정(2026년 10월 24일 공고)'
    start = page.index(old_start)
    end = page.index("</ul>", start) + len("</ul>")
    revision = f'''<p>이번 개정({DATE_LABEL} 공고)에서 바뀐 내용과 사유는 다음과 같습니다. 직전 판은 <a href="https://www.bookkiki.com/ko-KR/policies/privacy-policy/{PREVIOUS_POLICY}" rel="noopener noreferrer">2026년 10월 24일 공고 판</a>입니다.</p>
<ul>
<li>사유: AI 인터뷰의 질문 생성·대화 요약·답변 안전 분류 업체를 Anthropic에서 OpenAI로 변경합니다.</li>
<li>6항 국외 이전에 OpenAI의 수령자·국가·항목·목적·시점·보유기간과 별도 재동의 안내를 더했습니다. 인터뷰 문답의 이용 목적과 Langfuse 품질 기록 항목은 그대로입니다.</li>
<li>기존 Anthropic 동의는 OpenAI 전송 동의로 사용하지 않습니다. 보호자가 새 원문을 확인하고 동의한 뒤에만 OpenAI로 인터뷰 문답을 보냅니다.</li>
</ul>
<p><a href="{NOTICE_ROUTE}">변경 전후 내용과 이용자 선택 안내</a></p>'''
    return page[:start] + revision + page[end:]


def notice_page() -> str:
    template = read_route(f"/ko-KR/policies/privacy-policy/{PREVIOUS_POLICY}")
    head = template[:template.index("  <main>")]
    head = replace_once(head, f"https://www.bookkiki.com/ko-KR/policies/privacy-policy/{PREVIOUS_POLICY}", f"https://www.bookkiki.com{NOTICE_ROUTE}")
    head = replace_once(head, "<title>개인정보처리방침 | Bookkiki</title>", "<title>AI 인터뷰 처리 업체 변경 안내 | Bookkiki</title>")
    return head + f'''  <main>
<h1>AI 인터뷰 처리 업체 변경 안내</h1>
<p>공고일·시행일: {DATE_LABEL}</p>
<p>AI 인터뷰의 질문 생성, 대화 요약과 답변 안전 분류를 맡는 업체를 Anthropic에서 OpenAI로 변경합니다. 새 동의를 마친 뒤 인터뷰를 이용하는 보호자와 자녀에게 적용됩니다.</p>
<div class="table-scroll"><table><thead><tr><th>항목</th><th>변경 전</th><th>변경 후</th></tr></thead><tbody>
<tr><td>이전받는 자</td><td>Anthropic, PBC</td><td>OpenAI OpCo, LLC (privacy@openai.com)</td></tr>
<tr><td>처리 국가</td><td>미국(주 서버), 유럽경제지역, 영국 및 Anthropic 재수탁자 소재 국가</td><td>미국 및 OpenAI 재수탁자 처리 국가</td></tr>
<tr><td>처리 항목·목적</td><td colspan="2">이전 인터뷰 질문·답변, 요약할 문답과 안전 분류할 답변을 질문 생성·대화 요약·답변 안전 분류에 이용합니다. 자녀 프로필 정보를 요청에 따로 넣지 않습니다.</td></tr>
<tr><td>공급자 보유기간</td><td><a href="/ko-KR/consents/overseas-transfer/overseas_anthropic_interview_consent/2026-09-26-2">기존 Anthropic 동의서의 보유기간</a></td><td>{RETENTION}</td></tr>
</tbody></table></div>
<h2>이용자가 선택할 수 있는 사항</h2>
<p>{RECONSENT}</p>
<p>회사가 보관하는 인터뷰·답변의 보유기간과 Langfuse 품질 기록의 항목·목적은 이번 변경으로 달라지지 않습니다. 질문·답변 원문은 Langfuse 품질 기록에 보내지 않습니다. 이전 동의서와 이미 기록된 동의 증빙은 보존합니다.</p>
<h2>확인할 원문</h2>
<ul>
<li><a href="{COLLECTION_ROUTE}">AI 인터뷰 개인정보 수집·이용 동의서</a></li>
<li><a href="{OVERSEAS_ROUTE}">OpenAI AI 인터뷰 국외 이전 동의서</a></li>
<li><a href="{POLICY_ROUTE}">개인정보처리방침 {VERSION} 판</a></li>
<li><a href="/ko-KR/policies/privacy-policy/{PREVIOUS_POLICY}">개인정보처리방침 {PREVIOUS_POLICY} 이전판</a></li>
</ul>
<p>문의·권리행사: contact@bookkiki.com</p>
  </main>
</body>
</html>
'''


def main() -> None:
    pages = [
        (OVERSEAS_CODE, OVERSEAS_ROUTE, overseas_page()),
        (COLLECTION_CODE, COLLECTION_ROUTE, collection_page()),
        ("privacy_policy", POLICY_ROUTE, privacy_page()),
        ("ai_interview_openai_revision_notice", NOTICE_ROUTE, notice_page()),
    ]
    manifest_path = ROOT / "policies/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    alias = "/ko-KR/policies/privacy-policy"
    for document in manifest["documents"]:
        if document["termsCode"] == "privacy_policy" and document["version"] != VERSION:
            document["aliases"] = [item for item in document["aliases"] if item != alias]
    for code, route, content in pages:
        digest = write_immutable(route, content)
        document = registration(code, route, digest, [alias] if code == "privacy_policy" else [])
        existing = next((item for item in manifest["documents"] if (item["termsCode"], item["version"]) == (code, VERSION)), None)
        if existing is not None and existing != document:
            raise ValueError(f"immutable manifest entry differs: {code}")
        if existing is None:
            manifest["documents"].append(document)
        if code == "privacy_policy":
            (ROOT / alias.lstrip("/") / "index.html").write_text(content, encoding="utf-8")
        print(json.dumps(document, ensure_ascii=False))
    index = read_route("/ko-KR/consents/overseas-transfer/2026-10-16")
    index = replace_once(index, '<li><a href="/ko-KR/consents/overseas-transfer/overseas_anthropic_interview_consent/2026-09-26-2">Anthropic AI 인터뷰</a></li>', f'<li><a href="{OVERSEAS_ROUTE}">OpenAI AI 인터뷰</a></li>')
    index = replace_once(index, "</ul></body>", f'</ul><p><a href="{NOTICE_ROUTE}">AI 인터뷰 처리 업체 변경 안내</a></p></body>')
    write_immutable(INDEX_ROUTE, index)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "policies/SHA256SUMS").write_text("".join(f'{item["sha256"]}  {item["sourcePath"]}\n' for item in manifest["documents"]), encoding="utf-8")


if __name__ == "__main__":
    main()
