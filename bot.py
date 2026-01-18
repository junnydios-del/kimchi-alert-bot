import requests
import json
import os
import sys
import time
from datetime import datetime, timedelta

# ======================
# 설정
# ======================
UPBIT_URL = "https://api.upbit.com/v1/ticker"
BINANCE_URL = "https://api.binance.com/api/v3/ticker/price"

COMMON_FILE = "common_coins.json"
EXCLUDED_FILE = "excluded_coins.json"
COOLDOWN_FILE = "cooldown.json"

AUTO_THRESHOLD = 1.5
MANUAL_THRESHOLD = 0.5
COOLDOWN_HOURS = 3

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ======================
# 유틸
# ======================
def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ 텔레그램 설정 없음")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg})


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ======================
# 가격 수집
# ======================
def get_upbit_prices():
    markets = requests.get("https://api.upbit.com/v1/market/all").json()
    markets = [m["market"] for m in markets if m["market"].startswith("KRW-")]

    prices = {}
    for i in range(0, len(markets), 100):
        chunk = markets[i:i+100]
        res = requests.get(UPBIT_URL, params={"markets": ",".join(chunk)}).json()
        for r in res:
            prices[r["market"].replace("KRW-", "")] = r["trade_price"]
    return prices


def get_binance_prices():
    res = requests.get(BINANCE_URL).json()
    prices = {}
    for r in res:
        if r["symbol"].endswith("USDT"):
            prices[r["symbol"].replace("USDT", "")] = float(r["price"])
    return prices


# ======================
# 공통 코인 생성 (수동)
# ======================
def generate_common_coins():
    upbit = get_upbit_prices()
    binance = get_binance_prices()
    common = sorted(set(upbit.keys()) & set(binance.keys()))
    save_json(COMMON_FILE, common)
    send_telegram(f"✅ 공통 코인 {len(common)}개 생성 완료")


# ======================
# 비교 로직
# ======================
def compare(mode="auto"):
    common = load_json(COMMON_FILE, [])
    excluded = load_json(EXCLUDED_FILE, [])
    cooldown = load_json(COOLDOWN_FILE, {})

    threshold = AUTO_THRESHOLD if mode == "auto" else MANUAL_THRESHOLD
    now = datetime.utcnow()

    upbit = get_upbit_prices()
    binance = get_binance_prices()

    messages = []

    for coin in common:
        if coin in excluded:
            continue
        if coin not in upbit or coin not in binance:
            continue

        price_up = upbit[coin]
        price_bn = binance[coin] * 1300  # 대략 환율

        diff = ((price_up - price_bn) / price_bn) * 100

        if abs(diff) < threshold:
            continue

        # 쿨타임 체크 (자동만)
        if mode == "auto":
            last = cooldown.get(coin)
            if last:
                last_time = datetime.fromisoformat(last)
                if now - last_time < timedelta(hours=COOLDOWN_HOURS):
                    continue
            cooldown[coin] = now.isoformat()

        messages.append(
            f"{coin}\n업비트: {price_up:,.0f}\n바이낸스: {price_bn:,.0f}\n차이: {diff:.2f}%"
        )

    if messages:
        send_telegram(f"📊 {mode.upper()} 조회 결과\n\n" + "\n\n".join(messages))
    else:
        print("ℹ️ 조건 충족 코인 없음")

    save_json(COOLDOWN_FILE, cooldown)


# ======================
# 실행 분기
# ======================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python bot.py [init|manual|auto]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        generate_common_coins()
    elif cmd == "manual":
        compare("manual")
    elif cmd == "auto":
        compare("auto")
    else:
        print("❌ 알 수 없는 명령어")
