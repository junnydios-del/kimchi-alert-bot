import requests
import time
import os
from datetime import datetime, timedelta

# ===============================
# 설정
# ===============================
ALERT_GAP = 1.5  # %
COOLDOWN_HOURS = 3
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===============================
# 공통 코인 (BTT, FLOW 제거)
# ===============================
COMMON_COINS = {
    "0G","1INCH","2Z","A","AAVE","ADA","AERGO","AERO","AGLD","AHT",
    "AKT","ALGO","ALT","ANIME","ANKR","API3","APT","AQT","ARB","ARDR",
    "ARK","ARKM","ASTR","ATH","ATOM","AUCTION","AVAX","AVNT","AWE","AXS",
    "BARD","BAT","BCH","BEAM","BERA","BIGTIME","BIO","BLAST","BLUR","BONK",
    "BORA","BOUNTY","BREV","BSV","BTC","CARV","CBK","CELO","CHZ",
    "CKB","COMP","COW","CPOOL","CRO","CTC","CVC","CYBER","DEEP","DKA",
    "DOGE","DOOD","DOT","DRIFT","EGLD","ELF","ENA","ENS","ENSO","ERA",
    "ETC","ETH","F","FCT2","FF","FIL","FLOCK","FLUID","G","GAME2",
    "GAS","GLM","GMT","GRT","HBAR","HIVE","HOLO","HP","HUNT","HYPER",
    "ICX","ID","IMX","IN","INJ","IOST","IOTA","IP","IQ","JST","JTO",
    "JUP","KAITO","KAVA","KERNEL","KITE","KNC","LA","LAYER","LINEA",
    "LINK","LPT","LSK","MANA","MASK","MBL","ME","MED","META","MEW",
    "MINA","MIRA","MLK","MMT","MNT","MOC","MOCA","MON","MOODENG","MOVE",
    "MTL","MVL","NEAR","NEO","NEWT","NOM","NXPC","OM","ONDO","ONG","ONT",
    "OP","OPEN","ORBS","ORCA","ORDER","PENDLE","PENGU","PEPE","PLUME",
    "POKT","POL","POLYX","POWR","PROVE","PUMP","PUNDIX","PYTH","QKC",
    "QTUM","RAY","RED","RENDER","RVN","SAFE","SAHARA","SAND","SC","SEI",
    "SHIB","SIGN","SNT","SOL","SOMI","SONIC","SOPH","STEEM","STG",
    "STORJ","STRAX","STX","SUI","SUN","SUPER","SXP","SYRUP","T","TAIKO",
    "TFUEL","THETA","TIA","TOKAMAK","TOSHI","TREE","TRUMP","TRUST","TRX",
    "TT","UNI","USD1","USDC","USDE","USDT","VANA","VET","VIRTUAL","VTHO",
    "W","WAL","WAVES","WAXP","WCT","WET","WLD","WLFI","XAUT","XEC",
    "XLM","XPL","XRP","XTZ","YGG","ZBT","ZETA","ZIL","ZK","ZKC","ZKP",
    "ZORA","ZRO","ZRX"
}

# ===============================
# 메모리 쿨타임 (실행 중 유지)
# ===============================
last_alert_time = {}

# ===============================
# API
# ===============================
def get_upbit_prices():
    r = requests.get("https://api.upbit.com/v1/ticker/all?quote_currencies=KRW").json()
    return {
        x["market"].replace("KRW-", ""): x["trade_price"]
        for x in r
        if x["market"].startswith("KRW-")
    }

def get_bithumb_prices():
    r = requests.get("https://api.bithumb.com/public/ticker/ALL_KRW").json()["data"]
    return {
        k: float(v["closing_price"])
        for k, v in r.items()
        if k != "date"
    }

# ===============================
# 텔레그램
# ===============================
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

# ===============================
# 메인 로직
# ===============================
def run():
    upbit = get_upbit_prices()
    bithumb = get_bithumb_prices()

    now = datetime.utcnow()

    for coin in COMMON_COINS:
        if coin not in upbit or coin not in bithumb:
            continue

        u = upbit[coin]
        b = bithumb[coin]

        if u <= 0 or b <= 0:
            continue

        gap = (u - b) / b * 100

        if abs(gap) < ALERT_GAP:
            continue

        # 쿨타임 체크
        last = last_alert_time.get(coin)
        if last and now - last < timedelta(hours=COOLDOWN_HOURS):
            continue

        direction = "업비트 ↑" if gap > 0 else "빗썸 ↑"

        msg = (
            f"🚨 김프 알림\n"
            f"{coin}\n"
            f"{direction}\n"
            f"업비트: {u:,.0f}원\n"
            f"빗썸: {b:,.0f}원\n"
            f"차이: {gap:.2f}%"
        )

        send_telegram(msg)
        last_alert_time[coin] = now

# ===============================
# 실행
# ===============================
if __name__ == "__main__":
    run()
