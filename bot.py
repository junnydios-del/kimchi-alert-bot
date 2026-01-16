import os
import json
import datetime
import requests

# ===============================
# 설정
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DIFF_THRESHOLD = 2.0  # % 차이 기준


# ===============================
# 공통 코인 하루 1회 갱신
# ===============================
def update_common_coins():
    def get_upbit():
        url = "https://api.upbit.com/v1/market/all"
        res = requests.get(url, timeout=10).json()
        return {
            m["market"].replace("KRW-", "")
            for m in res
            if m["market"].startswith("KRW-")
        }

    def get_bithumb():
        url = "https://api.bithumb.com/public/ticker/ALL_KRW"
        res = requests.get(url, timeout=10).json()
        return set(res["data"].keys()) - {"date"}

    common = sorted(list(get_upbit() & get_bithumb()))

    data = {
        "date": datetime.date.today().isoformat(),
        "coins": common
    }

    with open("common_coins.json", "w") as f:
        json.dump(data, f)

    print(f"[INFO] 공통 코인 {len(common)}개 갱신 완료")


def load_common_coins():
    today = datetime.date.today().isoformat()

    if not os.path.exists("common_coins.json"):
        update_common_coins()

    with open("common_coins.json", "r") as f:
        data = json.load(f)

    if data.get("date") != today:
        update_common_coins()
        with open("common_coins.json", "r") as f:
            data = json.load(f)

    return data["coins"]


# ===============================
# 가격 조회
# ===============================
def get_upbit_price(symbol):
    url = "https://api.upbit.com/v1/ticker"
    params = {"markets": f"KRW-{symbol}"}
    res = requests.get(url, params=params, timeout=10).json()
    return float(res[0]["trade_price"])


def get_bithumb_price(symbol):
    url = f"https://api.bithumb.com/public/ticker/{symbol}_KRW"
    res = requests.get(url, timeout=10).json()
    return float(res["data"]["closing_price"])


# ===============================
# 텔레그램 전송
# ===============================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data, timeout=10)


# ===============================
# 메인 감시 로직 (1회 실행)
# ===============================
def price_watcher():
    coins = load_common_coins()
    alerts = []

    for symbol in coins:
        try:
            up = get_upbit_price(symbol)
            bt = get_bithumb_price(symbol)

            diff = ((up - bt) / bt) * 100

            if abs(diff) >= DIFF_THRESHOLD:
                alerts.append(
                    f"{symbol}\n"
                    f"업비트: {up:,.0f}원\n"
                    f"빗썸: {bt:,.0f}원\n"
                    f"차이: {diff:.2f}%"
                )

        except Exception as e:
            print(f"[SKIP] {symbol} 오류: {e}")

    if alerts:
        message = "🚨 가격 차이 알림 🚨\n\n" + "\n\n".join(alerts)
        send_telegram(message)
    else:
        print("[INFO] 조건 만족 코인 없음")


# ===============================
# 실행 지점 (절대 위치 중요)
# ===============================
if __name__ == "__main__":
    price_watcher()
