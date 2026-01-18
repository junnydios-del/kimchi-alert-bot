import requests
import json
import os
import sys
import time
from datetime import datetime, timedelta

# =====================
# 설정값
# =====================
UPBIT_URL = "https://api.upbit.com/v1/ticker"
BITHUMB_URL = "https://api.bithumb.com/public/ticker/ALL_KRW"

COMMON_COINS_FILE = "common_coins.json"
LAST_ALERT_FILE = "last_alert.json"

MANUAL_THRESHOLD = 0.5   # %
AUTO_THRESHOLD = 1.5     # %
ALERT_COOLDOWN_HOURS = 3

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# =====================
# 유틸
# =====================
def send_telegram(msg: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARN] 텔레그램 토큰/아이디 없음")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg
    })


def load_common_coins():
    if not os.path.exists(COMMON_COINS_FILE):
        raise Exception(
            "common_coins.json 없음.\n"
            "로컬에서 python bot.py init 실행 후\n"
            "git commit & push 하세요."
        )
    with open(COMMON_COINS_FILE, "r") as f:
        return json.load(f)


def load_last_alert():
    if not os.path.exists(LAST_ALERT_FILE):
        return {}
    with open(LAST_ALERT_FILE, "r") as f:
        return json.load(f)


def save_last_alert(data):
    with open(LAST_ALERT_FILE, "w") as f:
        json.dump(data, f, indent=2)


# =====================
# 시세 조회
# =====================
def get_upbit_prices(coins):
    markets = [f"KRW-{c}" for c in coins]
    r = requests.get(UPBIT_URL, params={"markets": ",".join(markets)}).json()

    prices = {}
    for item in r:
        symbol = item["market"].replace("KRW-", "")
        prices[symbol] = item["trade_price"]
    return prices


def get_bithumb_prices():
    r = requests.get(BITHUMB_URL).json()
    prices = {}
    for symbol, data in r["data"].items():
        if symbol == "date":
            continue
        prices[symbol] = float(data["closing_price"])
    return prices


# =====================
# 공통 코인 생성 (로컬 전용)
# =====================
def generate_common_coins():
    upbit_markets = requests.get("https://api.upbit.com/v1/market/all").json()
    upbit_coins = {
        m["market"].replace("KRW-", "")
        for m in upbit_markets
        if m["market"].startswith("KRW-")
    }

    bithumb = requests.get(BITHUMB_URL).json()["data"]
    bithumb_coins = set(bithumb.keys()) - {"date"}

    common = sorted(list(upbit_coins & bithumb_coins))

    with open(COMMON_COINS_FILE, "w") as f:
        json.dump(common, f, indent=2)

    print(f"[INIT] 공통 코인 {len(common)}개 저장 완료")


# =====================
# 비교 로직
# =====================
def compare_prices(threshold, send_alert=False):
    coins = load_common_coins()
    upbit = get_upbit_prices(coins)
    bithumb = get_bithumb_prices()

    last_alert = load_last_alert()
    now = datetime.utcnow()

    results = []

    for c in coins:
        if c not in upbit or c not in bithumb:
            continue

        u = upbit[c]
        b = bithumb[c]

        diff = (u - b) / b * 100
        diff = round(diff, 2)

        if abs(diff) < threshold:
            continue

        # 자동 알림 쿨타임 체크
        if send_alert:
            last_time_str = last_alert.get(c)
            if last_time_str:
                last_time = datetime.fromisoformat(last_time_str)
                if now - last_time < timedelta(hours=ALERT_COOLDOWN_HOURS):
                    continue

        results.append((c, u, b, diff))

        if send_alert:
            msg = (
                f"[김프 알림]\n"
                f"{c}\n"
                f"업비트: {u:,} KRW\n"
                f"빗썸: {b:,} KRW\n"
                f"차이: {diff}%"
            )
            send_telegram(msg)
            last_alert[c] = now.isoformat()

    if send_alert:
        save_last_alert(last_alert)

    return results


# =====================
# 명령
# =====================
def manual_query():
    results = compare_prices(MANUAL_THRESHOLD, send_alert=True)
    print(f"[MANUAL] 알림 {len(results)}건 전송")


def auto_monitor():
    results = compare_prices(AUTO_THRESHOLD, send_alert=True)
    print(f"[AUTO] 알림 {len(results)}건 전송")


# =====================
# 진입점
# =====================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python bot.py [manual|auto]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        print("⚠️ init은 로컬에서만 사용하세요.")
        generate_common_coins()
    elif cmd == "manual":
        manual_query()
    elif cmd == "auto":
        auto_monitor()
    else:
        print("사용법: python bot.py [manual|auto]")
        sys.exit(1)
