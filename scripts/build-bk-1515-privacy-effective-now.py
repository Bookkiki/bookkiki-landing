#!/usr/bin/env python3
"""Re-issue the 2026-11-02 privacy policy as 2026-11-02-1 with the effective date moved to the announcement date (BK-1515).

대표 결정(2026-11-02): 새 앱 버전을 바로 출시하므로 공개 방침의 시행일과 실제 수집 시작이 어긋나지 않게 시행일을
공고일로 앞당긴다. 내용은 2026-11-02 판과 같고, 머리말 날짜·canonical·14항 버전 기록과 변경 안내 링크만 바꾼다.
기존 2026-11-02 판(11-09 시행 예정)과 그 변경 안내의 bytes·manifest 항목은 그대로 둔다.

공고일과 시행일이 같으므로 무버전 주소를 이 판으로 옮긴다(2026-10-28 판의 aliases를 비운다).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_VERSION = "2026-11-02"
VERSION = "2026-11-02-1"
DATE = "2026-11-02"
ALIAS = "/ko-KR/policies/privacy-policy"
POLICY_DIR = ROOT / "ko-KR" / "policies" / "privacy-policy"
NOTICE_DIR = ROOT / "ko-KR" / "notices" / "privacy-policy-guest-browsing"
POLICY_ROUTE = f"/ko-KR/policies/privacy-policy/{VERSION}"
BASE_POLICY_ROUTE = f"/ko-KR/policies/privacy-policy/{BASE_VERSION}"
NOTICE_ROUTE = f"/ko-KR/notices/privacy-policy-guest-browsing/{VERSION}"
BASE_NOTICE_ROUTE = f"/ko-KR/notices/privacy-policy-guest-browsing/{BASE_VERSION}"
NOTICE_CODE = "privacy_policy_guest_browsing_notice"

POLICY_REPLACEMENTS = (
    (f'href="https://www.bookkiki.com{BASE_POLICY_ROUTE}">', f'href="https://www.bookkiki.com{POLICY_ROUTE}">'),
    ("<li>시행일: <code>2026년 11월 9일</code></li>", "<li>시행일: <code>2026년 11월 2일</code></li>"),
    (
        "<p>이번 개정(2026년 11월 2일 공고, 2026년 11월 9일 시행)은",
        "<p>이번 개정(2026년 11월 2일 공고·시행)은",
    ),
    (
        '직전 판은 <a href="/ko-KR/policies/privacy-policy/2026-10-28">2026-10-28 판</a>입니다.</p>',
        '직전에 시행한 판은 <a href="/ko-KR/policies/privacy-policy/2026-10-28">2026-10-28 판</a>입니다. '
        f'같은 내용을 2026년 11월 9일 시행으로 먼저 공고한 <a href="{BASE_POLICY_ROUTE}">2026-11-02 판</a>의 '
        "시행일을 공고일(2026년 11월 2일)로 앞당겨 이 판으로 다시 냈습니다.</p>",
    ),
    (
        "<ul><li>가입 전 둘러보기: 처리 목적",
        "<ul><li>시행일을 공고일로 앞당김: 2026-11-02 판(2026년 11월 9일 시행 예정)과 내용이 같고 시행일만 2026년 11월 2일로 바꿨습니다.</li>"
        "<li>가입 전 둘러보기: 처리 목적",
    ),
    (f'<p><a href="{BASE_NOTICE_ROUTE}">', f'<p><a href="{NOTICE_ROUTE}">'),
)

NOTICE_REPLACEMENTS = (
    (f'href="https://www.bookkiki.com{BASE_NOTICE_ROUTE}">', f'href="https://www.bookkiki.com{NOTICE_ROUTE}">'),
    (
        "<p>공고일: 2026년 11월 2일 · 시행일: 2026년 11월 9일</p>",
        "<p>공고일·시행일: 2026년 11월 2일 (처음 안내한 시행일 2026년 11월 9일을 앞당겼습니다)</p>",
    ),
    (
        f'<ul><li><a href="{BASE_POLICY_ROUTE}">개정 개인정보처리방침(2026-11-02 판, 2026년 11월 9일 시행)</a></li>'
        '<li><a href="/ko-KR/policies/privacy-policy/2026-10-28">현재 개인정보처리방침(2026-10-28 판)</a></li></ul>',
        f'<ul><li><a href="{POLICY_ROUTE}">현재 개인정보처리방침(2026-11-02-1 판, 2026년 11월 2일 시행)</a></li>'
        '<li><a href="/ko-KR/policies/privacy-policy/2026-10-28">이전 개인정보처리방침(2026-10-28 판)</a></li></ul>',
    ),
)


def apply(source: Path, replacements) -> bytes:
    text = source.read_text(encoding="utf-8")
    for old, new in replacements:
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"expected exactly one match in {source}, found {count}: {old[:80]!r}")
        text = text.replace(old, new)
    if "11월 9일 시행)" in text and "시행 예정" not in text:
        raise SystemExit("stale effective date remains")
    return text.encode("utf-8")


def entry(code: str, path: Path, route: str, aliases: list[str]) -> dict:
    return {
        "termsCode": code,
        "version": VERSION,
        "locale": "ko-KR",
        "announcedAt": DATE,
        "effectiveAt": DATE,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "sourcePath": path.relative_to(ROOT).as_posix(),
        "publicPath": route,
        "aliases": aliases,
    }


def main() -> int:
    policy = POLICY_DIR / VERSION / "index.html"
    notice = NOTICE_DIR / VERSION / "index.html"
    policy.parent.mkdir(parents=True, exist_ok=True)
    notice.parent.mkdir(parents=True, exist_ok=True)
    policy.write_bytes(apply(POLICY_DIR / BASE_VERSION / "index.html", POLICY_REPLACEMENTS))
    notice.write_bytes(apply(NOTICE_DIR / BASE_VERSION / "index.html", NOTICE_REPLACEMENTS))
    (POLICY_DIR / "index.html").write_bytes(policy.read_bytes())

    manifest_path = ROOT / "policies" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for document in manifest["documents"]:
        if ALIAS in document["aliases"]:
            document["aliases"] = [a for a in document["aliases"] if a != ALIAS]
    new_entries = [
        entry("privacy_policy", policy, POLICY_ROUTE, [ALIAS]),
        entry(NOTICE_CODE, notice, NOTICE_ROUTE, []),
    ]
    existing = {(d["termsCode"], d["version"], d["locale"]) for d in manifest["documents"]}
    for new in new_entries:
        if (new["termsCode"], new["version"], new["locale"]) in existing:
            raise SystemExit(f"version already issued: {new['termsCode']} {VERSION}")
        manifest["documents"].append(new)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sums_path = ROOT / "policies" / "SHA256SUMS"
    sums = sums_path.read_text(encoding="utf-8")
    for new in new_entries:
        sums += f"{new['sha256']}  {new['sourcePath']}\n"
    sums_path.write_text(sums, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
