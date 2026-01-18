import os
import json
import datetime
import requests

# ===============================
# 설정
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

DIFF_THRESHOLD = 1.5  # % 차이 기준
COMMON_FILE = "tradable_coins.json"


# ===============================
# 공통 + 입출금 가능 코인 하루 1회 생성
# ===============================
def update_tradable_coins():
    # 업비트 KRW
    upbit = requests.get(
        "https://api.upbit.com/v1/market/all", timeout=10
    ).json()

    upbit_coins = {
        m["market"].replace("KRW-", "")
        for m in upbit
        if m["market"].startswith("KRW-")
    }

    # 빗썸 KRW
    bithumb = requests.get(
        "https://api.bithumb.com/public/ticker/ALL_KRW", timeout=10
    ).json()

    bithumb_coins = set(bithumb["data"].keys()) - {"date"}

    common = upbit_coins & bithumb_coins

    # ✅ 업비트 지갑 상태 (중요)
    wallet = requests.get(
        "https://api.upbit.com/v1/status/wallet", timeout=10
    ).json()

    wallet_data = wallet.get("data", [])   # ← 이 줄이 반드시 있어야 함

    wallet_map = {
        c.get("currency"): (
            c.get("deposit_state") == "ACTIVE" and
            c.get("withdraw_state") == "ACTIVE"
        )
        for c in wallet_data
    }

    tradable = sorted([
        c for c in common if wallet_map.get(c)
    ])

    with open("tradable_coins.json", "w") as f:
        json.dump({
            "date": datetime.date.today().isoformat(),
            "coins": tradable
        }, f)

    print(f"[INFO] 입출금 가능 공통 코인 {len(tradable)}개 저장")


def load_tradable_coins():
    today = datetime.date.today().isoformat()

    if not os.path.exists(COMMON_FILE):
        update_tradable_coins()

    with open(COMMON_FILE, "r") as f:
        data = json.load(f)

    if data["date"] != today:
        update_tradable_coins()
        with open(COMMON_FILE, "r") as f:
            data = json.load(f)

    return data["coins"]


# ===============================
# 가격 조회
# ===============================
def get_upbit_price(symbol):
    r = requests.get(
        "https://api.upbit.com/v1/ticker",
        params={"markets": f"KRW-{symbol}"},
        timeout=10
    ).json()
    return float(r[0]["trade_price"])


def get_bithumb_price(symbol):
    r = requests.get(
        f"https://api.bithumb.com/public/ticker/{symbol}_KRW",
        timeout=10
    ).json()
    return float(r["data"]["closing_price"])


# ===============================
# 텔레그램
# ===============================
def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )


# ===============================
# 가격 감시 (5분마다 실행)
# ===============================
def price_watcher():
    command = load_command()

    if command == "query":
        send_query_result()
        clear_command()
        return

def price_watcher():
    coins = load_tradable_coins()
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
            print(f"[SKIP] {symbol}: {e}")

    if alerts:
        send_telegram(
            "🚨 가격 차이 알림 🚨\n\n" + "\n\n".join(alerts)
        )
    else:
        print("[INFO] 조건 만족 없음")


# ===============================
# 실행
# ===============================
if __name__ == "__main__":
    price_watcher()


def load_command():
    if not os.path.exists("command.json"):
        return None

    with open("command.json", "r") as f:
        data = json.load(f)

    return data.get("command")


def clear_command():
    with open("command.json", "w") as f:
        json.dump({"command": None}, f)


def get_all_diffs():
    coins = load_common_coins()
    diffs = []

    for symbol in coins:
        try:
            up = get_upbit_price(symbol)
            bt = get_bithumb_price(symbol)

            diff = ((up - bt) / bt) * 100
            diffs.append((symbol, diff))

        except:
            continue

    return diffs

def send_query_result():
    diffs = get_all_diffs()

    if not diffs:
        send_telegram("조회 실패")
        return

    diffs.sort(key=lambda x: x[1], reverse=True)

    top10 = diffs[:10]
    bottom10 = diffs[-10:][::-1]

    msg = "📊 업비트 ↔ 빗썸 가격차이\n\n"

    msg += "📈 상위 10\n"
    for s, d in top10:
        msg += f"{s}: {d:.2f}%\n"

    msg += "\n📉 하위 10\n"
    for s, d in bottom10:
        msg += f"{s}: {d:.2f}%\n"

    send_telegram(msg)

