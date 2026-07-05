#!/usr/bin/env python3
"""생일 쿠지 티켓 생성기.

결과 종류(꽝, +1, +5, +10)당 URL을 하나씩만 만들고, 같은 결과 티켓은 같은 QR을 복붙한다.

실행하면 다음 세 가지를 만든다.
  1. index.html 안의 티켓 데이터(base64)를 새로 채운다
  2. private/answer-key.csv  — 결과별 URL과 인쇄 장수 (QR을 직접 만들 때 이 URL 사용)
  3. private/qr-sheet.html   — A4 인쇄용 QR 시트, 같은 QR을 장수만큼 반복 배치 (segno 설치 시에만)

주의: 다시 실행하면 토큰이 전부 바뀌므로, 이미 인쇄한 QR은 무효가 된다.
"""
import base64
import csv
import json
import random
import re
import sys
from pathlib import Path

# ── 설정: 여기만 고치면 된다 ─────────────────────────────
CONFIG = [        # (더 뽑기 횟수, 장수) — 횟수 0은 꽝
    (10, 1),
    (5, 2),
    (1, 25),
    (0, 52),
]
BASE_URL = "https://surpmh.github.io/event/birthday/"
# ─────────────────────────────────────────────────────

TOKEN_LEN = 5
CHARS = "abcdefghjkmnpqrstuvwxyz23456789"   # 헷갈리는 글자 i, l, o, 0, 1 제외
HERE = Path(__file__).resolve().parent
PRIVATE = HERE / "private"


def result_label(r: int) -> str:
    return "꽝" if r == 0 else f"{r}번 더"


def main() -> None:
    rng = random.SystemRandom()
    tokens: set[str] = set()
    while len(tokens) < len(CONFIG):
        tokens.add("".join(rng.choice(CHARS) for _ in range(TOKEN_LEN)))
    token_list = sorted(tokens)
    rng.shuffle(token_list)

    # 결과 종류당 토큰 하나 — (토큰, 횟수, 인쇄 장수)
    rows = [(tok, n, cnt) for tok, (n, cnt) in zip(token_list, CONFIG)]
    mapping = {tok: n for tok, n, _ in rows}   # {토큰: 횟수}, 0은 꽝

    # 1) index.html에 주입
    packed = base64.b64encode(
        json.dumps(mapping, separators=(",", ":")).encode()
    ).decode()
    html_path = HERE / "index.html"
    html = html_path.read_text(encoding="utf-8")
    new_html, n = re.subn(
        r'/\*TICKETS\*/"[^"]*"/\*TICKETS\*/',
        f'/*TICKETS*/"{packed}"/*TICKETS*/',
        html,
    )
    if n != 1:
        sys.exit("index.html에서 티켓 데이터 자리를 찾지 못했습니다")
    html_path.write_text(new_html, encoding="utf-8")

    PRIVATE.mkdir(exist_ok=True)

    # 2) 정답표 CSV
    with open(PRIVATE / "answer-key.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["결과", "인쇄 장수", "URL"])
        for tok, n, cnt in rows:
            w.writerow([result_label(n), cnt, f"{BASE_URL}?t={tok}"])

    # 3) QR 인쇄 시트 (segno가 있을 때만)
    try:
        import segno
    except ImportError:
        segno = None
    if segno:
        cells = []
        for tok, n, cnt in rows:
            uri = segno.make(f"{BASE_URL}?t={tok}", error="m").svg_data_uri(border=2)
            star = '<span class="star">★</span>' if n > 0 else ""
            cells.extend([f'<div class="cell">{star}<img src="{uri}" alt=""></div>'] * cnt)
        sheet = QR_SHEET_TEMPLATE.replace("__CELLS__", "\n".join(cells))
        (PRIVATE / "qr-sheet.html").write_text(sheet, encoding="utf-8")

    total = sum(cnt for _, cnt in CONFIG)
    summary = ", ".join(f"{result_label(n)} {cnt}장" for n, cnt in CONFIG)
    print(f"티켓 {total}장 생성 완료 ({summary})")
    print(f"- index.html 티켓 데이터 갱신")
    print(f"- {PRIVATE / 'answer-key.csv'}")
    if segno:
        print(f"- {PRIVATE / 'qr-sheet.html'} (브라우저에서 열어 인쇄)")
    else:
        print("- segno가 없어 QR 시트는 건너뜀 (pip install segno 후 재실행)")


QR_SHEET_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>생일 쿠지 QR 시트</title>
<style>
  @page { size: A4; margin: 8mm; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: sans-serif; }
  .grid { display: grid; grid-template-columns: repeat(5, 1fr); }
  .cell {
    position: relative;
    border: 1px dashed #aaa;
    padding: 3mm 0;
    text-align: center;
    break-inside: avoid;
  }
  .cell img { width: 26mm; height: 26mm; display: block; margin: 0 auto; }
  .star { position: absolute; top: 1mm; right: 2mm; color: #d99e00; font-size: 11pt; }
  @media screen {
    body { background: #eee; padding: 20px; }
    .grid { max-width: 800px; margin: 0 auto; background: #fff; padding: 10px; }
  }
</style>
</head>
<body>
<div class="grid">
__CELLS__
</div>
</body>
</html>
"""

if __name__ == "__main__":
    main()
