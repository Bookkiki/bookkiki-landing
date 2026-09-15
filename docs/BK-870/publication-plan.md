# BK-870 목적·업체별 동의 원문 발행 계획

상태: 초안. 이 파일과 아래 경로는 공개된 동의 URL이나 운영 동의 계약이 아니다.

법률 문안의 원본은 Server 저장소 `docs/policies/legal-copy/overseas-transfer-consent.md`, `privacy-policy.md`, `in-app-disclosures.md`에 있다. [Server BK-870 이슈](https://github.com/Bookkiki/bookkiki-server/issues/738)에서 실제 payload와 2026-09-15 ElevenLabs non-ZRM 운영 결정을 대조한다. landing의 [BK-870 발행 이슈](https://github.com/Bookkiki/bookkiki-landing/issues/6)는 확정된 원문을 불변 HTML·manifest·URL로 게시하는 단계다.

| 동의 단위 | 문서 code | version 고정 경로 안 |
| --- | --- | --- |
| OpenAI 사진 캐릭터 | `overseas_openai_photo_character_consent` | `/ko-KR/consents/overseas-transfer/overseas_openai_photo_character_consent/{version}` |
| Anthropic AI 인터뷰 | `overseas_anthropic_interview_consent` | `/ko-KR/consents/overseas-transfer/overseas_anthropic_interview_consent/{version}` |
| ElevenLabs STT | `overseas_elevenlabs_stt_consent` | `/ko-KR/consents/overseas-transfer/overseas_elevenlabs_stt_consent/{version}` |
| OpenAI 동화·삽화 | `overseas_openai_story_generation_consent` | `/ko-KR/consents/overseas-transfer/overseas_openai_story_generation_consent/{version}` |
| OpenRouter 추가 검수 | `overseas_openrouter_story_review_consent` | `/ko-KR/consents/overseas-transfer/overseas_openrouter_story_review_consent/{version}` |
| ElevenLabs 질문·동화 TTS | `overseas_elevenlabs_tts_consent` | `/ko-KR/consents/overseas-transfer/overseas_elevenlabs_tts_consent/{version}` |
| Apple·Google push | `overseas_push_notification_consent` | `/ko-KR/consents/overseas-transfer/overseas_push_notification_consent/{version}` |

이 일곱 code와 `/ko-KR/consents/overseas-transfer/{document-code}/{version}` 경로 규칙은 Server 법률 문안 초안의 README에 적혀 있다. Server 동의 API(BK-871)와 앱 시트(BK-872)가 회원·자녀·목적·수령자별로 동일한 code·version·SHA-256을 사용해야 한다. 한 HTML 페이지의 전체 동의 checkbox로 합치지 않는다.

## 게시 전 순서

1. 실제 공급자 계약·계정·운영 설정에서 연락처, 처리 국가, 보유기간, 조기 삭제 조건, OpenAI ZDR 및 OpenRouter 하위 provider를 확인한다. 초기 STT non-ZRM과 질문·동화 TTS의 서로 다른 logging 경로를 따로 검증한다.
2. 외부 법률 검토와 BK-876 출시 gate를 거쳐 공고일·시행일·원문을 확정한다. OpenRouter가 계속 비활성화되면 이를 출시 지원 기능처럼 고지하지 않는다.
3. 각 원문을 별도 version 고정 파일로 추가하고 `policies/manifest.json`에 code, version, locale, 날짜, SHA-256, sourcePath, publicPath를 등록한다. `2026-09-03` 기존 파일·hash는 변경하지 않는다.
4. 공개 URL·Server catalog/API·앱 WebView가 같은 원문과 hash를 가리키는지 인증 없이 검증한다. 그 전에는 최신 alias를 바꾸거나 운영 동의에 사용하지 않는다.

현재 manifest에는 2026-09-03 원문 네 개만 있으며 위 일곱 경로는 아직 존재하지 않는다.
