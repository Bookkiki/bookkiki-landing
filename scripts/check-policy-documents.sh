#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

shasum -a 256 -c policies/SHA256SUMS
cmp ko-KR/policies/terms-of-use/2026-09-03/index.html \
  ko-KR/policies/terms-of-use/index.html
cmp ko-KR/policies/privacy-policy/2026-09-03/index.html \
  ko-KR/policies/privacy-policy/index.html

if [[ $# -eq 0 ]]; then
  exit 0
fi

base_url="${1%/}"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

verify_remote() {
  local route="$1"
  local expected_file="$2"
  local downloaded_file="$tmp_dir/$(printf '%s' "$route" | tr '/' '_').html"

  curl --fail --location --silent --show-error \
    "$base_url$route" \
    --output "$downloaded_file"
  cmp "$expected_file" "$downloaded_file"
  printf 'OK %s%s\n' "$base_url" "$route"
}

verify_remote \
  /ko-KR/policies/terms-of-use/2026-09-03 \
  ko-KR/policies/terms-of-use/2026-09-03/index.html
verify_remote \
  /ko-KR/consents/personal-information-collection/2026-09-03 \
  ko-KR/consents/personal-information-collection/2026-09-03/index.html
verify_remote \
  /ko-KR/consents/marketing-information/2026-09-03 \
  ko-KR/consents/marketing-information/2026-09-03/index.html
verify_remote \
  /ko-KR/policies/privacy-policy \
  ko-KR/policies/privacy-policy/2026-09-03/index.html
