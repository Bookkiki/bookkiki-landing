# BK-903 보호자 동의 기반 GA4 출시 게이트

이 문서는 앱 행동 분석을 켜기 전에 제품·정책·스토어 설정이 함께 충족됐는지 확인하는
내부 체크리스트다. 기존 공개 약관 원문은 변경하지 않는다. 아래 미확정 값이 확정되고
법률 검토가 끝나기 전에는 새 개인정보처리방침 version을 발행하지 않는다.

## 확정된 제품 원칙

- Firebase Analytics 수집 기본값은 OFF다.
- 보호자가 설정에서 별도로 동의한 뒤에만 수집한다.
- 철회는 같은 화면에서 가능하고, 철회 즉시 새 수집을 중단한다.
- 자동 화면 추적, 광고 ID(AAID/IDFA), 개인 맞춤 광고 신호를 사용하지 않는다.
- 앱이 직접 기록하는 사용자 정의 이벤트는 닫힌 allowlist의 행동 이벤트로 제한한다.
- 사용자 ID와 user property를 설정하지 않는다.
- 사진·음성·인터뷰·동화 원문과 아이·보호자의 식별정보는 보내지 않는다.

보호자 동의 후 Firebase가 앱 버전·OS·기기 종류와 `first_open`, `session_start`,
`user_engagement` 같은 기본 이벤트를 함께 처리할 수 있다는 점은 동의 화면과 공개 정책에
고지한다. 자동 화면 추적은 비활성화한다.

`14세 이상` 표시는 광고 식별자 사용의 자동 허가가 아니다. Google Play의 13~15세와
16~17세 대상은 지역에 따라 아동으로 취급될 수 있고, 북끼끼의 실제 콘텐츠와 기능도
아이를 직접 대상으로 한다. 따라서 광고 상품을 도입하고 보호자/성인만 통과하는 neutral
age screen과 스토어 신고를 별도로 검증하기 전까지 AAID·IDFA와 광고 개인화는 계속 끈다.
이는 앱 홍보나 보호자의 광고성 정보 수신 동의를 없애는 조치가 아니라, 기기 광고
식별자를 Analytics SDK에 보내지 않는 조치다.

## 수집 허용 범위

| 이벤트 | 의미 | 허용 파라미터 |
|---|---|---|
| `settings_opened` | 설정 화면 진입 | 없음 |
| `analytics_consent_opened` | 사용 분석 동의 화면 진입 | 없음 |
| `profile_management_opened` | 자녀 프로필 관리 진입 | 없음 |
| `child_profile_creation_opened` | 자녀 프로필 생성 흐름 진입 | 없음 |
| `child_profile_created` | 자녀 프로필 생성 완료 | 없음 |
| `character_creation_opened` | 캐릭터 생성 흐름 진입 | 없음 |
| `character_creation_continued` | 캐릭터 결과에서 계속 진행 | 없음 |
| `character_history_opened` | 캐릭터 관리 이력 진입 | 없음 |
| `interview_opened` | 인터뷰 흐름 진입 | 없음 |
| `interview_started` | 새 인터뷰 시작 | 없음 |
| `interview_history_opened` | 지난 인터뷰 진입 | 없음 |
| `interview_completed` | 인터뷰 완료 | 없음 |
| `story_creation_opened` | 동화 생성 설정 진입 | 없음 |
| `story_generation_requested` | 동화 생성 요청 | 없음 |
| `story_generation_retry_opened` | 실패 후 다시 만들기 진입 | 없음 |
| `bookshelf_opened` | 책장 진입 | 없음 |
| `story_opened` | 완성 동화 뷰어 진입 | 없음 |
| `narration_started` | 동화 읽어주기 시작 | 없음 |
| `reading_completed` | 읽기 완료 | 없음 |
| `print_preparation_opened` | 실물책 주문 준비 진입 | 없음 |
| `print_preview_requested` | 펼친 표지 미리보기 요청 | 없음 |
| `book_checkout_opened` | 주문서 진입 | 없음 |
| `payment_started` | 유효한 주문 정보로 결제 시작 | 없음 |
| `order_history_opened` | 주문 내역 진입 | 없음 |
| `order_detail_opened` | 주문 상세 진입 | 없음 |
| `order_cancellation_requested` | 확인 후 주문 취소 요청 | 없음 |
| `support_contact_opened` | 주문 고객지원 문의 시작 | 없음 |

금지 항목은 아이·보호자 이름, 이메일·전화번호, 회원/프로필/인터뷰/동화 ID, 사진·음성,
질문·답변·동화·프롬프트 원문, 파일 URL, 광고 ID, 연령·성별·관심사·위치, 자유 형식 오류다.

## 공개 정책 발행 전 확인

| 항목 | 현재 상태 | 출시 조건 |
|---|---|---|
| 처리 목적 | 확정 | 제품 사용성·안정성 개선으로 한정 |
| 처리 항목 | 일부 확정 | 위 allowlist 이벤트와 Firebase 기본 이벤트·기기/앱 기본 정보의 실제 DebugView 결과로 확정 |
| 법적 근거 | 구현 확정 | 보호자 선택 동의 전 수집 중지 |
| 처리자·수탁자 | 후보 확인 | Google/Firebase의 실제 계약 주체 명칭 확인 |
| 국외 이전 국가·시점·방법 | 미확정 | Firebase 계약·데이터 위치 문서로 검증 후 기재 |
| 보유 기간 | 미확정 | GA4 property의 실제 data retention 값 확인 후 기재 |
| 파기·철회 효과 | 구현 확정/문구 검토 필요 | 새 수집 중단과 기존 Google 보관 데이터 처리 범위를 구분해 고지 |
| 문의·권리 행사 | 기존 정책과 연결 필요 | 개인정보처리방침의 담당자·연락처 확정 |

미확정 값을 추측해 공개 문서에 쓰지 않는다. 값이 확정되면 새 version 경로에 새 HTML을
추가하고 `policies/manifest.json`과 `policies/SHA256SUMS`를 함께 갱신한다.

## 콘솔·스토어 출시 체크리스트

2026-09-16 `fetfdsf5@gmail.com` 계정에 Firebase·GA4 운영 프로젝트를 새로 만들었다.
프로젝트 표시 이름은 `Bookkiki Prod`, 프로젝트 ID는 `bookkiki-prod-cbff3`이며,
Analytics 위치는 대한민국이다. iOS·Android 모두 운영 앱 식별자 `com.bookkiki.app`으로
등록했고 production 앱 설정도 이 프로젝트를 가리킨다. Spark 요금제를 유지하며 Gemini,
Google 제품 데이터 공유, 벤치마킹, 기술 지원, 계정 전문가 데이터 공유는 모두 껐다.
광고 상품과 Google Play 연결도 하지 않았다.

- [x] GA4 dev/prod 프로젝트와 앱 stream을 분리한다.
- [x] Google Signals, ads personalization, remarketing, 광고 계정 연결을 사용하지 않는다.
- [ ] GA4 data retention 값을 확정하고 화면 증거를 보존한다.
- [x] Firebase/GA4 관리자 계정은 운영 계정 1개로 시작한다. 팀 초대 시 최소 권한을 다시 점검한다.
- [ ] iOS App Privacy에 실제 수집 항목·목적·추적 여부를 그대로 신고한다.
- [ ] Google Play Data safety와 Target audience/Families 답변을 실제 SDK 동작과 일치시킨다.
- [ ] Android release manifest에 `AD_ID` 권한이 합쳐지지 않았는지 검사한다.
- [ ] iOS binary에 AdSupport/ATT 의존이 추가되지 않았는지 검사한다.
- [ ] 동의 OFF 실기기에서 DebugView 이벤트가 0건인지 확인한다.
- [ ] 동의 ON 실기기에서 allowlist 사용자 정의 이벤트와 고지한 Firebase 기본 이벤트만 보이는지 확인한다.
- [ ] 사진·음성·인터뷰 원문·식별자·URL이 이벤트와 user property에 없는지 확인한다.
- [ ] 철회 뒤 새 이벤트가 더 이상 수집되지 않는지 확인한다.

## 운영 대시보드

- 실시간 설치 확인: GA4 `Reports > Realtime`
- 개발 기기 검증: GA4 `Admin > Data display > DebugView`
- 앱 종합 지표: GA4 `Reports > App developer > Firebase overview`
- 이벤트별 횟수·사용자: GA4 `Reports > Engagement > Events`
- 가입 이후 핵심 흐름: GA4 `Explore > Funnel exploration`에서
  `child_profile_created → interview_completed → story_generation_requested → story_opened`
- 실물책 구매 의향 흐름: `print_preparation_opened → book_checkout_opened → payment_started`

`child_profile_created`, `interview_completed`, `story_generation_requested`, `story_opened`,
`payment_started`는 운영 합의 후 GA4의 key event 후보로 등록한다. `payment_started`는 결제
성공이 아니므로 매출 지표로 사용하지 않는다. 실제 결제 성공·환불·배송 완료는 서버의
멱등 lifecycle 이벤트 계약을 추가하기 전까지 주문 DB를 원천으로 본다.

## 근거 문서

- Firebase Analytics Android data collection:
  <https://firebase.google.com/docs/analytics/android/configure-data-collection>
- Firebase Analytics Apple data collection:
  <https://firebase.google.com/docs/analytics/ios/configure-data-collection>
- Firebase screenview collection:
  <https://firebase.google.com/docs/analytics/screenviews>
- Google Play Families policy:
  <https://support.google.com/googleplay/android-developer/answer/9893335>
