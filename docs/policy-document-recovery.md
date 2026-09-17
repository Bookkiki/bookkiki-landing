# 약관 원문 검증·복구 절차

## 원본 식별

`policies/manifest.json`의 `(termsCode, version, locale)`가 문서 버전을 식별한다. 동의
증빙의 `document_sha256`은 같은 항목의 `sha256`과 일치해야 한다. `sourcePath`의 파일이
복구 기준 원본이며 `publicPath`와 `aliases`는 GitHub Pages에서 제공하는 경로다.
`aliases`는 현재 버전을 가리키는 라우팅이므로 새 version을 발행할 때 옮길 수 있고(alias 파일은
해당 version 원문의 복사본이어야 한다), 나머지 필드와 원문은 불변이다.

## 정기 검증

`Policy documents` workflow가 매일 manifest, 저장소 원문, 공개 URL을 대조한다. 로컬에서는
다음 명령을 사용한다.

```bash
./scripts/check-policy-documents.sh
./scripts/check-policy-documents.sh https://www.bookkiki.com
```

PR에서는 base branch에 이미 존재하는 manifest 항목과 원문을 수정하거나 삭제하면
`check-policy-history.py`가 실패한다. 개정 문서는 새 version의 파일과 manifest 항목으로
추가한다.

## 공개 URL 장애 복구

1. 장애 URL의 `(termsCode, version, locale)`를 server 동의 증빙에서 확인한다.
2. manifest에서 같은 항목을 찾아 `sourcePath`와 `sha256`을 확인한다.
3. `./scripts/check-policy-documents.sh`로 저장소 원문의 해시를 검증한다.
4. GitHub Pages의 source가 `main` `/ (root)`, custom domain이 `bookkiki.com`인지 확인한다.
5. 저장소 원본과 manifest가 정상이면 Pages를 재배포한다. 원본이 없으면 git backup에서
   해당 commit을 복구하되 기존 version의 내용을 변경하지 않는다.
6. 공개 URL 검증 명령으로 모든 version 경로와 alias가 원문과 일치하는지 확인한다.

DB backup·restore와 탈퇴 후 증빙의 보관·파기는 BK-869에서 확정한 정책과 절차를 따른다.
