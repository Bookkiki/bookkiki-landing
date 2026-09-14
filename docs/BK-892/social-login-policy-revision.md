# BK-892 소셜 로그인 약관 개정안

## 상태

- Google, Kakao, Naver 로그인은 출시 가능한 구현 상태다.
- Apple 로그인은 BK-857 완료 전이므로 이 개정안을 아직 공개하지 않는다.
- 기존 `2026-09-03` 문서와 SHA-256은 변경하지 않는다.
- 공고일·시행일이 정해지고 BK-857이 Done이 되면 새 버전으로 발행한다.

## 코드 기준 처리 항목

| 제공자 | 로그인 증거 | 저장하는 OAuth 신원 정보 | 저장하지 않는 정보 |
| --- | --- | --- | --- |
| Google | ID Token | 제공자, 제공자 회원 식별자, 제공되고 검증된 이메일 | ID Token 원문, 비밀번호, 이름, 프로필 사진 |
| Kakao | ID Token | 제공자, 제공자 회원 식별자, 제공된 이메일 | ID Token 원문, 비밀번호, 이름, 프로필 사진 |
| Naver | Access Token으로 사용자 정보 API 조회 | 제공자, 제공자 회원 식별자, 제공된 이메일 | Access Token 원문, 비밀번호, 이름, 프로필 사진 |
| Apple | ID Token, 탈퇴 시 authorization code | 제공자, 제공자 회원 식별자, 최초 제공 이메일 | ID Token·authorization code 원문, 비밀번호, 이름, 프로필 사진 |

Apple 항목은 BK-857의 구현 계약이며, BK-857 완료 후 실제 코드와 다시 대조한다.

## 개정 범위

### 이용약관

- 서비스 이용 안내의 `Google OAuth`를 `Google·Kakao·Naver·Apple 소셜 로그인`으로 바꾼다.
- 제6조의 계정·비밀번호·인증정보 안내를 특정 제공자 하나가 아닌 로그인 제공자 전체에 적용한다.

### 개인정보 수집·이용 동의

- 수집·이용 목적에 Google·Kakao·Naver·Apple 소셜 로그인을 명시한다.
- 수집 항목을 로그인 제공자, 제공자 회원 식별자, 제공되고 확인된 이메일로 정정한다.
- 이름·프로필 사진과 인증 Token 원문은 저장하지 않는다고 명시한다.

### 개인정보처리방침

- 회원가입·로그인 처리 항목과 수집 방법에 네 제공자를 명시한다.
- 소셜 로그인 인증 수탁자와 인증 과정에서 처리하는 항목을 네 제공자 기준으로 정정한다.
- 인증 Token 원문은 검증 후 저장하지 않는다고 명시한다.

## 발행 절차

공고일·시행일이 정해지고 BK-857이 Done이면 다음 명령으로 새 버전을 만든다.

```bash
python3 scripts/publish-bk892-policy-version.py \
  --version YYYY-MM-DD \
  --announced-at YYYY-MM-DD \
  --effective-at YYYY-MM-DD \
  --confirm-apple-ready
./scripts/check-policy-documents.sh
python3 scripts/check-policy-history.py origin/main
```

발행 도구는 새 버전 HTML 세 개를 만들고, manifest와 SHA-256을 갱신하며, 이용약관과 개인정보처리방침의 최신 문서 경로를 새 버전으로 전환한다.

