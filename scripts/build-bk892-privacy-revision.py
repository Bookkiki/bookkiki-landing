#!/usr/bin/env python3
"""Publish the BK-892 privacy-policy revision with four social login providers.

BK-876 승인 정책(`DRAFT-2026-09-14`)을 기준으로 삼되, 소셜 로그인 제공자 4종과
BK-877 대기열 전송 금지 계약을 더하고 확인된 값으로 미확정 표기를 없앤 판을 발행한다.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-09-16"
ROUTE = f"/ko-KR/policies/privacy-policy/{VERSION}"
PUBLIC_ALIAS = "/ko-KR/policies/privacy-policy"

# 공개 전에 남아 있으면 안 되는 내부 검토 표기.
FORBIDDEN_MARKERS = (
    "출시 전 확정 필요",
    "구현 검증 필요",
    "계약 및 구현 검증 필요",
    "외부 법률 검토 필요",
    "log lifecycle 검증 필요",
    "결제업체 확정 필요",
    "제작·배송업체 및 재위탁사 확정 필요",
    "본인확인 업체 확정 필요",
    "메일 수신·회신 시험 필요",
)

# BK-892가 반드시 담아야 하는 내용.
REQUIRED_PHRASES = (
    "소셜 로그인 제공자(Google·Kakao·Naver·Apple)",
    "인증 Token 원문은 저장하지 않음",
    "전송 금지 표시",
    "공고일: `2026년 9월 16일`",
    "시행일: `2026년 9월 16일`",
)

# 공개 페이지 안내문. 미확정 항목이 없으므로 초안 경고를 쓰지 않는다.
PUBLIC_NOTICE = (
    '<p class="warning" role="status"><strong>이 문서는 2026년 9월 16일 시행 판입니다.</strong> '
    "이전 버전은 각 버전 경로에서 그대로 열람할 수 있습니다. 이 공개 페이지를 여는 것만으로 "
    "동의 기록이 생성되거나 AI 기능이 활성화되지 않습니다.</p>"
)


def load(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_source(source: str) -> None:
    for marker in FORBIDDEN_MARKERS:
        if marker in source:
            raise ValueError(f"unresolved review marker in source: {marker}")
    for phrase in REQUIRED_PHRASES:
        if phrase not in source:
            raise ValueError(f"missing required BK-892 content: {phrase}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the source and render without writing files",
    )
    args = parser.parse_args()

    source = args.source.read_text(encoding="utf-8")
    verify_source(source)

    preview = load("build-bk-870-preview.py", "bk892_privacy_preview")
    operating = load("build-bk-870-operating.py", "bk892_privacy_operating")
    operating.VERSION = VERSION

    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    draft = preview.privacy_page(source, digest)
    content = operating.public_html(draft, ROUTE, privacy=True)
    # BK-870 초안 경고는 미확정 항목을 전제로 한다. 이 판에는 해당 항목이 없다.
    content, replaced = _replace_notice(content)
    if replaced != 1:
        raise ValueError("public notice paragraph not found")
    # 국외 이전 동의서는 아직 2026-09-15 판이 최신이다.
    content = content.replace(
        f'href="/ko-KR/consents/overseas-transfer/{VERSION}"',
        'href="/ko-KR/consents/overseas-transfer/2026-09-15"',
    )

    if args.check:
        print(f"{ROUTE}\t{hashlib.sha256(content.encode('utf-8')).hexdigest()}")
        return

    path, content_digest = operating.add_file(ROUTE, content)
    document = operating.registration("privacy_policy", ROUTE, path, content_digest)
    document["announcedAt"] = VERSION
    document["effectiveAt"] = VERSION
    document["aliases"] = [PUBLIC_ALIAS]
    operating.update_manifest([document])
    _move_alias(content)
    print(f"{ROUTE}\t{content_digest}")


def _replace_notice(content: str) -> tuple[str, int]:
    import re

    return re.subn(r'<p class="warning" role="status">.*?</p>', PUBLIC_NOTICE, content)


def _move_alias(content: str) -> None:
    """최신 문서를 공개 alias 경로에도 쓰고 manifest의 이전 alias를 비운다."""
    import json

    alias_path = ROOT / PUBLIC_ALIAS.lstrip("/") / "index.html"
    alias_path.parent.mkdir(parents=True, exist_ok=True)
    alias_path.write_text(content, encoding="utf-8")

    manifest_path = ROOT / "policies" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for document in manifest["documents"]:
        if document["termsCode"] != "privacy_policy":
            continue
        if document["version"] == VERSION:
            document["aliases"] = [PUBLIC_ALIAS]
        elif PUBLIC_ALIAS in document.get("aliases", []):
            document["aliases"] = [
                alias for alias in document["aliases"] if alias != PUBLIC_ALIAS
            ]
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    sums = ROOT / "policies" / "SHA256SUMS"
    sums.write_text(
        "".join(f'{item["sha256"]}  {item["sourcePath"]}\n' for item in manifest["documents"]),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
