#!/usr/bin/env python3
"""Issue immutable 2026-09-17 revisions that disclose the Langfuse observation transfer.

AI 인터뷰와 동화·삽화 생성 호출의 품질 관측(Langfuse Cloud)은 2026-09-15(BK-891)부터 운영에서
실제로 돌지만 2026-09-15 원문에는 수령자로 적혀 있지 않았다. 이 script는 그 두 국외 이전 동의와
개인정보처리방침만 새 version으로 발행한다. 기존 version의 bytes는 건드리지 않는다.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-09-17"
# 관측 수령자가 실제로 붙는 두 문서만 개정한다. 나머지 다섯 동의의 전송 항목은 그대로다.
REVISED = (
    ("Anthropic AI 인터뷰", "overseas_anthropic_interview_consent"),
    ("OpenAI 동화·삽화 생성", "overseas_openai_story_generation_consent"),
)


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
    parser.add_argument("overseas_source", type=Path)
    parser.add_argument("privacy_source", type=Path)
    args = parser.parse_args()
    overseas = args.overseas_source.read_text(encoding="utf-8")
    privacy = args.privacy_source.read_text(encoding="utf-8")
    # 원문이 실제로 Langfuse 개정본인지 확인한다. 확인 없이 발행하면 같은 내용을 새 version으로
    # 다시 찍어 이용자에게 의미 없는 재동의를 요구하게 된다.
    if "Langfuse GmbH" not in overseas or "Langfuse" not in privacy:
        raise ValueError("expected the Langfuse-disclosing source copy")
    if "판정 근거" not in overseas:
        raise ValueError("free-text evidence disclosure must stay in the overseas copy")

    preview = load("build-bk-870-preview.py", "bk870_langfuse_preview")
    operating = load("build-bk-870-operating.py", "bk870_langfuse_operating")
    operating.VERSION = VERSION

    parts = preview.sections(overseas)
    overseas_digest = hashlib.sha256(overseas.encode("utf-8")).hexdigest()
    documents: list[dict] = []
    for title, code in REVISED:
        if parts[title].count(f"문서 code: `{code}`") != 1:
            raise ValueError(f"document code mismatch: {code}")
        route = f"/ko-KR/consents/overseas-transfer/{code}/{VERSION}"
        rendered = preview.page(title, code, parts[title], parts["철회와 삭제"], overseas_digest)
        path, digest = operating.add_file(route, operating.public_html(rendered, route))
        documents.append(operating.registration(code, route, path, digest))
        print(route)

    # 개정하지 않은 다섯 동의는 2026-09-15 목록을 그대로 가리킨다.
    route = f"/ko-KR/policies/privacy-policy/{VERSION}"
    privacy_digest = hashlib.sha256(privacy.encode("utf-8")).hexdigest()
    content = operating.public_html(
        preview.privacy_page(privacy, privacy_digest), route, privacy=True
    ).replace(
        f'href="/ko-KR/consents/overseas-transfer/{VERSION}"',
        'href="/ko-KR/consents/overseas-transfer/2026-09-15"',
    )
    path, digest = operating.add_file(route, content)
    documents.append(operating.registration("privacy_policy", route, path, digest))
    print(route)

    operating.update_manifest(documents)


if __name__ == "__main__":
    main()
