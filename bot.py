import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# =========================
# 설정
# =========================
TELEGRAM_TOKEN = "여기에_텔레그램_봇_토큰"
CHAT_ID = "여기에_채팅_ID"

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

EXCLUDE_COINS = {"FLOW","BTT"}

# =========================
# 텔레그램 전송
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    })

# =========================
# 가격 조회 (업비트 / 빗썸)
# =========================
def get_prices(coin):
    if coin in EXCLUDE_COINS:
        return None

    try:
        up = requests.get("https://api.upbit.com/v1/ticker",
                          params={"markets": f"KRW-{coin}"}, timeout=5).json()[0]["trade_price"]
    except:
        up = None

    try:
        bi = float(requests.get(f"https://api.bithumb.com/public/ticker/{coin}_KRW", timeout=5).json()["data"]["closing_price"])
    except:
        bi = None

    if up is None or bi is None:
        return None

    diff = (up - bi) / bi * 100
    return (coin, up, bi, diff)

# =========================
# 메인 비교 및 정렬
# =========================
def compare_top10():
    upbit_higher = []
    bithumb_higher = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(get_prices, coin): coin for coin in COINS}
        for f in as_completed(futures):
            result = f.result()
            if result is None:
                continue
            coin, up, bi, diff = result
            if diff > 0:
                upbit_higher.append(result)
            elif diff < 0:
                bithumb_higher.append(result)

    # 정렬
    upbit_higher.sort(key=lambda x: x[3], reverse=True)
    bithumb_higher.sort(key=lambda x: x[3])

    # 메시지 생성
    msg = "<b>===== 업비트가 비싼 상위 10코인 =====</b>\n"
    for c, up, bi, diff in upbit_higher[:10]:
        msg += f"{c}: 업비트 {up:,}원 / 빗썸 {bi:,}원 / 차이 {diff:.2f}%\n"

    msg += "\n<b>===== 빗썸이 비싼 상위 10코인 =====</b>\n"
    for c, up, bi, diff in bithumb_higher[:10]:
        msg += f"{c}: 업비트 {up:,}원 / 빗썸 {bi:,}원 / 차이 {diff:.2f}%\n"

    send_telegram(msg)
    print("텔레그램 메시지 전송 완료 ✅")

# =========================
# 실행
# =========================
if __name__ == "__main__":
    compare_top10()
