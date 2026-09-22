#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

require_text() {
  local file="$1"
  local text="$2"
  grep -Fq "$text" "$file" || {
    echo "$file: missing required text: $text" >&2
    exit 1
  }
}

for page in index.html review.html order.html subscription.html terms.html privacy.html refund.html; do
  test -s "$page" || { echo "$page: missing or empty" >&2; exit 1; }
done

require_text order.html 'const SHIPPING = 3000;'
require_text order.html 'PortOne.requestPayment'
require_text order.html '영업일 기준 5일'
require_text order.html 'id="address"'
require_text subscription.html 'PortOne.requestIssueBillingKey'
require_text subscription.html 'offerPeriod: { interval: "1m" }'
require_text subscription.html 'issueName: `북끼끼 매월 ${plan.price.toLocaleString("ko-KR")}원 정기결제`'
require_text subscription.html 'BILLING_CHANNEL_KEY'
require_text review.html 'id="general-payment"'
require_text review.html 'id="recurring-payment"'
require_text review.html 'PortOne.requestPayment'
require_text review.html 'PortOne.requestIssueBillingKey'
require_text review.html 'offerPeriod: { interval: "1m" }'
require_text review.html 'const SHIPPING = 3000;'
require_text index.html 'href="review.html#general-payment"'
require_text index.html 'href="review.html#recurring-payment"'

# KG이니시스는 빌링키 발급 상품명을 UTF-8 기준 최대 40바이트까지 표시한다.
test "$(printf %s '북끼끼 매월 19,900원 정기결제' | wc -c | tr -d ' ')" -le 40

for page in index.html review.html order.html subscription.html; do
  require_text "$page" '525-43-01349'
  require_text "$page" '황채원'
  require_text "$page" '010-2497-1267'
  require_text "$page" '경기도 안산시 단원구 원선1로 10'
done

if grep -ERq 'MOI8341143|MOI5492858|PORTONE_API_SECRET|INIAPI Key|INILite Key|signkey' --include='*.html' .; then
  echo 'payment review pages must not contain production MID or secret-key material' >&2
  exit 1
fi

test "$(grep -c 'class="required-agreement"' order.html)" -ge 3
test "$(grep -c 'class="required-agreement"' subscription.html)" -ge 4
test "$(grep -c 'class="order-required-agreement"' review.html)" -ge 3
test "$(grep -c 'class="subscription-required-agreement"' review.html)" -ge 4

echo 'payment review pages: OK'
