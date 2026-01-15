import requests
import os
import json
from datetime import datetime, timedelta

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# ===== 설정 =====
THRESHOLD = 2.0  # % 차이 기준
COINS = [
    "SAFE","BOUNTY","MTL","BREV","GLM","ZK","DOT","OP","CHZ","AVNT",
    "PUMP","AKT","MON","MEW","XAUT","LSK","DEEP","APT","ORBS","MINA",
    "WET","ZIL","RENDER","PLUME","CKB","FLOCK","SOPH","ME","POLYX","OG",
    "AAVE","ONT","BERA","SAHARA","MASK","CTC","COW","ARKM","F",
    "ARK","ANIME","WAL","HYPER","ATH","CARV","TIA","KNC","STORJ","ELF"
]

ALERT_FILE = "last_alert.json"
ALERT_COOLDOWN = timedelta(minutes=30)  # 같은 코인 30분 중복 방지
# =================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def load_last_alert():
    if not os.path.exists(ALERT_FILE):
        return {}
    with open(ALERT_FILE, "r") as f:
        return json.load(f)

def save_last_alert(data):
    with open(ALERT_FILE, "w") as f:
        json.dump(data, f)

def get_bithumb_prices():
    url = "https://api.bithumb.com/public/ticker/ALL_KRW"
    data = requests.get(url, timeout=10).json()["data"]
    return {k: float(v["closing_price"]) for k, v in data.items() if k != "date"}

def get_upbit_prices():
    markets = requests.get("https://api.upbit.com/v1/market/all").json()
    krw_markets = {m["market"].split("-")[1]: m["market"]
                   for m in markets if m["market"].startswith("KRW-")}

    prices = {}
    for coin, market in krw_markets.items():
        ticker = requests.get(
            "https://api.upbit.com/v1/ticker",
            params={"markets": market},
            timeout=10
        ).json()
        if ticker:
            prices[coin] = float(ticker[0]["trade_price"])
    return prices

def main():
    bithumb = get_bithumb_prices()
    upbit = get_upbit_prices()

    last_alert = load_last_alert()
    now = datetime.utcnow()

    for coin in COINS:
        if coin not in bithumb or coin not in upbit:
            continue

        b_price = bithumb[coin]
        u_price = upbit[coin]

        diff_percent = abs(b_price - u_price) / min(b_price, u_price) * 100

        if diff_percent >= THRESHOLD:
            last_time = last_alert.get(coin)
            if last_time:
                last_time = datetime.fromisoformat(last_time)
                if now - last_time < ALERT_COOLDOWN:
                    continue  # 중복 알림 차단

            direction = "빗썸 > 업비트" if b_price > u_price else "업비트 > 빗썸"

            msg = (
                f"🚨 가격 차이 발생\n"
                f"코인: {coin}\n"
                f"차이: {diff_percent:.2f}%\n"
                f"{direction}\n"
                f"빗썸: {b_price:,.0f}원\n"
                f"업비트: {u_price:,.0f}원"
            )
            send_telegram(msg)
            last_alert[coin] = now.isoformat()

    save_last_alert(last_alert)

if __name__ == "__main__":
    main()
