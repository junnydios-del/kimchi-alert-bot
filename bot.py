import os
import requests

# ===============================
# 설정 (GitHub Secrets 사용)
# ===============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise Exception("BOT_TOKEN 또는 CHAT_ID 없음 (GitHub Secrets 확인)")

# ===============================
# 공통 코인 계산
# ===============================
def get_common_coins():
    # 업비트 KRW
    upbit = requests.get(
        "https://api.upbit.com/v1/market/all",
        timeout=10
    ).json()

    upbit_coins = {
        m["market"].replace("KRW-", "")
        for m
