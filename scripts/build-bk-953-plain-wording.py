#!/usr/bin/env python3
"""Reissue the BK-953 pages with the plain-wording legal copy.

동의서 2026-09-26-1·개인정보처리방침 2026-09-26-2 판에는 `enable_logging`, Server, UUID 같은 개발자용
문장이 남아 있다. 이를 이용자용 문장으로 고친 원문으로 동의서 2026-09-26-2, 개인정보처리방침
2026-09-26-3 판을 발행한다. 문서 code·버전·원본 해시를 빼는 처리는
build-bk-953-without-internal-labels.py와 같고, 개발자용 표현이 남으면 발행이 실패한다.
이전 version의 bytes는 건드리지 않는다.
"""

from __future__ import annotations

import importlib.util
import re
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVELOPER_TERMS = re.compile(
    r"enable_logging|content_redacted|character_kind|store=|UUID|Worker|Server|endpoint|"
    r"ZDR|ZRM|MAM|STT|TTS|queue|cache|backup|retry|session|snapshot|upload|reader|watermark|"
    r"secret|\btoken\b|\btext\b|\blog\b|HTTP \d{3}|프롬프트|호출"
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
    labels = load("build-bk-953-without-internal-labels.py", "bk953_labels")
    bk953 = load("build-bk-953-legal-docs.py", "bk953")
    bk953.CONSENT_VERSION = "2026-09-26-2"
    bk953.PRIVACY_VERSION = "2026-09-26-3"

    without_banner = bk953.without_banner

    def plain_page(page: str, label: str) -> str:
        page = without_banner(page, label)
        for pattern in labels.INTERNAL_LABELS:
            page = pattern.sub("", page)
        text = bk953.visible_text(page)
        remaining = labels.REMAINING_LABEL.search(text) or DEVELOPER_TERMS.search(text)
        if remaining:
            raise ValueError(f"{label}: internal or developer wording remains: {remaining.group(0)}")
        return page

    bk953.without_banner = plain_page
    bk953.main()


if __name__ == "__main__":
    main()
