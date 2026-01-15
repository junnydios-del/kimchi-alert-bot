import requests
import time
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

COINS = [
    "SAFE","BOUNTY","MTL","BREV","KAITO","GLM","ZK","DOT","OP","CHZ",
    "AVNT","PUMP","AKT","MON","MEW","XAUT","LSK","DEEP","APT","ORBS",
    "MINA","WET","ZIL","RENDER","PLUME","CKB","FLOCK","SOPH","ME","POLYX",
    "OG","AAVE","ONT","BERA","SAHARA","MASK","CTC","COW","ARKM","F",
    "ARK","ANIME","WAL","HYPER","ATH","CARV","TIA","KNC","STORJ","ELF"
]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

def get_upbit_prices():
    markets = ",".join([f"KRW-{c}" for c in COINS])
    url = f"https://api.upbit.com/v1/ticker?markets={markets}"
    res = requests.get(url).json()
    return {x["market"].replace("KRW-",""): x["trade_price"] for x in res}

def get_bithumb_price(coin):
    url = f"https://api.bithumb.com/public/ticker/{coin}_KRW"
    res = requests.get(url).json()
    if res["status"] != "0000":
        return None
    return float(res["data"]["closing_price"])

while True:
    try:
        upbit = get_upbit_prices()

        for coin in COINS:
            if coin not in upbit:
                continue

            bithumb = get_bithumb_price(coin)
            if not bithumb:
                continue

            u = upbit[coin]
            b = bithumb

            high = max(u, b)
            low = min(u, b)
            diff = (high - low) / low * 100

            if diff >= 2.0:
                where = "업비트" if u > b else "빗썸"
                msg = (
                    f"[시세 차이 감지]\n"
                    f"{coin}\n"
                    f"업비트: {u:,.0f}원\n"
                    f"빗썸: {b:,.0f}원\n"
                    f"차이: {diff:.2f}%\n"
                    f"비싼곳: {where}"
                )
                send_telegram(msg)

        time.sleep(60)

    except Exception:
        time.sleep(60)
