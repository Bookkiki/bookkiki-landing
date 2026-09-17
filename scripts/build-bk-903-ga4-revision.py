#!/usr/bin/env python3
"""Issue the immutable 2026-09-17-1 privacy-policy revision that discloses Google Analytics.

앱 1.0.0+6부터 보호자가 설정에서 켠 경우에만 Google Analytics for Firebase로 사용 분석
이벤트를 보내지만, 2026-09-17 원문 10항에는 analytics 도구가 `[출시 전 확정 필요]`로만
남아 있었다. 이 script는 개인정보처리방침만 새 version으로 발행한다. 국외 이전 동의서와
그 외 원문의 bytes는 건드리지 않는다. Google로의 처리위탁·보관은 개인정보 보호법
제28조의8 제1항 제3호에 따라 별도 동의 대신 이 방침으로 고지한다.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-09-17-1"
EFFECTIVE = "2026-09-17"


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
    # 원문이 실제로 GA4 고지 개정본인지 확인한다. 같은 내용을 새 version으로 다시 찍으면
    # 이용자에게 의미 없는 개정 고지를 하게 된다.
    if "DRAFT-2026-09-14" not in source or "Google Analytics for Firebase" not in source:
        raise ValueError("expected the Google Analytics-disclosing source copy")
    if "제28조의8 제1항 제3호" not in source:
        raise ValueError("the overseas processing notice basis must stay in the copy")
    if "analytics·crash 도구" in source:
        raise ValueError("the analytics placeholder must be resolved in this revision")
    # 이 개정에서 Langfuse 고지(2026-09-17)가 사라지면 안 된다.
    if "Langfuse GmbH" not in source:
        raise ValueError("the Langfuse disclosure must survive this revision")

    preview = load("build-bk-870-preview.py", "bk903_privacy_preview")
    operating = load("build-bk-870-operating.py", "bk903_privacy_operating")
    operating.VERSION = VERSION
    route = f"/ko-KR/policies/privacy-policy/{VERSION}"
    source_digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    draft = preview.privacy_page(source, source_digest)
    # 국외 이전 동의서 목록 page는 2026-09-15 경로만 있다(개별 동의는 2026-09-17로 개정됨).
    content = operating.public_html(draft, route, privacy=True).replace(
        f'href="/ko-KR/consents/overseas-transfer/{VERSION}"',
        'href="/ko-KR/consents/overseas-transfer/2026-09-15"',
    )
    path, digest = operating.add_file(route, content)
    document = operating.registration("privacy_policy", route, path, digest)
    document["effectiveAt"] = EFFECTIVE
    operating.update_manifest([document])
    print(route)
    print(digest)


if __name__ == "__main__":
    main()
