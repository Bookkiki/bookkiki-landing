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

## 수집 허용 범위

| 이벤트 | 의미 | 허용 파라미터 |
|---|---|---|
| `settings_opened` | 설정 화면 진입 | 없음 |
| `child_profile_creation_opened` | 자녀 프로필 생성 흐름 진입 | 없음 |
| `interview_opened` | 인터뷰 흐름 진입 | 없음 |
| `story_creation_opened` | 동화 생성 설정 진입 | 없음 |
| `story_opened` | 완성 동화 뷰어 진입 | 없음 |

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

- [ ] GA4 dev/prod property 또는 stream을 분리한다.
- [ ] Google Signals, ads personalization, remarketing, 광고 계정 연결을 사용하지 않는다.
- [ ] GA4 data retention 값을 확정하고 화면 증거를 보존한다.
- [ ] Firebase/GA4 관리자 권한을 최소 인원으로 제한한다.
- [ ] iOS App Privacy에 실제 수집 항목·목적·추적 여부를 그대로 신고한다.
- [ ] Google Play Data safety와 Target audience/Families 답변을 실제 SDK 동작과 일치시킨다.
- [ ] Android release manifest에 `AD_ID` 권한이 합쳐지지 않았는지 검사한다.
- [ ] iOS binary에 AdSupport/ATT 의존이 추가되지 않았는지 검사한다.
- [ ] 동의 OFF 실기기에서 DebugView 이벤트가 0건인지 확인한다.
- [ ] 동의 ON 실기기에서 allowlist 사용자 정의 이벤트와 고지한 Firebase 기본 이벤트만 보이는지 확인한다.
- [ ] 사진·음성·인터뷰 원문·식별자·URL이 이벤트와 user property에 없는지 확인한다.
- [ ] 철회 뒤 새 이벤트가 더 이상 수집되지 않는지 확인한다.

## 근거 문서

- Firebase Analytics Android data collection:
  <https://firebase.google.com/docs/analytics/android/configure-data-collection>
- Firebase Analytics Apple data collection:
  <https://firebase.google.com/docs/analytics/ios/configure-data-collection>
- Firebase screenview collection:
  <https://firebase.google.com/docs/analytics/screenviews>
- Google Play Families policy:
  <https://support.google.com/googleplay/android-developer/answer/9893335>
