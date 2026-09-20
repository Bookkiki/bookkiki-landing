#!/usr/bin/env python3
"""Reissue the BK-892 signup terms so the four-provider notice takes effect immediately.

2026-09-18 판은 이용약관 제3조의 7일 사전공지에 맞춰 시행일을 2026-09-25로 적었다. 그런데
소셜 로그인 4종 고지가 그 판에만 있어, 시행 전까지 앱에 보이는 정본은 "회원가입과 로그인은
Google OAuth 방식으로 제공됩니다"라고 적은 2026-09-03 판이다. 앱은 Google·Kakao·Naver·
Apple 4종을 띄우므로 BK-892가 없애려던 불일치가 시행일까지 그대로 남는다.

Prod 앱이 출시된 적이 없어 2026-09-03 판에 동의한 회원이 없다. 제3조 3항의 사전공지는 기존
회원을 보호하는 규정이므로 대상이 없고, 신규 가입자는 가입 시점에 이 판에 직접 동의한다.
그래서 공고일과 시행일이 같은 새 판을 발행한다.

또 실물책 결제는 요청의 동의 문서를 시행 중 정본과 version까지 비교한다
(`CreateBookOrderPaymentService`). 앱은 `GET /v1/terms/required`가 준 최신 version만 보낼 수
있어, 등록 version과 시행 중 정본이 어긋나면 결제가 전부 거절된다. 시행일을 발행일과 맞추면
이 창이 생기지 않는다.

2026-09-18 판의 bytes와 manifest 항목은 건드리지 않는다. 시행일이 지났으므로 이용약관의
무버전 alias는 이 판으로 옮긴다.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "policies" / "manifest.json"
SHA256SUMS_PATH = ROOT / "policies" / "SHA256SUMS"

BASE_VERSION = "2026-09-18"
VERSION = "2026-09-20"
ANNOUNCED = "2026-09-20"
EFFECTIVE = "2026-09-20"
LOCALE = "ko-KR"

BASE_EFFECTIVE_TEXT = "2026년 9월 25일"
NEW_EFFECTIVE_TEXT = "2026년 9월 20일"

TARGET_CODES = ("terms_of_service", "personal_information_collection_consent")
ROUTE_PREFIXES = {
    "terms_of_service": "/ko-KR/policies/terms-of-use",
    "personal_information_collection_consent": "/ko-KR/consents/personal-information-collection",
}
# 시행일이 되었으므로 무버전 경로를 이 판으로 옮긴다. 수집·이용 동의서는 alias를 쓰지 않는다.
ALIASES = {"terms_of_service": ["/ko-KR/policies/terms-of-use"]}

# 2026-09-18 판이 실제로 4종 고지본인지 확인하는 표지다.
REQUIRED_PHRASES = {
    "terms_of_service": (
        "현재 서비스의 회원가입과 로그인은 Google·Kakao·Naver·Apple 소셜 로그인 방식으로 제공됩니다.",
        "회사는 로그인 제공자 계정의 비밀번호를 전달받거나 저장하지 않습니다.",
    ),
    "personal_information_collection_consent": (
        "로그인 제공자(Google·Kakao·Naver·Apple)",
        "제공자가 제공한 이메일",
    ),
}


def load(name: str, module_name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_loader(module_name, SourceFileLoader(module_name, str(path)))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


revision = load("build-bk-892-signup-terms-revision.py", "bk892_signup_revision")


def base_document(manifest: dict, code: str) -> dict:
    for document in manifest["documents"]:
        if (document["termsCode"], document["version"], document["locale"]) == (
            code,
            BASE_VERSION,
            LOCALE,
        ):
            return document
    raise ValueError(f"missing base document: {code} {BASE_VERSION}")


def revise(code: str, source: str) -> str:
    for phrase in REQUIRED_PHRASES[code]:
        if phrase not in source:
            raise ValueError(f"{code}: base document is not the four-provider revision: {phrase}")
    if NEW_EFFECTIVE_TEXT in source:
        raise ValueError(f"{code}: base document already carries the new effective date")

    revised = revision.replace_expected(
        source, BASE_EFFECTIVE_TEXT, NEW_EFFECTIVE_TEXT, f"{code} effective date"
    )
    prefix = ROUTE_PREFIXES[code]
    revised = revision.replace_expected(
        revised,
        f"https://www.bookkiki.com{prefix}/{BASE_VERSION}",
        f"https://www.bookkiki.com{prefix}/{VERSION}",
        f"{code} canonical route",
    )
    if code == "terms_of_service":
        revised = revision.replace_expected(
            revised,
            f"서비스 이용약관 ({BASE_VERSION}) | BookKiki",
            f"서비스 이용약관 ({VERSION}) | BookKiki",
            "terms title version",
        )
    if BASE_EFFECTIVE_TEXT in revised:
        raise ValueError(f"{code}: the old effective date survived the revision")
    return revision.update_react_payload_length(revised, code)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if any(
            (d["termsCode"], d["version"], d["locale"]) == (code, VERSION, LOCALE)
            for d in manifest["documents"]
            for code in TARGET_CODES
        ):
            raise ValueError(f"version already exists: {VERSION}")

        outputs: dict[str, bytes] = {}
        registered: list[dict] = []
        for code in TARGET_CODES:
            base = base_document(manifest, code)
            content = revise(code, (ROOT / base["sourcePath"]).read_text(encoding="utf-8"))
            encoded = content.encode("utf-8")
            source_path = base["sourcePath"].replace(BASE_VERSION, VERSION)
            aliases = ALIASES.get(code, [])
            registered.append(
                {
                    **base,
                    "version": VERSION,
                    "announcedAt": ANNOUNCED,
                    "effectiveAt": EFFECTIVE,
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                    "sourcePath": source_path,
                    "publicPath": base["publicPath"].replace(BASE_VERSION, VERSION),
                    "aliases": aliases,
                }
            )
            outputs[source_path] = encoded
            for alias in aliases:
                outputs[f"{alias.lstrip('/')}/index.html"] = encoded

        if args.check:
            for document in registered:
                print(f'{document["termsCode"]}\t{document["publicPath"]}\t{document["sha256"]}')
            return 0

        # 무버전 alias는 한 version만 보유한다. 이전 보유 항목에서 뺀다.
        moved = {alias for document in registered for alias in document["aliases"]}
        for document in manifest["documents"]:
            if document["termsCode"] in TARGET_CODES and document.get("aliases"):
                document["aliases"] = [a for a in document["aliases"] if a not in moved]
        manifest["documents"].extend(registered)

        for relative_path, content in outputs.items():
            path = ROOT / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        MANIFEST_PATH.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        SHA256SUMS_PATH.write_text(revision.sha256sums(manifest), encoding="utf-8")
        for document in registered:
            print(f'{document["termsCode"]}\t{document["publicPath"]}\t{document["sha256"]}')
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"BK-892 effective-date reissue failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
