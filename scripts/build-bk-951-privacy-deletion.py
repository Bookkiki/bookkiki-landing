#!/usr/bin/env python3
"""Issue the immutable 2026-09-26 privacy-policy revision for BK-951.

8항에 앱 탈퇴 경로, 자녀 프로필 삭제와 동의 철회 방법, 앱을 쓸 수 없을 때의 메일 요청,
탈퇴 후 보관 정보를 적는다. 6항 국외 이전 수령자에서 비활성 OpenRouter를 뺀다.
이전 version의 bytes는 건드리지 않고 현재 주소(alias)만 새 version으로 옮긴다.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-09-26"
ANNOUNCED = "2026-09-26"
EFFECTIVE = "2026-09-26"
ALIAS = "/ko-KR/policies/privacy-policy"


def load(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def section(source: str, number: int) -> str:
    start = source.index(f"\n## {number}. ")
    end = source.index(f"\n## {number + 1}. ", start)
    return source[start:end]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    if "DRAFT-2026-09-14" not in source:
        raise ValueError("expected the reviewed legal-copy source")
    if "공고일: `2026년 9월 26일`" not in source or "시행일: `2026년 9월 26일`" not in source:
        raise ValueError("announcement and effective dates must be 2026-09-26")
    rights = section(source, 8)
    for phrase in (
        "설정 > 로그아웃 · 계정 탈퇴를 누릅니다.",
        "입력란에 \"탈퇴\"를 입력한 뒤 탈퇴하기를 누릅니다.",
        "설정 > 자녀 프로필 관리",
        "`contact@bookkiki.com`으로 탈퇴·삭제·열람 등을 요청할 수 있습니다.",
        "### 탈퇴 후에도 보관하는 정보",
        "주문이 끝난 뒤 탈퇴할 수 있습니다.",
    ):
        if phrase not in rights:
            raise ValueError(f"missing account deletion statement: {phrase}")
    if "OpenRouter" in section(source, 6):
        raise ValueError("inactive OpenRouter must not be listed as an overseas recipient")
    # 앞선 개정본의 고지가 사라지면 안 된다.
    for phrase in (
        "Langfuse GmbH",
        "제28조의8 제1항 제3호",
        "주식회사 코리아포트원(PortOne)",
        "| Sweetbook |",
        "별도의 본인확인 업체를 이용하지 않습니다",
    ):
        if phrase not in source:
            raise ValueError(f"earlier disclosure must survive this revision: {phrase}")

    preview = load("build-bk-870-preview.py", "bk951_privacy_preview")
    operating = load("build-bk-870-operating.py", "bk951_privacy_operating")
    operating.VERSION = VERSION
    route = f"/ko-KR/policies/privacy-policy/{VERSION}"
    source_digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    draft = preview.privacy_page(source, source_digest)
    # 국외 이전 동의서 목록 page는 2026-09-15 경로만 있다.
    content = operating.public_html(draft, route, privacy=True).replace(
        f'href="/ko-KR/consents/overseas-transfer/{VERSION}"',
        'href="/ko-KR/consents/overseas-transfer/2026-09-15"',
    )
    path, digest = operating.add_file(route, content)
    document = operating.registration("privacy_policy", route, path, digest)
    document["announcedAt"] = ANNOUNCED
    document["effectiveAt"] = EFFECTIVE
    operating.update_manifest([document])

    # 현재 주소를 새 version으로 옮긴다. aliases만 바뀌고 이전 version의 증빙 필드는 그대로다.
    manifest = json.loads(operating.MANIFEST.read_text(encoding="utf-8"))
    for item in manifest["documents"]:
        if item["termsCode"] != "privacy_policy":
            continue
        if item["version"] == VERSION:
            item["aliases"] = [ALIAS]
        elif ALIAS in item["aliases"]:
            item["aliases"] = [alias for alias in item["aliases"] if alias != ALIAS]
    operating.MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / ALIAS.lstrip("/") / "index.html").write_text(content, encoding="utf-8")
    print(route)
    print(digest)


if __name__ == "__main__":
    main()
