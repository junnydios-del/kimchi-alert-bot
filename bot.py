import os
import json
import datetime
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

COMMON_FILE = "common_coins.json"
AUTO_DIFF = 1.5   # 자동 알림 기준 %
MANUAL_DIFF = 0.5 # 수동 조회 표시 기준 %


# ===============================
# 공통 코인 생성 (수동 실행)
# ===============================
def generate_common_coins():
    upbit = requests.get(
        "https://api.upbit.com/v1/market/all", timeout=10
    ).json()

    upbit_coins = {
        m["market"].replace("KRW-", "")
        for m in upbit if m["market"].startswith("KRW-")
    }

    bithumb = requests.get(
        "https://api.bithumb.com/public/ticker/ALL_KRW", timeout=10
    ).json()

    bithumb_coins = set(bithumb["data"].keys()) - {"date"}

    common = sorted(upbit_coins & bithumb_coins)

    with open(COMMON_FILE, "w") as f:
        json.dump({
            "date": datetime.date.today().isoformat(),
            "coins": common
        }, f)

    print(f"[INIT] 공통 코인 {len(common)}개 저장 완료")


# ===============================
# 로드
# ===============================
def load_common_coins():
    if not os.path.exists(COMMON_FILE):
        raise Exception("common_coins.json 없음. 먼저 수동 생성하세요.")

    with open(COMMON_FILE, "r") as f:
        return json.load(f)["coins"]


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
# 수동 조회
# ===============================
def manual_query():
    coins = load_common_coins()
    diffs = []

    for c in coins:
        try:
            up = get_upbit_price(c)
            bt = get_bithumb_price(c)
            diff = ((up - bt) / bt) * 100
            if abs(diff) >= MANUAL_DIFF:
                diffs.append((c, diff))
        except:
            continue

    if not diffs:
        send_telegram("📊 조회 결과 없음")
        return

    diffs.sort(key=lambda x: x[1], reverse=True)

    msg = "📊 업비트 ↔ 빗썸 가격차이\n\n"
    msg += "📈 상위 10\n"
    for s, d in diffs[:10]:
        msg += f"{s}: {d:.2f}%\n"

    msg += "\n📉 하위 10\n"
    for s, d in diffs[-10:]:
        msg += f"{s}: {d:.2f}%\n"

    send_telegram(msg)


# ===============================
# 자동 감시
# ===============================
def auto_watch():
    coins = load_common_coins()
    alerts = []

    for c in coins:
        try:
            up = get_upbit_price(c)
            bt = get_bithumb_price(c)
            diff = ((up - bt) / bt) * 100
            if abs(diff) >= AUTO_DIFF:
                alerts.append(f"{c}: {diff:.2f}%")
        except:
            continue

    if alerts:
        send_telegram("🚨 가격 차이 알림\n\n" + "\n".join(alerts))


# ===============================
# 실행
# ===============================
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("사용법: python bot.py [init|manual|auto]")
        exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        generate_common_coins()
    elif cmd == "manual":
        manual_query()
    elif cmd == "auto":
        auto_watch()
    else:
        print("사용법: python bot.py [init|manual|auto]")
