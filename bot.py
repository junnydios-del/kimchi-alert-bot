import os
import requests

# ===============================
# 설정 (GitHub Secrets)
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise Exception("BOT_TOKEN 또는 CHAT_ID 없음 (GitHub Secrets 확인)")

# ===============================
# 업비트 ↔ 빗썸 공통 코인 조회
# ===============================
def get_common_coins():
    # 업비트 KRW 마켓
    upbit = requests.get(
        "https://api.upbit.com/v1/market/all",
        timeout=10
    ).json()

    upbit_coins = set()
    for m in upbit:
        if m.get("market", "").startswith("KRW-"):
            upbit_coins.add(m["market"].replace("KRW-", ""))

    # 빗썸 KRW 마켓
    bithumb = requests.get(
        "https://api.bithumb.com/public/ticker/ALL_KRW",
        timeout=10
    ).json()

    bithumb_coins = set(bithumb["data"].keys()) - {"date"}

    return sorted(upbit_coins & bithumb_coins)

# ===============================
# 텔레그램 전송
# ===============================
def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": msg
        },
        timeout=10
    )

# ===============================
# 실행
# ===============================
if __name__ == "__main__":
    coins = get_common_coins()

    if not coins:
        send_telegram("❌ 공통 코인 조회 실패")
        exit(1)

    msg = f"📌 업비트 ↔ 빗썸 공통 코인 ({len(coins)}개)\n\n"
    msg += "\n".join(coins)

    send_telegram(msg)
    print(f"[OK] 공통 코인 {len(coins)}개 전송 완료")
