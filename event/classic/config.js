/*
 * 이벤트 페이지 연결 정보 — 이 파일 한 곳만 고치면 페이지 전체에 반영돼요.
 * formUrl 이 비어 있으면 참여 버튼은 비활성 상태로 보여요(누를 수 없음). 배포 전에 꼭 채워 주세요.
 * operator 항목은 비어 있으면 화면에 그 줄이 아예 나오지 않아요(빈칸이 노출되지 않음).
 */
window.EVENT_CONFIG = {
  // 구글폼 응답 링크 (예: https://forms.gle/xxxx 또는 https://docs.google.com/forms/d/e/.../viewform)
  formUrl: "https://forms.gle/E6M2LTdFZdXUWuTX6",

  // 기존 고전 소개 릴스
  reelUrl: "https://www.instagram.com/p/DehQbUPP6es/",

  // 북끼끼 공식 링크
  instagramUrl: "https://www.instagram.com/bookkiki.official/",
  appUrl: "https://bookkiki.com/download",

  // 문의처 (참고 노션에 공개돼 있는 주소)
  contactEmail: "contact@bookkiki.com",

  // 법적 고지용 운영자 정보 — 운영자가 직접 입력
  operator: {
    name: "북끼끼(BOOKKIKI)",            // 이벤트 주최
    privacyOfficer: "황채원(대표)",  // 개인정보 보호책임자
    retention: "선정 연락과 배송이 끝나면 지체 없이 파기"
  }
};
