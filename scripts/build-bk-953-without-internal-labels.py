#!/usr/bin/env python3
"""Reissue the BK-953 pages without internal labels.

BK-953 판(동의서 2026-09-26, 개인정보처리방침 2026-09-26-1)은 문서 code·버전과 원본 Markdown 해시를
본문에 보여 준다. 이용자에게 의미 없는 내부 식별값이라 이 표기만 뺀 판(동의서 2026-09-26-1,
개인정보처리방침 2026-09-26-2)을 같은 원문으로 발행한다. 방침의 공고일·시행일은 남긴다.
발행 절차와 미완성 표기 검사는 build-bk-953-legal-docs.py를 그대로 쓰고, 이전 version의 bytes는
건드리지 않는다.
"""

from __future__ import annotations

import importlib.util
import re
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERNAL_LABELS = (
    re.compile(r'\n?[ \t]*<p>문서 code: <code>[a-z_]+</code> · 버전: <code>[0-9-]+</code></p>'),
    re.compile(r'\n?<li>문서 code: <code>[a-z_]+</code></li>'),
    re.compile(r'\n?<li>version: <code>[0-9-]+</code></li>'),
    re.compile(r'\n?[ \t]*<footer>원본 Markdown SHA-256: <code>[0-9a-f]{64}</code></footer>'),
)
REMAINING_LABEL = re.compile(r"문서 code|버전:|version:|SHA-256")


def load_bk953():
    path = ROOT / "scripts" / "build-bk-953-legal-docs.py"
    spec = importlib.util.spec_from_loader("bk953", SourceFileLoader("bk953", str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load build-bk-953-legal-docs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    bk953 = load_bk953()
    bk953.CONSENT_VERSION = "2026-09-26-1"
    bk953.PRIVACY_VERSION = "2026-09-26-2"

    without_banner = bk953.without_banner

    def without_banner_and_labels(page: str, label: str) -> str:
        page = without_banner(page, label)
        for pattern in INTERNAL_LABELS:
            page = pattern.sub("", page)
        remaining = REMAINING_LABEL.search(bk953.visible_text(page))
        if remaining:
            raise ValueError(f"{label}: internal label remains: {remaining.group(0)}")
        return page

    bk953.without_banner = without_banner_and_labels
    bk953.main()


if __name__ == "__main__":
    main()
