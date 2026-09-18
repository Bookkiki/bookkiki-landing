# BK-892 소셜 로그인 4종 약관 개정 (2026-09-18 판)

## 배경

- 2026-09-03 이용약관·개인정보 수집·이용 동의서는 `Google OAuth`만 안내한다. 운영 API Server는 Google·Kakao·Naver·Apple 로그인을 모두 켜고 있어(`GOOGLE_OAUTH_ENABLED`·`KAKAO_OAUTH_ENABLED`·`NAVER_OAUTH_ENABLED`·`APPLE_OAUTH_ENABLED`) 공개 문서와 실제 로그인 방식이 달랐다.
- 2026-09-17-1 개인정보처리방침은 로그인 제공자를 "소셜 로그인 제공자"로만 적고, 앱 사용 분석 동의의 시작점을 설정 화면으로만 안내했다. 앱은 가입 약관 화면에도 `앱 사용 분석 동의 (선택)`을 보여 준다.
- 기존 version의 원문·SHA-256·manifest 항목은 바꾸지 않는다. `aliases`만 옮긴다.

## 코드 기준 처리 항목

Server `OAuthIdentity`는 로그인 제공자, 제공자 회원 식별자(subject), 제공자가 제공한 이메일(정규화)만 저장한다. 비밀번호·이름·프로필 사진과 인증 Token 원문은 검증 후 저장하지 않는다.

| 제공자 | 로그인 증거 | 저장하는 OAuth 신원 정보 | 저장하지 않는 정보 |
| --- | --- | --- | --- |
| Google | ID Token | 제공자, 제공자 회원 식별자, 제공된 이메일(email_verified인 경우) | ID Token 원문, 비밀번호, 이름, 프로필 사진 |
| Kakao | OIDC ID Token | 제공자, 제공자 회원 식별자, 제공된 이메일 | ID Token 원문, 비밀번호, 이름, 프로필 사진 |
| Naver | Access Token으로 사용자 정보 API 조회 | 제공자, 제공자 회원 식별자, 제공된 이메일 | Access Token 원문, 비밀번호, 이름, 프로필 사진 |
| Apple | ID Token, 탈퇴 시 authorization code로 token revocation | 제공자, 제공자 회원 식별자, 제공된 이메일(email_verified인 경우) | ID Token·authorization code 원문, 비밀번호, 이름, 프로필 사진 |

로그인 제공자는 회원이 직접 인증하는 독립된 처리자이며 회사가 회원 정보 처리를 위탁하는 수탁자가 아니다. 개인정보처리방침 5항 위탁 표에는 넣지 않고 2항에 처리 방식을 고지한다.

## 발행 내용

| 문서 | version | 공고일 | 시행일 | alias |
| --- | --- | --- | --- | --- |
| 이용약관 `terms_of_service` | 2026-09-18 | 2026-09-18 | 2026-09-25 | 시행일에 `/ko-KR/policies/terms-of-use`를 옮긴다 |
| 개인정보 수집·이용 동의 `personal_information_collection_consent` | 2026-09-18 | 2026-09-18 | 2026-09-25 | 없음 |
| 개인정보처리방침 `privacy_policy` | 2026-09-18 | 2026-09-18 | 2026-09-18 | `/ko-KR/policies/privacy-policy`를 이 version으로 옮김 |

- 이용약관 제3조는 "적용일 7일 전부터 공지"를 정하므로 이용약관과 함께 가입 시 동의받는 수집·이용 동의서의 시행일을 공고일 7일 뒤로 둔다. 로그인 제공자를 추가하는 변경은 회원에게 불리하거나 중요한 내용의 변경(30일)으로 보지 않는다.
- 개인정보처리방침은 동의 checkbox가 아닌 고지 문서이므로 같은 날 시행한다.
- 이용약관·수집·이용 동의서는 2026-09-03 원문에서 소셜 로그인 문구만 치환한다(`scripts/build-bk-892-signup-terms-revision.py`). 회원 자격 등 다른 조항은 바꾸지 않는다.
- 개인정보처리방침은 `bookkiki-server` `docs/policies/legal-copy/privacy-policy.md`를 원본으로 `scripts/build-bk-892-privacy-revision.py`로 렌더링한다. 2026-09-17(Langfuse)·2026-09-17-1(Google Analytics) 고지는 그대로 남는다.

## 재현

```bash
python3 scripts/build-bk-892-signup-terms-revision.py \
  --version 2026-09-18 --announced-at 2026-09-18 --effective-at 2026-09-25
python3 scripts/build-bk-892-privacy-revision.py \
  ../bookkiki-server/docs/policies/legal-copy/privacy-policy.md
./scripts/check-policy-documents.sh
python3 scripts/check-policy-history.py origin/main
python3 scripts/check-policy-manifest.py
```

## 시행일(2026-09-25) 작업

0. Server 변경(V82 catalog 등록, `/v1/terms/required` 2026-09-18)은 **2026-09-25 이후에만 배포한다.** 동화책 주문 결제는 catalog에서 "현재 시행 중"(`effective_on <= 오늘`)인 원문 version만 동의로 받으므로, 시행일 전에 배포하면 앱이 `/terms/required`로 받은 2026-09-18로 결제를 요청하다가 거부된다.
1. Server 배포 직전에 dev SSM `/bookkiki/dev/api/TERMS_OF_SERVICE_URL`·`PERSONAL_INFORMATION_COLLECTION_CONSENT_URL`, prod SSM `/bookkiki/prod/api/terms-of-service-url`·`personal-information-collection-consent-url` 값을 `/2026-09-18` 경로로 바꾼다. Server는 시작 시 URL의 version과 `GetRequiredTermsService`의 version이 다르면 기동을 거부한다.
2. 이 저장소에서 [PR #21](https://github.com/Bookkiki/bookkiki-landing/pull/21)과 같은 방식으로 manifest의 `terms_of_service` 2026-09-03 `aliases`를 2026-09-18로 옮기고 `ko-KR/policies/terms-of-use/index.html`을 2026-09-18 원문 사본으로 바꾼다. 앱 설정의 이용약관 링크는 Server가 내려주는 version URL을 쓰므로 Server 배포와 같은 날 맞춘다.
3. 기존 회원 재동의: 이용약관 개정은 제3조 공지 절차를 따르며, 수집 항목의 실질 변경(제공된 이메일 저장 명시)은 이미 저장 중인 사실의 고지 정정이다. 기존 회원에게 앱에서 재동의를 강제하지 않고, 공고 후 계속 이용을 동의로 간주하지 않는다는 제3조 문구에 따라 회원이 개정 약관을 거부하면 탈퇴할 수 있음을 안내한다. 재동의 강제 여부는 외부 법률 검토 결과에 따라 별도 결정한다.
