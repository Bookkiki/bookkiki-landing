#!/usr/bin/env python3
"""download/index.html로 홈(index.html)을 만든다.

홈은 /download/와 같은 화면을 보여 준다. 다른 점은 세 가지다.
- 휴대폰에서도 스토어로 바로 보내지 않고 화면을 보여 준다(/download/?stay=1과 같음).
- 경로를 루트 기준으로 바꾼다(../assets/ → assets/).
- 맨 아래에 사업자 정보와 약관·결제 안내 링크를 둔다. 이용약관이 서비스 초기 화면에 게시한다고 정한 항목이다.

/download/를 고친 뒤에는 이 스크립트를 다시 실행한다. --check는 index.html이 최신인지만 확인한다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "download" / "index.html"
TARGET = ROOT / "index.html"

NOTICE = "<!-- download/index.html에서 scripts/build-root-index.py로 만든 파일이다. 직접 고치지 말고 스크립트를 다시 실행한다. -->\n"

FOOTER_CSS = """  footer .links{display:flex;flex-wrap:wrap;justify-content:center;gap:6px 0}
  footer .biz{display:flex;flex-wrap:wrap;justify-content:center;gap:2px 14px;margin:14px auto 0;max-width:760px;font-size:12px;line-height:1.6;color:var(--faint)}
  footer .biz span{margin-right:5px;color:var(--muted)}
  footer .copy{margin-top:10px;font-size:12px;color:var(--faint)}
"""

FOOTER = """<footer>
  <div class="links">
    <a href="terms.html">이용약관</a><a href="privacy.html"><strong>개인정보처리방침</strong></a><a href="refund.html">취소·환불·배송 정책</a><a href="review.html#general-payment">실물책 결제 안내</a><a href="review.html#recurring-payment">정기결제 안내</a><a href="https://www.ftc.go.kr/bizCommPop.do?wrkr_no=5254301349" target="_blank" rel="noopener">사업자정보확인</a><a href="https://www.instagram.com/bookkiki.official/">인스타그램</a>
  </div>
  <ul class="biz">
    <li><span>상호</span>북끼끼(BOOKKIKI)</li>
    <li><span>대표자</span>황채원</li>
    <li><span>사업자등록번호</span>525-43-01349</li>
    <li><span>통신판매업신고번호</span>신고 진행 중</li>
    <li><span>주소</span>경기도 안산시 단원구 원선1로 10, 101동 1004호 (원곡동, 초지역메이저타운푸르지오에코단지아파트)</li>
    <li><span>전화</span>010-2497-1267</li>
    <li><span>이메일</span>contact@bookkiki.com</li>
    <li><span>고객센터</span>평일 10:00~18:00 (주말·공휴일 휴무)</li>
    <li><span>개인정보보호책임자</span>황채원</li>
  </ul>
  <div class="copy">© 2026 북끼끼. All rights reserved.</div>
</footer>"""

REPLACEMENTS = [
    ('<meta property="og:url" content="https://bookkiki.com/download/">',
     '<meta property="og:url" content="https://bookkiki.com/">'),
    ("var stay = /[?&]stay=1/.test(q);",
     "var stay = true; // 홈은 휴대폰에서도 스토어로 바로 보내지 않는다."),
    ("  /* sticky store bar */\n", FOOTER_CSS + "\n  /* sticky store bar */\n"),
    ('<footer><a href="../">북끼끼 홈페이지</a><a href="https://www.instagram.com/bookkiki.official/">인스타그램</a></footer>',
     FOOTER),
    ("=== '../' ? 'home'", "=== './' ? 'home'"),
    ('<a class="brand" href="../">', '<a class="brand" href="./">'),
]


def build() -> str:
    html = SOURCE.read_text(encoding="utf-8")
    for old, new in REPLACEMENTS:
        if html.count(old) != 1:
            sys.exit(f"download/index.html에서 바꿀 부분을 정확히 하나 찾지 못했다: {old[:60]}")
        html = html.replace(old, new)
    html = html.replace("../assets/", "assets/")
    if "../" in html:
        sys.exit("루트로 옮기지 못한 ../ 경로가 남아 있다")
    doctype, rest = html.split("\n", 1)
    return f"{doctype}\n{NOTICE}{rest}"


def main() -> None:
    html = build()
    if "--check" in sys.argv[1:]:
        if TARGET.read_text(encoding="utf-8") != html:
            sys.exit("index.html이 download/index.html과 맞지 않는다. scripts/build-root-index.py를 실행한다.")
        return
    TARGET.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
