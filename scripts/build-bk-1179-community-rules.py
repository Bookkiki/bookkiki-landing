#!/usr/bin/env python3
"""Issue the 2026-10-16 community rules page for BK-1179.

서버 저장소의 `docs/policies/legal-copy/community-rules.md` 원문으로 게시판 이용 규칙 첫 판을 발행한다.
공고일과 시행일은 모두 2026-10-16이므로 무버전 주소 /ko-KR/policies/community-rules도 이 판으로 만든다.
앱이 동의 기록에 남기는 서버 version `community-rules-v1`은 이 게시 version에 대응한다.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import re
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-10-16"
ANNOUNCED = "2026-10-16"
EFFECTIVE = "2026-10-16"
ALIAS = "/ko-KR/policies/community-rules"
ROUTE = f"/ko-KR/policies/community-rules/{VERSION}"
TITLE = "북끼끼 게시판 이용 규칙"

# 공개 문서에 남으면 안 되는 미완성 표기(BK-953과 같다).
BRACKET_MARKER = re.compile(r"\[[^\]\n]{0,80}(필요|확정|검증|확인|TODO|TBD)[^\]\n]{0,80}\]")
FORBIDDEN_PHRASES = ("정보 확인 중", "미확정", "확정 필요", "검증 필요", "게시해야", "확인해 기재")


def load(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def published_markdown(source: str) -> str:
    """원문 머리말의 문서 code·version은 내부 메타데이터라 빼고, 공고일·시행일은 남긴다."""
    if not source.startswith(f"# {TITLE}\n"):
        raise ValueError("community rules title changed")
    for line in (
        "- 문서 code: `community_rules`",
        "- version: `community-rules-v1` (게시 version `2026-10-16`)",
        "- 공고일: `2026년 10월 16일`",
        "- 시행일: `2026년 10월 16일`",
    ):
        if line not in source:
            raise ValueError(f"unexpected header: {line}")
    body = source.split("\n", 1)[1]
    body = body.replace("- 문서 code: `community_rules`\n", "")
    body = body.replace("- version: `community-rules-v1` (게시 version `2026-10-16`)\n", "")
    # 원문의 상대 링크를 현재 시행 중인 공개 주소로 바꾼다.
    body = body.replace("](terms-of-use.md)", "](https://www.bookkiki.com/ko-KR/policies/terms-of-use)")
    if ".md)" in body:
        raise ValueError("relative Markdown link remains")
    marker = BRACKET_MARKER.search(body)
    if marker:
        raise ValueError(f"unfinished marker remains: {marker.group(0)}")
    for phrase in FORBIDDEN_PHRASES:
        if phrase in body:
            raise ValueError(f"unfinished phrase remains: {phrase}")
    return body


def page(body_html: str) -> str:
    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="canonical" href="https://www.bookkiki.com{ROUTE}">
  <title>게시판 이용 규칙 | Bookkiki</title>
  <style>
    :root {{ color-scheme: light; font-family: system-ui, -apple-system, sans-serif; color: #353744; background: #f8f9fc; }}
    body {{ margin: 0; }} header, main, footer {{ max-width: 900px; margin: auto; padding: 24px; }}
    header a {{ color: #353744; text-decoration: none; font-weight: 700; }}
    main {{ background: white; border: 1px solid #d9dbe2; border-radius: 16px; margin-top: 16px; margin-bottom: 24px; }}
    h1 {{ line-height: 1.3; }} h2 {{ margin-top: 32px; }} p, li {{ line-height: 1.8; }}
    .table-scroll {{ overflow-x: auto; }} table {{ border-collapse: collapse; min-width: 800px; width: 100%; }}
    th, td {{ border: 1px solid #d9dbe2; padding: 12px; text-align: left; vertical-align: top; line-height: 1.6; }}
    th {{ background: #f2f3f7; }} code {{ overflow-wrap: anywhere; }}
    footer {{ color: #626676; font-size: 14px; }}
  </style>
</head>
<body>
  <header><a href="/">Bookkiki</a></header>
  <main>
    <h1>{html.escape(TITLE)}</h1>
    {body_html}
  </main>
</body>
</html>
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="bookkiki-server docs/policies/legal-copy/community-rules.md")
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")

    preview = load("build-bk-870-preview.py", "bk1179_preview")
    operating = load("build-bk-870-operating.py", "bk1179_operating")
    operating.VERSION = VERSION

    content = page(preview.render_markdown(published_markdown(source)))
    path, digest = operating.add_file(ROUTE, content)
    document = operating.registration("community_rules", ROUTE, path, digest)
    document["announcedAt"] = ANNOUNCED
    document["effectiveAt"] = EFFECTIVE
    document["aliases"] = [ALIAS]
    operating.update_manifest([document])
    # 시행일이 공고일과 같아 무버전 주소를 바로 이 판으로 둔다. 이전 판이 없어 옮길 alias는 없다.
    alias_page = ROOT / ALIAS.lstrip("/") / "index.html"
    alias_page.parent.mkdir(parents=True, exist_ok=True)
    alias_page.write_text(content, encoding="utf-8")
    print(ROUTE)
    print(hashlib.sha256(source.encode("utf-8")).hexdigest(), "source")
    print(digest, "page")


if __name__ == "__main__":
    main()
