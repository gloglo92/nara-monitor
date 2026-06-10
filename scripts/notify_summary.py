"""
나라장터 일일 요약 텔레그램 알림 (하루 1회)
- 빈번한 수집 run 중 '그날 첫 성공 run'만 요약 1통 발송
- 마커파일(docs/data/.last_summary)로 중복 발송 방지
- force_notify=true 면 마커 무시하고 강제 발송 (수동 테스트용)
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta, timezone

# ── 환경변수 ──────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
FORCE_NOTIFY     = os.environ.get("FORCE_NOTIFY", "false").lower() == "true"

WEBSITE_URL = "https://gloglo92.github.io/nara-monitor/"

DATA_DIR    = Path(__file__).parent.parent / "docs" / "data"
MARKER_PATH = DATA_DIR / ".last_summary"


SUMMARY_HOUR_KST = 19   # ★ 요약은 하루 데이터가 쌓인 저녁 19시 이후에 발송


def get_target_date() -> str:
    """오늘(또는 TARGET_DATE) 날짜 문자열 YYYYMMDD 반환"""
    target = os.environ.get("TARGET_DATE", "").strip()
    if target and len(target) == 8:
        return target
    KST = timezone(timedelta(hours=9))
    return datetime.now(KST).strftime("%Y%m%d")   # ★ 오늘


def read_filtered(date_str: str, data_type: str) -> dict:
    """필터링 결과 JSON 읽기. 없으면 0건 처리."""
    path = DATA_DIR / f"{date_str}-{data_type}-filtered.json"
    if not path.exists():
        return {"confirmed_count": 0, "review_count": 0, "found": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "confirmed_count": data.get("confirmed_count", 0),
            "review_count":    data.get("review_count", 0),
            "found":           True,
        }
    except Exception as e:
        print(f"⚠️ {path} 읽기 실패: {e}")
        return {"confirmed_count": 0, "review_count": 0, "found": False}


def send_telegram(text: str) -> bool:
    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id":                  TELEGRAM_CHAT_ID,
            "text":                     text,
            "parse_mode":               "Markdown",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    if resp.status_code == 200:
        print("✅ 요약 발송 성공")
        return True
    print(f"❌ 요약 발송 실패: {resp.text}")
    return False


def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ 텔레그램 Secret 미설정 → 요약 생략")
        return

    date_str = get_target_date()

    # ── 저녁(19시) 이후에만 발송 (하루 데이터가 다 쌓인 뒤 요약) ──
    KST = timezone(timedelta(hours=9))
    if not FORCE_NOTIFY and datetime.now(KST).hour < SUMMARY_HOUR_KST:
        print(f"ℹ️ 아직 요약 시각(KST {SUMMARY_HOUR_KST}시) 전 → 생략")
        return

    # ── 중복 발송 방지 ────────────────────────────────────────
    if not FORCE_NOTIFY and MARKER_PATH.exists():
        last = MARKER_PATH.read_text(encoding="utf-8").strip()
        if last == date_str:
            print(f"ℹ️ {date_str} 요약 이미 발송됨 → 종료")
            return

    spec  = read_filtered(date_str, "사전규격")
    order = read_filtered(date_str, "발주계획")

    if not spec["found"] and not order["found"]:
        print("ℹ️ 해당 날짜 데이터 파일 없음 → 요약 생략")
        return

    y, m, d = date_str[:4], date_str[4:6], date_str[6:]
    msg = (
        f"📊 *나라장터 일일 요약* ({y}-{m}-{d})\n"
        f"\n"
        f"📋 사전규격: 확정 *{spec['confirmed_count']}건* / 검토 {spec['review_count']}건\n"
        f"📌 발주계획: 확정 *{order['confirmed_count']}건* / 검토 {order['review_count']}건\n"
        f"\n"
        f"🔗 [상세 보기 · 엑셀 다운로드]({WEBSITE_URL})"
    )

    if send_telegram(msg):
        # ── 마커 기록 (다음 run이 중복 발송 안 하도록) ──────────
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        MARKER_PATH.write_text(date_str, encoding="utf-8")
        print(f"✅ 마커 갱신: {date_str}")


if __name__ == "__main__":
    main()
