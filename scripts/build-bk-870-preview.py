#!/usr/bin/env python3
"""Build review-only BK-870 pages from the Server legal-copy draft.

These pages are deliberately outside the operating /consents routes and manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREVIEW_ROOT = ROOT / "docs" / "BK-870" / "preview-pages"
VERSION = "DRAFT-2026-09-14"
DOCUMENTS = (
    ("OpenAI 사진 캐릭터 생성", "overseas_openai_photo_character_consent"),
    ("Anthropic AI 인터뷰", "overseas_anthropic_interview_consent"),
    ("ElevenLabs 음성 답변 변환", "overseas_elevenlabs_stt_consent"),
    ("OpenAI 동화·삽화 생성", "overseas_openai_story_generation_consent"),
    ("OpenRouter 생성 결과 검수", "overseas_openrouter_story_review_consent"),
    ("ElevenLabs 질문·동화 음성 낭독", "overseas_elevenlabs_tts_consent"),
    ("Apple·Google Push 알림", "overseas_push_notification_consent"),
)


def inline(value: str) -> str:
    """Render the small inline Markdown subset used by this legal copy."""
    chunks: list[str] = []
    pattern = re.compile(
        r"\[([^\]]+)\]\((https?://[^)]+|overseas-transfer-consent\.md)\)|`([^`]+)`"
    )
    cursor = 0
    for match in pattern.finditer(value):
        chunks.append(html.escape(value[cursor : match.start()]))
        if match.group(1) is not None:
            label, url = match.group(1), match.group(2)
            if url == "overseas-transfer-consent.md":
                url = "/docs/BK-870/preview-pages/"
            chunks.append(
                f'<a href="{html.escape(url, quote=True)}" rel="noopener noreferrer">'
                f"{html.escape(label)}</a>"
            )
        else:
            chunks.append(f"<code>{html.escape(match.group(3))}</code>")
        cursor = match.end()
    chunks.append(html.escape(value[cursor:]))
    return "".join(chunks)


def render_markdown(source: str) -> str:
    lines = source.strip().splitlines()
    result: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("# "):
            result.append(f"<h2>{inline(line[2:])}</h2>")
            index += 1
            continue
        if line.startswith("## "):
            result.append(f"<h2>{inline(line[3:])}</h2>")
            index += 1
            continue
        if line.startswith("### "):
            result.append(f"<h3>{inline(line[4:])}</h3>")
            index += 1
            continue
        if line.startswith("| ") and index + 1 < len(lines) and re.fullmatch(
            r"[| :\-]+", lines[index + 1].strip()
        ):
            headers = [cell.strip() for cell in line.strip("|").split("|")]
            result.append('<div class="table-scroll"><table><thead><tr>')
            result.extend(f"<th scope=\"col\">{inline(cell)}</th>" for cell in headers)
            result.append("</tr></thead><tbody>")
            index += 2
            while index < len(lines) and lines[index].strip().startswith("| "):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if len(cells) != len(headers):
                    raise ValueError(f"table column mismatch: {lines[index]}")
                result.append("<tr>")
                result.extend(f"<td>{inline(cell)}</td>" for cell in cells)
                result.append("</tr>")
                index += 1
            result.append("</tbody></table></div>")
            continue
        if line.startswith("- [ ] "):
            result.append(
                '<p class="consent-line"><input type="checkbox" disabled '
                'aria-label="초안에서는 동의할 수 없습니다"> '
                f"{inline(line[6:])}</p>"
            )
            index += 1
            continue
        if line.startswith("- "):
            result.append("<ul>")
            while index < len(lines) and lines[index].strip().startswith("- "):
                result.append(f"<li>{inline(lines[index].strip()[2:])}</li>")
                index += 1
            result.append("</ul>")
            continue
        if re.match(r"\d+\. ", line):
            result.append("<ol>")
            while index < len(lines) and re.match(r"\d+\. ", lines[index].strip()):
                item = re.sub(r"^\d+\. ", "", lines[index].strip())
                result.append(f"<li>{inline(item)}</li>")
                index += 1
            result.append("</ol>")
            continue
        paragraph = [line]
        index += 1
        while index < len(lines) and lines[index].strip() and not lines[index].strip().startswith(
            ("# ", "## ", "### ", "| ", "- ")
        ):
            paragraph.append(lines[index].strip())
            index += 1
        result.append(f"<p>{inline(' '.join(paragraph))}</p>")
    return "\n".join(result)


def sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^## (.+)$", text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        title = match.group(1).strip()
        if title in result:
            raise ValueError(f"duplicate heading: {title}")
        result[title] = text[match.end() : end].strip()
    return result


def page(title: str, code: str, content: str, common: str, digest: str) -> str:
    rendered = render_markdown(content + "\n\n## 철회와 삭제\n\n" + common)
    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <title>{html.escape(title)} · BK-870 초안 | Bookkiki</title>
  <style>
    :root {{ color-scheme: light; font-family: system-ui, -apple-system, sans-serif; color: #353744; background: #f8f9fc; }}
    body {{ margin: 0; }}
    header, main, footer {{ max-width: 900px; margin: auto; padding: 24px; }}
    header a {{ color: #353744; text-decoration: none; font-weight: 700; }}
    main {{ background: white; border: 1px solid #d9dbe2; border-radius: 16px; margin-top: 16px; margin-bottom: 24px; }}
    h1 {{ line-height: 1.3; }} h2 {{ margin-top: 32px; }} p, li {{ line-height: 1.8; }}
    .warning {{ border-left: 5px solid #b94321; background: #fff2ec; padding: 16px; line-height: 1.7; }}
    .table-scroll {{ overflow-x: auto; }} table {{ border-collapse: collapse; min-width: 800px; width: 100%; }}
    th, td {{ border: 1px solid #d9dbe2; padding: 12px; text-align: left; vertical-align: top; line-height: 1.6; }}
    th {{ background: #f2f3f7; }} .consent-line {{ padding: 14px; background: #f2f3f7; }}
    code {{ overflow-wrap: anywhere; }} footer {{ color: #626676; font-size: 14px; }}
  </style>
</head>
<body>
  <header><a href="/">Bookkiki</a></header>
  <main>
    <p class="warning" role="status"><strong>BK-870 검토용 초안입니다.</strong> 업체 조건과 공고·시행일이 확정되지 않아 운영 동의 원문이 아니며, 이 화면에서 동의할 수 없습니다. 기존 2026-09-03 원문과 운영 앱 동의 URL은 변경되지 않았습니다.</p>
    <h1>{html.escape(title)}</h1>
    <p>문서 code: <code>{html.escape(code)}</code> · 버전: <code>{VERSION}</code></p>
    <p>각 기능의 국외 이전은 별도로 동의받아야 합니다. 회사 저장소의 삭제기한과 공급자 보유기간은 다릅니다.</p>
    {rendered}
  </main>
  <footer>원본 Markdown SHA-256: <code>{digest}</code></footer>
</body>
</html>
'''


def privacy_page(source: str, digest: str) -> str:
    if "DRAFT-2026-09-14" not in source:
        raise ValueError("privacy policy is not the reviewed draft")
    if not source.startswith("# Bookkiki 개인정보처리방침\n"):
        raise ValueError("privacy policy title changed")
    body = render_markdown(source.split("\n", 1)[1])
    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <title>개인정보처리방침 · BK-870 초안 | Bookkiki</title>
  <style>
    :root {{ color-scheme: light; font-family: system-ui, -apple-system, sans-serif; color: #353744; background: #f8f9fc; }}
    body {{ margin: 0; }} header, main, footer {{ max-width: 900px; margin: auto; padding: 24px; }}
    header a {{ color: #353744; text-decoration: none; font-weight: 700; }}
    main {{ background: white; border: 1px solid #d9dbe2; border-radius: 16px; margin-top: 16px; margin-bottom: 24px; }}
    h1 {{ line-height: 1.3; }} h2 {{ margin-top: 32px; }} p, li {{ line-height: 1.8; }}
    .warning {{ border-left: 5px solid #b94321; background: #fff2ec; padding: 16px; line-height: 1.7; }}
    .table-scroll {{ overflow-x: auto; }} table {{ border-collapse: collapse; min-width: 800px; width: 100%; }}
    th, td {{ border: 1px solid #d9dbe2; padding: 12px; text-align: left; vertical-align: top; line-height: 1.6; }}
    th {{ background: #f2f3f7; }} code {{ overflow-wrap: anywhere; }}
    footer {{ color: #626676; font-size: 14px; }}
  </style>
</head>
<body>
  <header><a href="/">Bookkiki</a></header>
  <main>
    <p class="warning" role="status"><strong>BK-870 검토용 초안입니다.</strong> 운영 개인정보처리방침이 아니며 기존 공개 URL과 앱 설정은 변경되지 않았습니다.</p>
    <h1>Bookkiki 개인정보처리방침</h1>
    {body}
  </main>
  <footer>원본 Markdown SHA-256: <code>{digest}</code></footer>
</body>
</html>
'''


def index_page() -> str:
    links = [
        '<li><a href="privacy_policy/' + VERSION + '/">개인정보처리방침 초안</a></li>'
    ]
    links.extend(
        f'<li><a href="{code}/{VERSION}/">{html.escape(title)}</a></li>'
        for title, code in DOCUMENTS
    )
    return '''<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>BK-870 법률 문안 초안 미리보기 | Bookkiki</title>
<style>body{font-family:system-ui,-apple-system,sans-serif;max-width:760px;margin:40px auto;padding:24px;color:#353744;line-height:1.8}li{margin:12px 0}.warning{padding:16px;background:#fff2ec;border-left:5px solid #b94321}</style>
</head><body><h1>BK-870 법률 문안 초안</h1>
<p class="warning">운영 동의에 사용하지 않는 검토용 페이지입니다. 아래 문서는 현재 앱에 표시되지 않습니다.</p>
<ul>''' + "\n".join(links) + "</ul></body></html>\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Server overseas-transfer-consent.md")
    parser.add_argument("--privacy-source", type=Path, help="Server privacy-policy.md")
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    parts = sections(source)
    expected_titles = {title for title, _ in DOCUMENTS} | {"철회와 삭제", "게시 차단 조건"}
    if set(parts) != expected_titles:
        raise ValueError(f"source headings changed: {set(parts) ^ expected_titles}")
    if "DRAFT-2026-09-14" not in source:
        raise ValueError("source is not the reviewed BK-870 draft")
    for title, code in DOCUMENTS:
        content = parts[title]
        if content.count(f"문서 code: `{code}`") != 1:
            raise ValueError(f"document code mismatch: {title}")
        destination = PREVIEW_ROOT / code / VERSION / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            page(title, code, content, parts["철회와 삭제"], digest), encoding="utf-8"
        )
        print(destination.relative_to(ROOT))
    if args.privacy_source:
        privacy_source = args.privacy_source.read_text(encoding="utf-8")
        privacy_digest = hashlib.sha256(privacy_source.encode("utf-8")).hexdigest()
        destination = PREVIEW_ROOT / "privacy_policy" / VERSION / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(privacy_page(privacy_source, privacy_digest), encoding="utf-8")
        print(destination.relative_to(ROOT))
    (PREVIEW_ROOT / "index.html").write_text(index_page(), encoding="utf-8")
    print((PREVIEW_ROOT / "index.html").relative_to(ROOT))


if __name__ == "__main__":
    main()
