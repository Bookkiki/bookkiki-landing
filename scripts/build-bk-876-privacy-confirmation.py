#!/usr/bin/env python3
"""Issue the immutable 2026-09-18-1 privacy-policy revision for BK-876.

확인된 값으로 미확정 표기 8건을 없앤 개정본이다. 본인확인 업체 미이용, 수탁자
PortOne·Sweetbook, 운영 데이터 7일 삭제와 원본 사진·음성 24시간 삭제, 운영 backup
설정, 권리행사 접수 창구를 확정한다. 이전 version의 bytes는 건드리지 않는다.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-09-18-1"
ANNOUNCED = "2026-09-18"
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
    # BK-876 확정 8건이 실제로 반영됐는지 확인한다.
    for marker in (
        "출시 전 확정 필요: 본인확인 업체",
        "결제업체 확정 필요",
        "제작·배송업체 및 재위탁사 확정 필요",
        "본인확인 업체 확정 필요",
        "출시 전 확정 필요: 운영 backup 설정 증빙",
    ):
        if marker in source:
            raise ValueError(f"unresolved marker must be confirmed first: {marker}")
    for phrase in (
        "별도의 본인확인 업체를 이용하지 않습니다",
        "주식회사 코리아포트원(PortOne)",
        "| Sweetbook |",
        "권리행사·고객지원 접수: 앱 설정 또는",
    ):
        if phrase not in source:
            raise ValueError(f"missing confirmed value: {phrase}")
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
    document["announcedAt"] = ANNOUNCED
    document["effectiveAt"] = EFFECTIVE
    operating.update_manifest([document])
    print(route)
    print(digest)


if __name__ == "__main__":
    main()
