import requests
import time
from telegram import Bot

BOT_TOKEN = "네_텔레그램_토큰"
CHAT_ID = "네_채팅_ID"

bot = Bot(token=BOT_TOKEN)

# 1. 업비트 KRW 코인
def get_upbit_krw_coins():
    url = "https://api.upbit.com/v1/market/all"
    data = requests.get(url).json()
    return {m["market"].replace("KRW-", "") for m in data if m["market"].startswith("KRW-")}

# 2. 빗썸 KRW 코인
def get_bithumb_krw_coins():
    url = "https://api.bithumb.com/public/ticker/ALL_KRW"
    data = requests.get(url).json()["data"]
    return {k for k in data.keys() if k != "date"}

# 3. 가격 조회
def get_upbit_price(symbol):
    url = f"https://api.upbit.com/v1/ticker?markets=KRW-{symbol}"
    return requests.get(url).json()[0]["trade_price"]

def get_bithumb_price(symbol):
    url = f"https://api.bithumb.com/public/ticker/{symbol}_KRW"
    return float(requests.get(url).json()["data"]["closing_price"])

# 4. 메인 감시 함수
def price_watcher():
    upbit = get_upbit_krw_coins()
    bithumb = get_bithumb_krw_coins()
    common_coins = upbit & bithumb

    alerts = []

    for coin in common_coins:
        try:
            up = get_upbit_price(coin)
            bt = get_bithumb_price(coin)

            diff = (bt - up) / up * 100

            # 🔥 실전 튜닝 조건 (아래 설명)
            if abs(diff) >= 2.5:
                alerts.append(
                    f"{coin}\n"
                    f"업비트: {up:,}원\n"
                    f"빗썸: {bt:,}원\n"
                    f"차이: {diff:.2f}%"
                )

            time.sleep(0.1)  # API 과부하 방지

        except:
            continue

    if alerts:
        bot.send_message(chat_id=CHAT_ID, text="\n\n".join(alerts))


if __name__ == "__main__":
    price_watcher()
