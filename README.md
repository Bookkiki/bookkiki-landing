# bookkiki-landing

북끼끼 심사용 랜딩 페이지이다. PG(KG이니시스) 계약과 카드사 심사, 통신판매업 신고에 필요한 "사업자 정보·상품·가격·정책·결제창"을 웹에 노출하는 것이 목적이다. 빌드 도구 없이 정적 HTML만 있다. 공개 주소는 https://bookkiki.com 예정.

## 구성

| 파일 | 내용 |
|---|---|
| `index.html` | 서비스 소개, 만드는 과정, 가격(실물책·구독 플랜), FAQ, 고객센터, 사업자 정보 푸터 |
| `order.html` | 심사용 실물책 주문 페이지. PortOne V2 SDK로 KG이니시스 테스트 결제창을 연다. 내비게이션에 노출하지 않고 URL로만 전달한다 |
| `terms.html` | 이용약관 (전자상거래 표준약관 기반, 맞춤 제작 청약철회 제한·정기결제·AI 생성물 조항 포함) |
| `privacy.html` | 개인정보처리방침 (아동 정보, 처리 위탁, 국외 이전 포함) |
| `refund.html` | 취소·환불·배송 정책 |
| `assets/style.css` | 공통 스타일. 색상은 앱 `BookkikiColors.light` 팔레트를 그대로 쓴다 |
| `assets/logo.svg` | 임시 로고. 정식 로고가 나오면 교체한다 |

## 버전 고정 정책 문서

회원이 동의한 2026-09-03 원문은 아래 경로에 원본 HTML 그대로 보존한다. 기존 버전 파일은 수정하거나 새 약관 본문으로 덮어쓰지 않는다.

| 문서 | 공개 경로 |
|---|---|
| 서비스 이용약관 | `/ko-KR/policies/terms-of-use/2026-09-03` |
| 개인정보 수집·이용 동의 | `/ko-KR/consents/personal-information-collection/2026-09-03` |
| 마케팅 정보 수신 동의 | `/ko-KR/consents/marketing-information/2026-09-03` |
| 광고성 정보 수신동의 신규 원문 | `/ko-KR/consents/marketing-information/2026-09-15` |
| 개인정보처리방침 | `/ko-KR/policies/privacy-policy` |
| 개인정보처리방침 2026-09-03 보존본 | `/ko-KR/policies/privacy-policy/2026-09-03` |

`policies/manifest.json`은 문서별 `termsCode`, version, locale, 공고일, 시행일, SHA-256, 원본 파일과 공개 경로를 연결한다. `policies/SHA256SUMS`는 manifest와 같은 해시를 담으며 검증 과정에서 서로 일치해야 한다. 현재 이용약관과 개인정보처리방침의 무버전 경로는 새 정책이 승인되기 전까지 2026-09-03 원문과 같은 파일을 제공한다.

기존 version의 원문과 manifest 항목은 수정하거나 삭제할 수 없다. 개정 문서는 새 version으로 추가한다. 검증·장애 복구 절차는 [`docs/policy-document-recovery.md`](docs/policy-document-recovery.md)에 기록한다.

로컬 원문 무결성은 다음 명령으로 확인한다.

```bash
./scripts/check-policy-documents.sh
```

배포 후 공개 URL의 응답과 원문 일치 여부는 다음 명령으로 확인한다.

```bash
./scripts/check-policy-documents.sh https://www.bookkiki.com
```

GitHub Actions의 `Policy documents` workflow는 pull request에서 원문 해시를 검사하고, 매일 공개 URL 4종의 응답과 원문 일치를 점검한다.

## 확정된 값과 임시 값

- 사업자 정보는 사업자등록증(2026-09-08 발급, 개업일 2026-09-16) 기준. 약관·방침 시행일도 개업일로 맞췄다.
- 실물책 가격은 서버 `docs/feature/BK-785` 기준. 제작 소요는 영업일 5일, 배송 1~3일로 적었다. 이니시스 사전심사의 최대 배송기간은 "8일~15일 이내"로 맞춘다.
- 구독 플랜은 임시 가격이다: Basic 월 9,900원(동화 4권), Premium 월 19,900원(동화 12권). 바꿔도 된다. 심사에서는 "실제 판매가로 표시돼 있는가"만 보므로 0원·미정 표기만 피한다.
- 인터뷰 음성 보관 30일, 정기결제 실패 재시도 7일, 플랜 부분 환불은 회당 요금 차감 방식으로 적었다. 운영 방식이 다르면 고친다.

## 배포 전 체크리스트

GA4 도입 전 별도 개인정보 최소화·스토어 신고 게이트는
[`docs/BK-903-ga4-release-gate.md`](docs/BK-903-ga4-release-gate.md)를 따른다.

1. **남은 노란 표시(`mark.todo`)는 전화번호뿐이다.** 고객센터 전화번호를 정해 4곳(index 2, privacy 1, refund 1)에 넣는다.

   ```bash
   grep -c 'class="todo"' index.html terms.html privacy.html refund.html order.html
   ```

   전부 0이어야 한다.
2. `contact@bookkiki.com` 메일이 실제로 수신되게 만든다(Google Workspace 또는 포워딩). 다른 주소를 쓰면 index 3곳, privacy 1곳, refund 1곳을 바꾼다.
3. `order.html`의 `CHANNEL_KEY`에 PortOne 콘솔의 KG이니시스 **테스트** 채널 키를 넣는다. 비어 있으면 결제 버튼이 비활성화된다. 운영 채널 키는 넣지 않는다. 심사 통과 후 이 페이지는 내리거나 앱 딥링크로 바꾼다.
4. 통신판매업신고번호는 신고증이 나온 뒤 "신고 진행 중"을 번호로 바꾼다(index 푸터, order 푸터).
5. 약관·개인정보처리방침·환불정책은 초안이다. 공개 전에 법률 검토를 받는다.

## 심사 요건 대응

| PG·카드사 심사가 보는 것 | 위치 |
|---|---|
| 상호·대표자·사업자등록번호·주소·연락처 | `index.html` 푸터 |
| 판매 상품과 가격 | `index.html` #pricing |
| 구매 시 이니시스 결제창 노출 | `order.html` |
| 이용약관 | `terms.html` |
| 개인정보처리방침 | `privacy.html` (푸터에서 굵게 링크) |
| 청약철회·환불·배송 조건 | `refund.html`, `terms.html` 제13~17조 |
| 고객센터 연락처·운영시간 | `index.html` #contact |
| 정기결제 안내·해지 방법 | `index.html` 플랜 카드, `refund.html` 3, `terms.html` 제17조 |

## 로컬 미리보기

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

`http://127.0.0.1:8765` 로 연다. `.claude/launch.json` 에 같은 설정이 있다.

## 배포 (GitHub Pages)

저장소: https://github.com/Bookkiki/bookkiki-landing (public. Free 조직은 public 저장소만 Pages를 쓸 수 있다.)

1. Settings > Pages > Source: `Deploy from a branch`, Branch `main` / `/ (root)`.
2. Custom domain에 `bookkiki.com` 입력, 저장 후 `Enforce HTTPS` 켠다. 루트에 `CNAME` 파일이 생긴다.
3. Route 53 `bookkiki.com` 호스팅 존에 레코드 추가.
   - `bookkiki.com` A → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `www.bookkiki.com` CNAME → `bookkiki.github.io`
4. 인증서 발급까지 수십 분 걸린다. `https://bookkiki.com` 이 열리면 PortOne 신청서의 서비스 URL, 이니시스 사전심사 URL과 일치하는지 확인한다.

S3 + CloudFront로 옮기려면 `bookkiki-infrastructure` 에 정적 사이트 모듈을 추가한다.
