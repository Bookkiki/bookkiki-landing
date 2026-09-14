#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python3 scripts/check-policy-manifest.py
shasum -a 256 -c policies/SHA256SUMS

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

while IFS=$'\t' read -r expected_file route; do
  verify_remote "$route" "$expected_file"
done < <(python3 scripts/check-policy-manifest.py --routes)
