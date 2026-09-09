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

## 확정된 값과 임시 값

- 사업자 정보는 사업자등록증(2026-09-08 발급, 개업일 2026-09-16) 기준. 약관·방침 시행일도 개업일로 맞췄다.
- 실물책 가격은 서버 `docs/feature/BK-785` 기준. 제작 소요는 영업일 5일, 배송 1~3일로 적었다. 이니시스 사전심사의 최대 배송기간은 "8일~15일 이내"로 맞춘다.
- 구독 플랜은 임시 가격이다: Basic 월 9,900원(동화 4권), Premium 월 19,900원(동화 12권). 바꿔도 된다. 심사에서는 "실제 판매가로 표시돼 있는가"만 보므로 0원·미정 표기만 피한다.
- 인터뷰 음성 보관 30일, 정기결제 실패 재시도 7일, 플랜 부분 환불은 회당 요금 차감 방식으로 적었다. 운영 방식이 다르면 고친다.

## 배포 전 체크리스트

1. **남은 노란 표시(`mark.todo`)는 전화번호뿐이다.** 고객센터 전화번호를 정해 4곳(index 2, privacy 1, refund 1)에 넣는다.

   ```bash
   grep -c 'class="todo"' index.html terms.html privacy.html refund.html order.html
   ```

   전부 0이어야 한다.
2. `hello@bookkiki.com` 메일이 실제로 수신되게 만든다(Google Workspace 또는 포워딩). 다른 주소를 쓰면 index 3곳, privacy 1곳, refund 1곳을 바꾼다.
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
