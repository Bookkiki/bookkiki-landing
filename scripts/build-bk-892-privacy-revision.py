#!/usr/bin/env python3
"""Issue the immutable 2026-09-18 privacy-policy revision for BK-892.

2026-09-17-1 원문은 로그인 제공자를 "소셜 로그인 제공자"로만 적고, 앱 사용 분석 동의의
시작점을 설정 화면으로만 안내했다. 이 개정본은 운영 Server가 실제로 켠 Google·Kakao·Naver·
Apple 네 제공자와 저장하는 OAuth 신원 정보(제공자, 제공자 회원 식별자, 제공된 이메일),
인증 Token 원문을 저장하지 않는 사실, 그리고 가입 화면의 앱 사용 분석 동의(선택)를 함께
고지한다. 이전 version의 bytes는 건드리지 않는다. 개인정보처리방침은 약관이 아니므로
공고일과 시행일을 같은 날로 둔다.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-09-18"
EFFECTIVE = "2026-09-18"


def load(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    # 원문이 실제로 소셜 로그인 4종을 고지하는 개정본인지 확인한다.
    if "DRAFT-2026-09-14" not in source:
        raise ValueError("expected the reviewed legal-copy source")
    if "로그인 제공자(Google·Kakao·Naver·Apple)" not in source:
        raise ValueError("the four social login providers must be named in the member row")
    if "인증 Token 원문을 검증 후 저장하지 않고" not in source:
        raise ValueError("the token non-retention statement must be in the copy")
    if "가입 화면의 앱 사용 분석 동의(선택)" not in source:
        raise ValueError("the signup-screen analytics consent start point must be in the copy")
    # 2026-09-17(Langfuse)과 2026-09-17-1(Google Analytics) 고지가 사라지면 안 된다.
    if "Langfuse GmbH" not in source or "제28조의8 제1항 제3호" not in source:
        raise ValueError("the Langfuse and Google Analytics disclosures must survive this revision")

    preview = load("build-bk-870-preview.py", "bk892_privacy_preview")
    operating = load("build-bk-870-operating.py", "bk892_privacy_operating")
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
    document["announcedAt"] = VERSION
    document["effectiveAt"] = EFFECTIVE
    operating.update_manifest([document])
    print(route)
    print(digest)


if __name__ == "__main__":
    main()
