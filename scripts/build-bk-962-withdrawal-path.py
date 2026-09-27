#!/usr/bin/env python3
"""Issue the immutable 2026-09-27 privacy-policy revision for BK-962.

앱 보호자 공간 개편으로 설정의 "로그아웃 · 계정 탈퇴"와 "자녀 프로필 관리" 항목이 없어졌다.
8항의 앱 내 탈퇴 경로와 자녀 프로필 삭제 경로만 새 화면에 맞추고 공고일·시행일을 바꾼다.
나머지 문장은 2026-09-26-3 판과 같아야 한다. 이전 version의 bytes는 건드리지 않고
현재 주소(alias)만 새 version으로 옮긴다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = "2026-09-26-3"
VERSION = "2026-09-27"
ANNOUNCED = "2026-09-27"
EFFECTIVE = "2026-09-27"
ALIAS = "/ko-KR/policies/privacy-policy"
MANIFEST = ROOT / "policies" / "manifest.json"
SUMS = ROOT / "policies" / "SHA256SUMS"

# (이전 판 HTML 문장, 새 판 HTML 문장, 원문(markdown)에 있어야 할 새 문장)
CHANGES = (
    (
        "<li>공고일: <code>2026년 9월 26일</code></li>\n<li>시행일: <code>2026년 9월 26일</code></li>",
        "<li>공고일: <code>2026년 9월 27일</code></li>\n<li>시행일: <code>2026년 9월 27일</code></li>",
        "- 공고일: `2026년 9월 27일`\n- 시행일: `2026년 9월 27일`",
    ),
    (
        "<li>설정 &gt; 로그아웃 · 계정 탈퇴를 누릅니다.</li>\n"
        "<li>계정 탈퇴를 누릅니다.</li>\n"
        "<li>삭제되는 항목을 확인하고 입력란에 &quot;탈퇴&quot;를 입력한 뒤 탈퇴하기를 누릅니다.</li>",
        "<li>아이 홈에서 설정을 눌러 보호자 공간을 엽니다.</li>\n"
        "<li>맨 아래 계정 탈퇴를 누릅니다.</li>\n"
        "<li>삭제되는 항목을 확인하고 다음을 누른 뒤, 입력란에 &quot;탈퇴&quot;를 입력하고 탈퇴하기를 누릅니다.</li>",
        "1. 아이 홈에서 설정을 눌러 보호자 공간을 엽니다.\n"
        "2. 맨 아래 계정 탈퇴를 누릅니다.\n"
        '3. 삭제되는 항목을 확인하고 다음을 누른 뒤, 입력란에 "탈퇴"를 입력하고 탈퇴하기를 누릅니다.',
    ),
    (
        "자녀 한 명의 정보만 지우려면 설정 &gt; 자녀 프로필 관리에서 자녀를 고르고",
        "자녀 한 명의 정보만 지우려면 설정의 아이 목록에서 자녀를 고르고",
        "자녀 한 명의 정보만 지우려면 설정의 아이 목록에서 자녀를 고르고",
    ),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="server docs/policies/legal-copy/privacy-policy.md")
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    for _, _, phrase in CHANGES:
        if phrase not in source:
            raise ValueError(f"legal-copy source must contain: {phrase}")
    for removed in ("설정 > 로그아웃 · 계정 탈퇴", "설정 > 자녀 프로필 관리"):
        if removed in source:
            raise ValueError(f"legal-copy source still has the removed app path: {removed}")

    previous_path = ROOT / "ko-KR/policies/privacy-policy" / PREVIOUS / "index.html"
    content = previous_path.read_text(encoding="utf-8")
    route_before = f"/ko-KR/policies/privacy-policy/{PREVIOUS}"
    route = f"/ko-KR/policies/privacy-policy/{VERSION}"
    if content.count(route_before) != 1:
        raise ValueError("previous page must mention its own route exactly once (canonical)")
    content = content.replace(route_before, route)
    for before, after, _ in CHANGES:
        if content.count(before) != 1:
            raise ValueError(f"previous page must contain exactly once: {before}")
        content = content.replace(before, after)

    page = ROOT / route.lstrip("/") / "index.html"
    page.parent.mkdir(parents=True, exist_ok=False)
    page.write_text(content, encoding="utf-8")
    digest = hashlib.sha256(page.read_bytes()).hexdigest()
    relative = page.relative_to(ROOT).as_posix()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for item in manifest["documents"]:
        if item["termsCode"] == "privacy_policy" and ALIAS in item["aliases"]:
            item["aliases"] = [alias for alias in item["aliases"] if alias != ALIAS]
    manifest["documents"].append(
        {
            "termsCode": "privacy_policy",
            "version": VERSION,
            "locale": "ko-KR",
            "announcedAt": ANNOUNCED,
            "effectiveAt": EFFECTIVE,
            "sha256": digest,
            "sourcePath": relative,
            "publicPath": route,
            "aliases": [ALIAS],
        }
    )
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with SUMS.open("a", encoding="utf-8") as sums:
        sums.write(f"{digest}  {relative}\n")
    (ROOT / ALIAS.lstrip("/") / "index.html").write_text(content, encoding="utf-8")
    print(route)
    print(digest)


if __name__ == "__main__":
    main()
