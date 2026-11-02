#!/usr/bin/env python3
"""Issue the 2026-11-02 privacy-policy revision for guest browsing and pre-consent guest analytics (BK-1515).

직전 공개판 2026-10-28의 bytes를 읽어, 정해 둔 문장만 바꿔 새 판을 만든다. 각 바꿀 문장은 원문에 정확히 한 번
있어야 하고, 없거나 두 번 이상이면 발행을 멈춘다. 2026-10-28 판의 bytes와 manifest 항목은 건드리지 않는다.

이번 판에 더하는 것(앱 bookkiki-client origin/dev, 서버 bookkiki-server origin/dev 기준):
- 가입 전 둘러보기(로그인 없이 홈·게시판·전래 동화 보기와 읽기, BK-1514·1515·1517): 접속 IP 해시 기반 요청 횟수 제한,
  기기에만 남는 읽은 책 목록
- 가입 전 둘러보기 이용 통계(동의 전 GA4 이벤트 10종, audience=guest)와 거부·중단 방법
- 회원 앱 사용 분석 이벤트 목록 갱신(기다리는 화면 이벤트 7종과 값, 게시판 같은 전래 동화로 만들기)
- 가입 직후 한 화면 동의(BK-1546): 항목별 응답 기록, 자녀 등록 전 동의의 적용 범위
- 말하는 도중 받아쓰기(ElevenLabs 실시간 변환, BK-1560): 같은 공급자, 회사 서버는 음성을 저장하지 않음
- 낭독 낱말 시각(회사 서버 계산), 사진 캐릭터 사진 1~3장, 기다리는 화면의 인스타그램 이동

공고일과 시행일이 다르다(시행 7일 전 공고). 무버전 주소는 시행일이 되기 전에는 옮기지 않으므로 이 스크립트는 새 판과
변경 안내만 만들고 manifest 항목의 aliases는 비워 둔다. 시행일에 별도 변경으로 무버전 주소를 이 판으로 옮긴다.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026-11-02"
ANNOUNCED = "2026-11-02"
EFFECTIVE = "2026-11-09"
PREVIOUS_VERSION = "2026-10-28"
POLICY_DIR = ROOT / "ko-KR" / "policies" / "privacy-policy"
SOURCE = POLICY_DIR / PREVIOUS_VERSION / "index.html"
TARGET = POLICY_DIR / VERSION / "index.html"
NOTICE_CODE = "privacy_policy_guest_browsing_notice"
NOTICE_ROUTE = f"/ko-KR/notices/privacy-policy-guest-browsing/{VERSION}"
NOTICE_TARGET = ROOT / NOTICE_ROUTE.lstrip("/") / "index.html"
POLICY_ROUTE = f"/ko-KR/policies/privacy-policy/{VERSION}"

GUEST_EVENTS_KO = (
    "둘러보기 홈 열기, 큰 그림 누르기(전래 동화 또는 게시판), 게시판·전래 동화 책장 둘러보기 열기(게시판 또는 전래 동화), "
    "게시판 책 열기, 전래 동화 고르기, 만들기 종류 누르기(인터뷰·전래 동화·일기), 가입 안내 띄움과 가입 안내에서 가입 시작"
    "(어떤 동작에서 띄웠는지), 둘러볼 수 있는 책 3권을 다 읽음, 게시판 읽기 화면에서 같은 전래 동화로 만들기 누르기의 10종"
)

REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (
        '<link rel="canonical" href="https://www.bookkiki.com/ko-KR/policies/privacy-policy/2026-10-28">',
        f'<link rel="canonical" href="https://www.bookkiki.com{POLICY_ROUTE}">',
    ),
    (
        "<li>공고일: <code>2026년 10월 28일</code></li>\n<li>시행일: <code>2026년 10월 28일</code></li>",
        "<li>공고일: <code>2026년 11월 2일</code></li>\n<li>시행일: <code>2026년 11월 9일</code></li>",
    ),
    # 1. 처리 목적
    (
        "<li>보호자가 선택 동의한 경우에 한한 앱 사용 분석과 사용성·안정성 개선</li>",
        "<li>보호자가 선택 동의한 경우에 한한 회원의 앱 사용 분석과 사용성·안정성 개선</li>\n"
        "<li>가입 전 둘러보기(로그인하지 않고 게시판·전래 동화 책 보기와 서로 다른 책 3권까지 읽기) 제공과 과도한 요청 방지</li>\n"
        "<li>가입 전 둘러보기 화면의 이용 통계(어떤 화면과 버튼이 쓰이는지)를 내어 첫 화면과 가입 안내 개선</li>",
    ),
    # 2. 처리 항목: 회원 다음에 동의 응답 행
    (
        "<td>Google·Kakao·Naver·Apple 로그인 제공자로부터 회원이 제공에 동의한 정보를 전달받는 회원가입과 확인 절차</td>\n</tr>",
        "<td>Google·Kakao·Naver·Apple 로그인 제공자로부터 회원이 제공에 동의한 정보를 전달받는 회원가입과 확인 절차</td>\n</tr>\n"
        "<tr>\n<td>동의 응답</td>\n"
        "<td>가입 직후 한 화면(또는 바뀐 항목이 있을 때 앱을 열 때)에서 받은 동의 항목별 응답(동의·거부), 그때 본 동의서 판, 응답 시각, 응답 경로(가입 직후 또는 앱을 열 때)</td>\n"
        "<td>보호자가 동의 화면에서 답하는 과정</td>\n</tr>",
    ),
    (
        "<td>자녀 얼굴 사진, 사진에서 생성한 실사풍 얼굴 이미지(이하 &quot;사진 기반 얼굴 이미지&quot;), 생성된 캐릭터 이미지</td>",
        "<td>자녀 얼굴 사진(한 번에 1~3장), 사진에서 생성한 실사풍 얼굴 이미지(이하 &quot;사진 기반 얼굴 이미지&quot;), 생성된 캐릭터 이미지</td>",
    ),
    (
        "<td>자녀 음성, 변환된 글, 질문·답변, 요약</td>\n<td>인터뷰 이용 과정</td>",
        "<td>자녀 음성, 변환된 글, 질문·답변, 요약</td>\n<td>인터뷰 이용 과정(말하는 도중 받아쓰기 포함)</td>",
    ),
    (
        "<td>동화를 만들 때의 자녀 프로필, 인터뷰 요약 또는 보호자가 고친 일기 글, 캐릭터, 동화 글, 삽화, 낭독 음성</td>",
        "<td>동화를 만들 때의 자녀 프로필, 인터뷰 요약 또는 보호자가 고친 일기 글, 캐릭터, 동화 글, 삽화, 낭독 음성, "
        "낭독 음성 속 낱말별 시작·끝 시각(읽는 낱말 표시용, 회사 서버에서 계산)</td>",
    ),
    (
        "<td>접속 시각, 앱·OS 버전, 기기 종류, 앱 설치 식별자, 알림 토큰, 이용·오류 기록</td>\n<td>앱 이용 과정</td>\n</tr>",
        "<td>접속 시각, 앱·OS 버전, 기기 종류, 앱 설치 식별자, 알림 토큰, 이용·오류 기록</td>\n<td>앱 이용 과정</td>\n</tr>\n"
        "<tr>\n<td>가입 전 둘러보기</td>\n"
        "<td>접속 IP(과도한 요청을 막기 위한 요청 횟수 제한에만 쓰며, 원문 대신 해시값으로 셈), 둘러보며 읽은 책 목록"
        "(기기에만 저장하고 회사로 보내지 않으며 로그인하면 지움). 이름·연락처·자녀 정보는 받지 않음</td>\n"
        "<td>로그인하지 않은 상태로 앱 첫 화면·게시판·전래 동화를 보거나 읽는 과정</td>\n</tr>",
    ),
    (
        "<td>기능 진입·버튼 행동 이벤트 이름과 일부 이벤트의 정해진 값(게시판 올리기 보상 여부, 인스타그램 공유 편 수·나누기 방법, "
        "실물책 선물 안내의 안내 모양·띄운 때·주문하지 않은 방법), Google Analytics 앱 설치 식별자",
        "<td>기능 진입·버튼 행동 이벤트 이름과 일부 이벤트의 정해진 값(게시판 올리기 보상 여부, 인스타그램 공유 편 수·나누기 방법, "
        "실물책 선물 안내의 안내 모양·띄운 때·주문하지 않은 방법, 동화·캐릭터 기다리는 화면의 화면 종류·영상 목록 식별자·영상 종류·순서·진행률), "
        "Google Analytics 앱 설치 식별자",
    ),
    (
        "<td>보호자가 가입 화면의 앱 사용 분석 동의(선택) 또는 설정에서 사용 분석에 동의한 뒤 앱 이용 과정</td>\n</tr>",
        "<td>보호자가 가입 화면의 앱 사용 분석 동의(선택) 또는 설정에서 사용 분석에 동의한 뒤 앱 이용 과정</td>\n</tr>\n"
        "<tr>\n<td>가입 전 둘러보기 이용 통계</td>\n"
        "<td>둘러보기 화면에서 연 화면과 누른 버튼의 이벤트 이름과 정해진 값(큰 그림 종류, 둘러본 화면 종류, 만들기 종류, "
        "가입 안내를 띄운 동작), 가입 전 이용임을 나타내는 표시, Google Analytics 앱 설치 식별자, 앱·OS 버전, 기기 종류, "
        "세션 시작·종료 시각, IP 주소로 산출한 대략적 지역(국가·도시). 이름·이메일·자녀 정보·게시물 식별자·책 제목·광고 식별자는 처리하지 않음</td>\n"
        "<td>로그인하지 않은 상태로 앱 첫 화면(가입 전 둘러보기)을 이용하는 과정. 별도 동의를 받지 않으며 거부·중단 방법은 8항과 10항에 적음</td>\n</tr>",
    ),
    (
        "<p>회사는 주민등록번호와 신분증 원본을 수집하지 않으며, 별도의 본인확인 업체를 이용하지 않습니다.</p>",
        "<p>동화·캐릭터를 기다리는 화면에는 북끼끼 인스타그램 게시물로 가는 버튼이 있습니다. 누르면 인스타그램 앱 또는 웹으로 이동하며, "
        "회사는 이때 인스타그램(Meta)에 회원·자녀 정보를 보내지 않습니다. 이동한 뒤의 처리는 Meta의 개인정보처리방침을 따릅니다.</p>\n"
        "<p>회사는 주민등록번호와 신분증 원본을 수집하지 않으며, 별도의 본인확인 업체를 이용하지 않습니다.</p>",
    ),
    # 3. 보유기간
    (
        "<td>Google Analytics의 이용자·이벤트 단위 데이터는 회사가 설정한 보관기간(최대 14개월) 경과 시 자동 삭제. "
        "동의를 끄면 새 수집을 중단하고 기기의 분석 식별자를 초기화하며, 개인을 식별할 수 없는 집계 통계는 보관 설정과 무관하게 남을 수 있음</td>\n</tr>",
        "<td>Google Analytics의 이용자·이벤트 단위 데이터는 회사가 설정한 보관기간(최대 14개월) 경과 시 자동 삭제. "
        "가입 전 둘러보기 이용 통계도 같음. 동의를 끄거나 가입할 때 앱 사용 분석에 동의하지 않으면 새 수집을 중단하고 기기의 분석 식별자를 초기화하며, "
        "개인을 식별할 수 없는 집계 통계는 보관 설정과 무관하게 남을 수 있음</td>\n</tr>\n"
        "<tr>\n<td>가입 전 둘러보기 요청 횟수 기록</td>\n"
        "<td>접속 IP의 해시값별 요청 횟수는 제한 구간(1분·1시간)이 끝나면 자동 삭제. 둘러보며 읽은 책 목록은 기기에만 있고 로그인하거나 앱을 삭제하면 지워짐</td>\n</tr>\n"
        "<tr>\n<td>동의 응답 기록</td>\n"
        "<td>이 응답 기록은 계정 탈퇴 시 함께 삭제. 동의한 사실의 최소 증빙은 이와 별도로 아래 약관·법정대리인 동의 증빙 기준(탈퇴·철회 후 5년)에 따라 보관</td>\n</tr>",
    ),
    (
        "<td>회사 서버에 영구 저장하지 않음. 임시 저장 시 처리 종료 또는 업로드 후 24시간 중 빠른 때 삭제</td>",
        "<td>회사 서버에 영구 저장하지 않음. 임시 저장 시 처리 종료 또는 업로드 후 24시간 중 빠른 때 삭제. "
        "말하는 도중 받아쓰기의 음성은 변환하는 동안 서버 메모리에서만 다루고 파일로 저장하지 않으며 변환이 끝나면 버림</td>",
    ),
    # 4. 아동
    (
        "<li>자녀 얼굴 사진과 사진 기반 얼굴 이미지는 법정대리인이 사진 캐릭터 생성의 개인정보 수집·이용과 국외 이전에 각각 동의한 경우에만 만듭니다.</li>\n</ol>",
        "<li>자녀 얼굴 사진과 사진 기반 얼굴 이미지는 법정대리인이 사진 캐릭터 생성의 개인정보 수집·이용과 국외 이전에 각각 동의한 경우에만 만듭니다.</li>\n"
        "<li>가입 직후 한 화면에서 받은 자녀 관련 선택 동의(AI 기능 등)는 자녀를 아직 등록하지 않았더라도 그 계정에 등록된 자녀와 앞으로 등록하는 자녀 모두에게 적용됩니다. "
        "법정대리인은 설정 &gt; AI 처리·알림 동의에서 자녀별로 철회할 수 있습니다.</li>\n"
        "<li>가입하지 않고 둘러보는 동안에는 자녀의 이름·나이·사진·음성 등 자녀 정보를 받지 않습니다.</li>\n</ol>",
    ),
    # 5. 위탁
    (
        "<td>앱 사용 분석(Google Analytics for Firebase). 보호자가 동의한 경우에만</td>\n"
        "<td>기능 진입·버튼 행동 이벤트 이름과 일부 이벤트의 정해진 값, Google Analytics 앱 설치 식별자, 앱·OS 버전, 기기 종류, 세션 시각, 대략적 지역</td>",
        "<td>앱 사용 분석(Google Analytics for Firebase). 회원은 보호자가 동의한 경우에만, 가입 전 둘러보기 화면에서는 2항의 가입 전 둘러보기 이용 통계만</td>\n"
        "<td>기능 진입·버튼 행동 이벤트 이름과 일부 이벤트의 정해진 값, 가입 전 이용 표시, Google Analytics 앱 설치 식별자, 앱·OS 버전, 기기 종류, 세션 시각, 대략적 지역</td>",
    ),
    # 6. 국외 이전: 앱 사용 분석 문단
    (
        "<p>앱 사용 분석은 보호자가 가입 화면 또는 설정에서 동의한 경우에만 Google LLC(",
        "<p>앱 사용 분석은 회원은 보호자가 가입 화면 또는 설정에서 동의한 경우에만, 가입 전에는 둘러보기 화면의 이용 통계에 한해 Google LLC(",
    ),
    (
        "이전 항목은 2항 표의 앱 사용 분석(선택) 항목, 목적은 앱 사용성·안정성 개선, 시점·방법은 동의 후 앱 이용 중 암호화 전송, 보유기간은 3항과 같습니다. "
        "이전을 원하지 않으면 사용 분석에 동의하지 않거나 설정에서 끄면 되고, 거부해도 회원·인터뷰·동화 만들기 등 다른 기능은 제한되지 않습니다.</p>",
        "이전 항목은 2항 표의 앱 사용 분석(선택)과 가입 전 둘러보기 이용 통계 항목, 목적은 앱 사용성·안정성 개선과 첫 화면·가입 안내 개선, "
        "시점·방법은 가입 전 둘러보기 이용 중 또는 동의 후 앱 이용 중 암호화 전송, 보유기간은 3항과 같습니다. "
        "회원은 가입할 때 사용 분석에 동의하지 않거나 설정에서 끄면 이전되지 않습니다. 가입 전 둘러보기 중에는 앱 안에서 따로 끌 수 없으며, "
        "가입할 때 동의하지 않거나 동의 없이 로그인하면 멈춥니다(8항). 사용 분석에 동의하지 않아도 회원·인터뷰·동화 만들기 등 다른 기능은 제한되지 않습니다.</p>",
    ),
    # 6. 국외 이전: 말하는 도중 받아쓰기
    (
        "<p>회사는 ElevenLabs 음성 기능을 요청 이력이 남는 방식으로 이용합니다.",
        "<p>인터뷰 음성 답변 변환은 보호자가 음성 답변 변환의 개인정보 수집·이용과 ElevenLabs 국외 이전에 동의한 경우에만 Eleven Labs Inc.(legal@elevenlabs.io)에 맡깁니다. "
        "말하는 도중 받아쓰기를 제공할 때에는 아이가 말하는 동안 화면에 글을 미리 보여 주기 위해 녹음 중인 음성을 회사 서버를 거쳐 ElevenLabs에 실시간으로 암호화 전송하고, "
        "녹음을 마치면 답변으로 쓸 최종 글을 만들기 위해 같은 음성을 한 번 더 보냅니다. 받는 자·국가·이전 항목(자녀 음성, 변환된 글)과 공급자 보관 조건은 "
        "ElevenLabs 음성 답변 변환 국외 이전 동의서와 아래 ElevenLabs 이용 방식과 같습니다. 회사 서버는 이 음성을 저장하지 않고 변환하는 동안에만 메모리에서 처리하며, "
        "말하는 동안 보이는 미리보기 글도 저장하지 않습니다. 원하지 않으면 음성 대신 글로 답할 수 있습니다.</p>\n"
        "<p>회사는 ElevenLabs 음성 기능을 요청 이력이 남는 방식으로 이용합니다.",
    ),
    # 8. 권리: 가입 전 둘러보기 통계 중단
    (
        "광고성 정보 수신은 설정 &gt; 광고성 정보 수신에서 언제든 끌 수 있습니다.</li>\n</ul>",
        "광고성 정보 수신은 설정 &gt; 광고성 정보 수신에서 언제든 끌 수 있습니다.</li>\n"
        "<li>가입 전 둘러보기 이용 통계는 가입 화면의 앱 사용 분석 동의(선택)에서 동의하지 않거나 동의 없이 로그인하면 바로 멈추고, 기기의 분석 자료와 분석 식별자를 초기화합니다. "
        "가입하지 않고 둘러보는 동안에는 앱 안에서 따로 끄는 메뉴가 없으며, 앱을 삭제하면 기기의 분석 식별자도 함께 지워집니다. "
        "이미 보낸 이용 통계의 삭제는 <code>contact@bookkiki.com</code>으로 요청할 수 있습니다.</li>\n</ul>",
    ),
    # 10. 자동 수집: 회원 앱 사용 분석은 동의 후에만이라는 문장의 범위를 회원으로 좁힌다(가입 전 이용 통계는 아래 새 문단).
    (
        "<p>앱 사용 분석에는 Google Analytics for Firebase를 사용합니다. 수집은 기본으로 꺼져 있고 보호자가",
        "<p>앱 사용 분석에는 Google Analytics for Firebase를 사용합니다. 회원의 앱 사용 분석 수집은 기본으로 꺼져 있고(가입 전 둘러보기 이용 통계는 아래 문단) 보호자가",
    ),
    # 10. 자동 수집: 회원 앱 사용 분석 이벤트 목록
    (
        "회사가 직접 기록하는 것은 회원가입·설정·문의·프로필 관리·캐릭터 만들기·인터뷰·동화 만들기·책장·낭독·단어 뜻 보기·실물책 주문·실물책 선물 안내·게시판·인스타그램 공유 화면의 진입과 버튼 행동을 뜻하는 이벤트 이름 43종입니다.",
        "회사가 직접 기록하는 것은 회원가입·설정·문의·프로필 관리·캐릭터 만들기·인터뷰·동화 만들기·동화·캐릭터 기다리는 화면·책장·낭독·단어 뜻 보기·실물책 주문·실물책 선물 안내·게시판·인스타그램 공유 화면의 진입과 버튼 행동을 뜻하는 이벤트 이름 53종입니다.",
    ),
    (
        "띄운 때(동화 완성 직후 또는 동화 마지막 쪽)와 주문하지 않은 방법(거절 또는 닫기)을 붙이며, 그 밖의 이벤트에는 다른 정보를 붙이지 않습니다.",
        "띄운 때(동화 완성 직후 또는 동화 마지막 쪽)와 주문하지 않은 방법(거절 또는 닫기)을, 기다리는 화면 이벤트에는 화면 종류(동화 또는 캐릭터), "
        "회사가 정한 영상 목록 식별자와 영상 종류, 몇 번째 영상인지와 진행률을 붙이며, 그 밖의 이벤트에는 다른 정보를 붙이지 않습니다.",
    ),
    # 10. 자동 수집: 가입 전 둘러보기 이용 통계
    (
        "<p>웹사이트(bookkiki.com)에서는 방문·버튼 클릭 통계를 위해 Google Analytics를 사용합니다.",
        "<p>로그인하지 않은 상태로 앱 첫 화면(가입 전 둘러보기)을 이용하면, 첫 화면과 가입 안내를 개선하기 위해 별도 동의 없이 "
        f"Google Analytics for Firebase로 다음 이벤트를 보냅니다: {GUEST_EVENTS_KO}. 모든 이벤트에 가입 전 이용임을 나타내는 표시를 붙입니다. "
        "이때 Google Analytics가 앱 설치 식별자, 앱·OS 버전, 기기 종류, 첫 실행·세션 시작 같은 기본 이벤트와 IP 주소로 산출한 대략적 지역을 함께 처리합니다. "
        "책 식별자·제목, 이름·이메일, 자녀 정보와 광고 식별자는 보내지 않고, 자동 화면 추적·광고 식별자·회원 식별자 연결·개인 맞춤 광고를 쓰지 않는 것은 위와 같습니다. "
        "가입할 때 앱 사용 분석 동의(선택)에 동의하면 회원의 앱 사용 분석으로 이어지고, 동의하지 않거나 동의 없이 로그인하면 바로 수집을 끄고 기기의 분석 자료와 "
        "앱 설치 식별자를 초기화합니다. 이 통계는 회원 계정과 연결하지 않으며, 이미 보낸 자료는 3항의 보관기간이 지나면 자동 삭제됩니다.</p>\n"
        "<p>웹사이트(bookkiki.com)에서는 방문·버튼 클릭 통계를 위해 Google Analytics를 사용합니다.",
    ),
    # 14. 변경
    (
        "<p>이번 개정(2026년 10월 28일 공고)은 동화 낭독의 문맥 연출에 OpenAI를 추가하고, 글·삽화 완성 후 음성을 자동 준비하는 처리를 알립니다. "
        "직전 판은 <a href=\"/ko-KR/policies/privacy-policy/2026-10-27-1\">2026-10-27-1 판</a>입니다.</p>\n"
        "<ul><li>동화 낭독 전용 동의서에 두 공급자의 처리 항목·목적·보관 조건을 분리했습니다.</li>"
        "<li>기존 질문·동화 낭독 동의로 새 전송을 허용하지 않고, 보호자가 새 동의서를 확인하고 동의한 후 처리합니다.</li></ul>\n"
        "<p><a href=\"/ko-KR/notices/story-narration-direction/2026-10-28\">동화 낭독 변경 안내</a></p>",
        "<p>이번 개정(2026년 11월 2일 공고, 2026년 11월 9일 시행)은 로그인하지 않고 앱을 둘러보는 기능과 그 이용 통계, 가입 직후 한 화면 동의, "
        "말하는 도중 받아쓰기를 알립니다. 직전 판은 <a href=\"/ko-KR/policies/privacy-policy/2026-10-28\">2026-10-28 판</a>입니다.</p>\n"
        "<ul>"
        "<li>가입 전 둘러보기: 처리 목적·항목·보유기간에 요청 횟수 제한용 접속 IP(해시값)와 기기에만 남는 읽은 책 목록을 더했습니다.</li>"
        "<li>가입 전 둘러보기 이용 통계: 로그인 전 첫 화면의 이벤트 10종을 동의 없이 Google Analytics for Firebase로 보내는 것과 그 항목·보유기간·위탁·국외 이전·중단 방법을 더했습니다(1·2·3·5·6·8·10항).</li>"
        "<li>회원 앱 사용 분석: 기다리는 화면 이벤트와 그 값을 더해 이벤트 목록을 53종으로 고쳤습니다. 동의한 경우에만 수집하는 것은 그대로입니다.</li>"
        "<li>가입 직후 한 화면 동의: 항목별 응답 기록과 보유기간, 자녀 등록 전에 받은 동의가 계정의 모든 자녀에게 적용되는 것을 적었습니다(2·3·4항).</li>"
        "<li>말하는 도중 받아쓰기: 같은 공급자(ElevenLabs)에게 녹음 중 음성을 실시간으로 보내고 회사 서버는 음성을 저장하지 않는 것을 적었습니다(6항).</li>"
        "<li>그 밖에 사진 캐릭터 사진 1~3장, 낭독 낱말 시각(회사 서버 계산), 기다리는 화면의 인스타그램 이동을 적었습니다. 새 처리 위탁·국외 이전 업체는 없습니다.</li>"
        "</ul>\n"
        f"<p><a href=\"{NOTICE_ROUTE}\">개인정보처리방침 변경 안내</a></p>",
    ),
)

NOTICE_HTML = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="canonical" href="https://www.bookkiki.com{NOTICE_ROUTE}">
  <title>개인정보처리방침 변경 안내 | Bookkiki</title>
  <style>
    :root {{ color-scheme: light; font-family: system-ui, -apple-system, sans-serif; color: #353744; background: #f8f9fc; }}
    body {{ margin: 0; }}
    header, main, footer {{ max-width: 900px; margin: auto; padding: 24px; }}
    header a {{ color: #353744; text-decoration: none; font-weight: 700; }}
    main {{ background: white; border: 1px solid #d9dbe2; border-radius: 16px; margin-top: 16px; margin-bottom: 24px; }}
    h1 {{ line-height: 1.3; }} h2 {{ margin-top: 32px; }} p, li {{ line-height: 1.8; }}
    .table-scroll {{ overflow-x: auto; }} table {{ border-collapse: collapse; min-width: 720px; width: 100%; }}
    th, td {{ border: 1px solid #d9dbe2; padding: 12px; text-align: left; vertical-align: top; line-height: 1.6; }}
    th {{ background: #f2f3f7; }} code {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body>
  <header><a href="/">Bookkiki</a></header>
  <main>
<h1>개인정보처리방침 변경 안내</h1>
<p>공고일: 2026년 11월 2일 · 시행일: 2026년 11월 9일</p>
<p>로그인하지 않고도 앱을 둘러보고 책을 읽을 수 있게 되면서 개인정보처리방침을 고칩니다. 새로 쓰는 처리 위탁·국외 이전 업체는 없습니다.</p>
<h2>무엇이 바뀌나요</h2>
<div class="table-scroll"><table>
<thead><tr><th scope="col">항목</th><th scope="col">변경 전</th><th scope="col">변경 후</th></tr></thead>
<tbody>
<tr><td>가입 전 둘러보기</td><td>로그인해야 앱을 쓸 수 있었습니다.</td><td>로그인하지 않고 홈·게시판·전래 동화를 보고 서로 다른 책을 3권까지 읽을 수 있습니다. 과도한 요청을 막기 위해 접속 IP를 해시값으로 바꿔 요청 횟수만 세고, 제한 구간(1분·1시간)이 끝나면 자동으로 지웁니다. 읽은 책 목록은 기기에만 남습니다.</td></tr>
<tr><td>가입 전 이용 통계</td><td>앱 사용 분석은 보호자가 동의한 경우에만 했습니다.</td><td>로그인 전 첫 화면에서 어떤 화면과 버튼이 쓰이는지(이벤트 10종)를 동의 없이 Google Analytics for Firebase로 보냅니다. 이름·자녀 정보·책 제목·광고 식별자는 보내지 않습니다. 가입할 때 앱 사용 분석에 동의하지 않거나 동의 없이 로그인하면 바로 멈추고 기기의 분석 식별자를 초기화합니다. 회원의 앱 사용 분석은 지금처럼 동의한 경우에만 합니다.</td></tr>
<tr><td>가입 동의</td><td>기능을 처음 쓸 때마다 동의 창이 떴습니다.</td><td>가입 직후 한 화면에서 한 번에 동의하고, 항목별 응답(동의·거부) 기록을 탈퇴할 때까지 보관합니다. 자녀를 등록하기 전에 받은 동의는 계정의 모든 자녀에게 적용되며 자녀별로 철회할 수 있습니다.</td></tr>
<tr><td>말하는 도중 받아쓰기</td><td>녹음을 마친 뒤 음성을 보내 글로 바꿨습니다.</td><td>말하는 동안 글을 미리 보여 주기 위해 녹음 중인 음성을 같은 업체(ElevenLabs)에 실시간으로 보내고, 녹음을 마치면 최종 글을 만들기 위해 같은 음성을 한 번 더 보냅니다. 회사 서버는 이 음성을 파일로 저장하지 않습니다.</td></tr>
<tr><td>그 밖</td><td>-</td><td>사진 캐릭터 사진 1~3장, 낭독 낱말 시각(회사 서버에서 계산), 기다리는 화면의 인스타그램 이동(회원·자녀 정보는 보내지 않음), 회원 앱 사용 분석 이벤트 목록(53종)을 적었습니다.</td></tr>
</tbody></table></div>
<p>이번 방침 개정 때문에 다시 동의해야 하는 항목은 없습니다. 문의: <code>contact@bookkiki.com</code></p>
<ul><li><a href="{POLICY_ROUTE}">개정 개인정보처리방침(2026-11-02 판, 2026년 11월 9일 시행)</a></li><li><a href="/ko-KR/policies/privacy-policy/{PREVIOUS_VERSION}">현재 개인정보처리방침(2026-10-28 판)</a></li></ul>
  </main>
</body>
</html>
"""


def build_policy() -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    for old, new in REPLACEMENTS:
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"expected exactly one match, found {count}: {old[:80]!r}")
        text = text.replace(old, new)
    if "43종" in text or "2026년 10월 28일</code>" in text:
        raise SystemExit("stale wording remains")
    return text.encode("utf-8")


def manifest_entry(code: str, path: Path, route: str, effective: str) -> dict:
    return {
        "termsCode": code,
        "version": VERSION,
        "locale": "ko-KR",
        "announcedAt": ANNOUNCED,
        "effectiveAt": effective,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "sourcePath": path.relative_to(ROOT).as_posix(),
        "publicPath": route,
        "aliases": [],
    }


def main() -> int:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(build_policy())
    NOTICE_TARGET.parent.mkdir(parents=True, exist_ok=True)
    NOTICE_TARGET.write_bytes(NOTICE_HTML.encode("utf-8"))

    manifest_path = ROOT / "policies" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = [
        manifest_entry("privacy_policy", TARGET, POLICY_ROUTE, EFFECTIVE),
        # 변경 안내는 공고와 함께 바로 게시한다.
        manifest_entry(NOTICE_CODE, NOTICE_TARGET, NOTICE_ROUTE, ANNOUNCED),
    ]
    existing = {(d["termsCode"], d["version"], d["locale"]) for d in manifest["documents"]}
    for entry in entries:
        if (entry["termsCode"], entry["version"], entry["locale"]) in existing:
            raise SystemExit(f"version already issued: {entry['termsCode']} {VERSION}")
        manifest["documents"].append(entry)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sums_path = ROOT / "policies" / "SHA256SUMS"
    sums = sums_path.read_text(encoding="utf-8")
    if not sums.endswith("\n"):
        sums += "\n"
    for entry in entries:
        sums += f"{entry['sha256']}  {entry['sourcePath']}\n"
    sums_path.write_text(sums, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
