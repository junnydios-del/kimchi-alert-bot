import requests

# =========================
# 설정
# =========================
TELEGRAM_TOKEN = "너의_텔레그램_봇_토큰"
CHAT_ID = "너의_채팅_ID"

THRESHOLD = 2.0  # 2%

# 업비트 ↔ 빗썸 공통 코인 (232개)
COINS = [
"0G","1INCH","2Z","A","AAVE","ADA","AERGO","AERO","AGLD","AHT","AKT","ALGO",
"ALT","ANIME","ANKR","API3","APT","AQT","ARB","ARDR","ARK","ARKM","ASTR",
"ATH","ATOM","AUCTION","AVAX","AVNT","AWE","AXS","BARD","BAT","BCH","BEAM",
"BERA","BIGTIME","BIO","BLAST","BLUR","BONK","BORA","BOUNTY","BREV","BSV",
"BTC","BTT","CARV","CBK","CELO","CHZ","CKB","COMP","COW","CPOOL","CRO",
"CTC","CVC","CYBER","DEEP","DKA","DOGE","DOOD","DOT","DRIFT","EGLD","ELF",
"ENA","ENS","ENSO","ERA","ETC","ETH","F","FCT2","FF","FIL","FLOCK","FLOW",
"FLUID","G","GAME2","GAS","GLM","GMT","GRT","HBAR","HIVE","HOLO","HP","HUNT",
"HYPER","ICX","ID","IMX","IN","INJ","IOST","IOTA","IP","IQ","JST","JTO",
"JUP","KAITO","KAVA","KERNEL","KITE","KNC","LA","LAYER","LINEA","LINK","LPT",
"LSK","MANA","MASK","MBL","ME","MED","META","MEW","MINA","MIRA","MLK","MMT",
"MNT","MOC","MOCA","MON","MOODENG","MOVE","MTL","MVL","NEAR","NEO","NEWT",
"NOM","NXPC","OM","ONDO","ONG","ONT","OP","OPEN","ORBS","ORCA","ORDER",
"PENDLE","PENGU","PEPE","PLUME","POKT","POL","POLYX","POWR","PROVE","PUMP",
"PUNDIX","PYTH","QKC","QTUM","RAY","RED","RENDER","RVN","SAFE","SAHARA",
"SAND","SC","SEI","SHIB","SIGN","SNT","SOL","SOMI","SONIC","SOPH","STEEM",
"STG","STORJ","STRAX","STX","SUI","SUN","SUPER","SXP","SYRUP","T","TAIKO",
"TFUEL","THETA","TIA","TOKAMAK","TOSHI","TREE","TRUMP","TRUST","TRX","TT",
"UNI","USD1","USDC","USDE","USDT","VANA","VET","VIRTUAL","VTHO","W","WAL",
"WAVES","WAXP","WCT","WET","WLD","WLFI","XAUT","XEC","XLM","XPL","XRP",
"XTZ","YGG","ZBT","ZETA","ZIL","ZK","ZKC","ZKP","ZORA","ZRO","ZRX"
]

# 제외 코인
EXCLUDE_COINS = {"FLOW", "BTT"}

# =========================
# 텔레그램
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    })

# =========================
# 가격 조회 (실패 시 None)
# =========================
def get_upbit(symbol):
    try:
        r = requests.get(
            "https://api.upbit.com/v1/ticker",
            params={"markets": f"KRW-{symbol}"},
            timeout=5
        ).json()
        return r[0]["trade_price"]
    except:
        return None

def get_bithumb(symbol):
    try:
        r = requests.get(
            f"https://api.bithumb.com/public/ticker/{symbol}_KRW",
            timeout=5
        ).json()
        return float(r["data"]["closing_price"])
    except:
        return None

# =========================
# 메인 로직
# =========================
def run():
    for coin in COINS:
        if coin in EXCLUDE_COINS:
            continue

        upbit = get_upbit(coin)
        bithumb = get_bithumb(coin)

        # 한쪽이라도 없으면 스킵
        if upbit is None or bithumb is None:
            continue

        diff = (upbit - bithumb) / bithumb * 100

        if abs(diff) >= THRESHOLD:
            high = "업비트 🔺" if diff > 0 else "빗썸 🔺"

            msg = (
                f"🚨 <b>{coin}</b>\n"
                f"업비트: {upbit:,}원\n"
                f"빗썸: {bithumb:,}원\n"
                f"차이: {diff:.2f}%\n"
                f"비싼 곳: <b>{high}</b>"
            )

            send_telegram(msg)

# =========================
if __name__ == "__main__":
    run()
