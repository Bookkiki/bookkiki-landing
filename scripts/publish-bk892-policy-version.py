#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "policies" / "manifest.json"
SHA256SUMS_PATH = REPO_ROOT / "policies" / "SHA256SUMS"
BASE_VERSION = "2026-09-03"
LOCALE = "ko-KR"
TARGET_CODES = (
    "terms_of_service",
    "personal_information_collection_consent",
    "privacy_policy",
)
PUBLIC_ROUTE_PREFIXES = {
    "terms_of_service": "/ko-KR/policies/terms-of-use",
    "personal_information_collection_consent": "/ko-KR/consents/personal-information-collection",
    "privacy_policy": "/ko-KR/policies/privacy-policy",
}

TEXT_REPLACEMENTS = {
    "terms_of_service": (
        (
            "Bookkiki 회원 계정은 Google OAuth로 로그인합니다.",
            "Bookkiki 회원 계정은 Google·Kakao·Naver·Apple 소셜 로그인으로 로그인합니다.",
        ),
        (
            "Bookkiki는 Google 계정의 비밀번호를 전달받거나 저장하지 않습니다.",
            "Bookkiki는 로그인 제공자 계정의 비밀번호를 전달받거나 저장하지 않습니다.",
        ),
        (
            "현재 서비스의 회원가입과 로그인은 Google OAuth 방식으로 제공됩니다. 회원은 본인이 적법하게 사용할 수 있는 Google 계정으로 로그인해야 합니다.",
            "현재 서비스의 회원가입과 로그인은 Google·Kakao·Naver·Apple 소셜 로그인 방식으로 제공됩니다. 회원은 본인이 적법하게 사용할 수 있는 로그인 제공자 계정으로 로그인해야 합니다.",
        ),
        (
            "회사는 Google 계정의 비밀번호를 전달받거나 저장하지 않습니다. Google에서 발급한 인증정보는 로그인 확인에 사용하고, 로그인 후에는 Bookkiki 서비스 이용을 위한 별도의 인증 토큰을 발급·관리합니다.",
            "회사는 로그인 제공자 계정의 비밀번호를 전달받거나 저장하지 않습니다. 로그인 제공자가 발급한 인증정보는 로그인 확인에 사용하고, 로그인 후에는 Bookkiki 서비스 이용을 위한 별도의 인증 토큰을 발급·관리합니다.",
        ),
        (
            "회원은 Google 계정, 로그인된 기기 및 Bookkiki 인증정보를 안전하게 관리해야 하며, 이를 제3자에게 양도하거나 공유해서는 안 됩니다.",
            "회원은 로그인 제공자 계정, 로그인된 기기 및 Bookkiki 인증정보를 안전하게 관리해야 하며, 이를 제3자에게 양도하거나 공유해서는 안 됩니다.",
        ),
    ),
    "personal_information_collection_consent": (
        (
            "회원 식별, Google OAuth 회원가입·로그인, 계정 관리, 약관 동의 이력 관리",
            "회원 식별, Google·Kakao·Naver·Apple 소셜 계정 회원가입·로그인, 계정 관리, 약관 동의 이력 관리",
        ),
        (
            "회원 식별자, 로그인 제공자(Google), Google 제공자 회원 식별자, 약관 코드·버전·동의 시각",
            "회원 식별자, 로그인 제공자(Google·Kakao·Naver·Apple), 제공자 회원 식별자, 제공되고 확인된 이메일, 약관 코드·버전·동의 시각",
        ),
        (
            "현재 Bookkiki 서버는 Google 계정의 이메일, 이름, 프로필 사진을 회원정보로 저장하지 않습니다.",
            "Bookkiki 서버는 로그인 제공자가 제공한 이메일을 OAuth 신원 정보로 저장할 수 있으며, 로그인 제공자 계정의 비밀번호·이름·프로필 사진과 인증 Token 원문은 저장하지 않습니다.",
        ),
    ),
    "privacy_policy": (
        (
            "회원 식별자, 로그인 제공자(Google), 제공자 회원 식별자, 약관 코드·버전·동의 시각. 현재 서버는 Google 계정의 이메일·이름·프로필 사진을 회원정보로 저장하지 않음",
            "회원 식별자, 로그인 제공자(Google·Kakao·Naver·Apple), 제공자 회원 식별자, 제공되고 확인된 이메일, 약관 코드·버전·동의 시각. 로그인 제공자 계정의 비밀번호·이름·프로필 사진과 인증 Token 원문은 저장하지 않음",
        ),
        (
            "Google 등 로그인 제공자로부터 회원이 제공에 동의한 정보를 전달받는 방법",
            "Google·Kakao·Naver·Apple 로그인 제공자로부터 회원이 제공에 동의한 정보를 전달받는 방법",
        ),
    ),
}

OLD_LOGIN_PROCESSOR_ROW = (
    "<tr><td>Google LLC</td><td>Google 소셜 로그인 인증</td>"
    "<td>Google ID Token과 제공자 회원 식별자. ID Token은 검증 후 저장하지 않음</td>"
    "<td>인증 처리 시까지. 제공자 회원 식별자는 연동 해제 또는 회원 탈퇴 시까지</td></tr>"
)
NEW_LOGIN_PROCESSOR_ROW = (
    "<tr><td>Google LLC, Kakao Corp., NAVER Corp., Apple Inc.</td>"
    "<td>Google·Kakao·Naver·Apple 소셜 로그인 인증</td>"
    "<td>로그인 제공자의 ID Token 또는 Access Token, 제공자 회원 식별자와 제공된 이메일. 인증 Token은 검증 후 저장하지 않음</td>"
    "<td>인증 Token은 인증 처리 시까지. 제공자 회원 식별자와 제공된 이메일은 연동 해제 또는 회원 탈퇴 시까지</td></tr>"
)


def fail(message: str) -> None:
    raise ValueError(message)


def parse_iso_date(value: str, field: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO date: {value}") from error
    return value


def korean_date(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"{parsed.year}년 {parsed.month}월 {parsed.day}일"


def identity(document: dict) -> tuple[str, str, str]:
    return document["termsCode"], document["version"], document["locale"]


def react_escape(html: str) -> str:
    return html.replace("<", r"\u003c").replace(">", r"\u003e")


def replace_expected(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count == 0:
        fail(f"missing expected {label}: {old}")
    return text.replace(old, new)


def update_react_payload_length(text: str, terms_code: str) -> str:
    article_match = re.search(r'<article[^>]*>(.*?)</article>', text, re.DOTALL)
    marker_match = re.search(r"5:T([0-9a-f]+),", text)
    if article_match is None or marker_match is None:
        fail(f"{terms_code}: missing article or React payload length marker")
    article_length = len(article_match.group(1).encode("utf-8"))
    marker = marker_match.group(0)
    return text.replace(marker, f"5:T{article_length:x},", 1)


def revise_html(
    terms_code: str,
    source: str,
    version: str,
    announced_at: str,
    effective_at: str,
) -> str:
    revised = source
    for old, new in TEXT_REPLACEMENTS[terms_code]:
        revised = replace_expected(revised, old, new, terms_code)

    if terms_code == "privacy_policy":
        revised = replace_expected(
            revised,
            OLD_LOGIN_PROCESSOR_ROW,
            NEW_LOGIN_PROCESSOR_ROW,
            "privacy processor row",
        )
        revised = replace_expected(
            revised,
            react_escape(OLD_LOGIN_PROCESSOR_ROW),
            react_escape(NEW_LOGIN_PROCESSOR_ROW),
            "privacy processor row in React payload",
        )

    route_prefix = PUBLIC_ROUTE_PREFIXES[terms_code]
    if terms_code == "privacy_policy":
        old_canonical = f"https://www.bookkiki.com{route_prefix}"
    else:
        old_canonical = f"https://www.bookkiki.com{route_prefix}/{BASE_VERSION}"
    revised = replace_expected(
        revised,
        old_canonical,
        f"https://www.bookkiki.com{route_prefix}/{version}",
        f"{terms_code} canonical route",
    )

    if terms_code == "terms_of_service":
        revised = replace_expected(
            revised,
            f"서비스 이용약관 ({BASE_VERSION}) | BookKiki",
            f"서비스 이용약관 ({version}) | BookKiki",
            "terms title version",
        )

    base_korean_date = korean_date(BASE_VERSION)
    if terms_code == "privacy_policy":
        revised = replace_expected(
            revised,
            f"공고일: {base_korean_date}",
            f"공고일: {korean_date(announced_at)}",
            "privacy announced date",
        )
        revised = replace_expected(
            revised,
            f"시행일: {base_korean_date}",
            f"시행일: {korean_date(effective_at)}",
            "privacy effective date",
        )
    else:
        revised = replace_expected(
            revised,
            base_korean_date,
            korean_date(effective_at),
            f"{terms_code} effective date",
        )
    return update_react_payload_length(revised, terms_code)


def load_manifest() -> dict:
    with MANIFEST_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def base_documents(manifest: dict) -> dict[str, dict]:
    documents = {
        document["termsCode"]: document
        for document in manifest["documents"]
        if document["version"] == BASE_VERSION and document["locale"] == LOCALE
    }
    missing = set(TARGET_CODES) - documents.keys()
    if missing:
        fail(f"missing base documents: {sorted(missing)}")
    return documents


def prepare(
    manifest: dict,
    version: str,
    announced_at: str,
    effective_at: str,
) -> tuple[dict, dict[str, bytes]]:
    if version == BASE_VERSION:
        fail("new version must differ from the immutable base version")
    if any(
        identity(document) == (code, version, LOCALE)
        for document in manifest["documents"]
        for code in TARGET_CODES
    ):
        fail(f"version already exists: {version}")

    revised_manifest = deepcopy(manifest)
    bases = base_documents(revised_manifest)
    outputs: dict[str, bytes] = {}

    for code in TARGET_CODES:
        base = bases[code]
        source_path = REPO_ROOT / base["sourcePath"]
        revised = revise_html(
            code,
            source_path.read_text(encoding="utf-8"),
            version,
            announced_at,
            effective_at,
        )
        target_source_path = base["sourcePath"].replace(BASE_VERSION, version)
        target_public_path = base["publicPath"].replace(BASE_VERSION, version)
        encoded = revised.encode("utf-8")
        aliases = list(base["aliases"])
        base["aliases"] = []

        new_document = {
            **base,
            "version": version,
            "announcedAt": announced_at,
            "effectiveAt": effective_at,
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "sourcePath": target_source_path,
            "publicPath": target_public_path,
            "aliases": aliases,
        }
        revised_manifest["documents"].append(new_document)
        outputs[target_source_path] = encoded
        for alias in aliases:
            outputs[f"{alias.lstrip('/')}/index.html"] = encoded

    return revised_manifest, outputs


def sha256sums(manifest: dict) -> str:
    return "".join(
        f'{document["sha256"]}  {document["sourcePath"]}\n'
        for document in manifest["documents"]
    )


def write_outputs(manifest: dict, outputs: dict[str, bytes]) -> None:
    for relative_path, content in outputs.items():
        path = REPO_ROOT / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    SHA256SUMS_PATH.write_text(sha256sums(manifest), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare and publish the BK-892 social-login policy revision."
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--announced-at", required=True)
    parser.add_argument("--effective-at", required=True)
    parser.add_argument("--confirm-apple-ready", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the transformation without writing files or requiring Apple readiness",
    )
    args = parser.parse_args()

    try:
        version = parse_iso_date(args.version, "version")
        announced_at = parse_iso_date(args.announced_at, "announced-at")
        effective_at = parse_iso_date(args.effective_at, "effective-at")
        if date.fromisoformat(announced_at) > date.fromisoformat(effective_at):
            fail("announced-at must not be later than effective-at")
        manifest, outputs = prepare(load_manifest(), version, announced_at, effective_at)
        if args.check:
            for document in manifest["documents"]:
                if document["version"] == version:
                    print(
                        f'{document["termsCode"]}\t{document["sourcePath"]}\t{document["sha256"]}'
                    )
            return 0
        if not args.confirm_apple_ready:
            fail("publishing requires --confirm-apple-ready after BK-857 is Done")
        write_outputs(manifest, outputs)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"BK-892 policy publication failed: {error}", file=sys.stderr)
        return 1

    print(f"published BK-892 policy version {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
