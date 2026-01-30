import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# =========================
# 환경변수
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("환경변수 BOT_TOKEN 또는 CHAT_ID가 설정되지 않았습니다.")

# =========================
# 코인 설정
# =========================
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

EXCLUDE_COINS = {"FLOW", "BTT"}
TOP_N = 10  # 상위/하위 표시 개수

# =========================
# 가격 조회
# =========================
def get_upbit_price(symbol):
    try:
        r = requests.get("https://api.upbit.com/v1/ticker", params={"markets": f"KRW-{symbol}"}, timeout=5).json()
        return float(r[0]["trade_price"])
    except:
        return None

def get_bithumb_price(symbol):
    try:
        r = requests.get(f"https://api.bithumb.com/public/ticker/{symbol}_KRW", timeout=5).json()
        return float(r["data"]["closing_price"])
    except:
        return None

# =========================
# 텔레그램 전송
# =========================
def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print(f"[ERROR] 텔레그램 전송 실패: {e}")

# =========================
# 코인 비교
# =========================
def fetch_coin(coin):
    if coin in EXCLUDE_COINS:
        return None
    up = get_upbit_price(coin)
    bi = get_bithumb_price(coin)
    if up is None or bi is None:
        return None
    diff = ((up - bi) / bi) * 100
    return (coin, up, bi, diff)

def compare_all():
    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_coin, coin): coin for coin in COINS}
        for f in as_completed(futures):
            res = f.result()
            if res:
                results.append(res)

    upbit_higher = sorted([r for r in results if r[3] > 0], key=lambda x: x[3], reverse=True)[:TOP_N]
    bithumb_higher = sorted([r for r in results if r[3] < 0], key=lambda x: x[3])[:TOP_N]

    def format_msg(title, data):
        msg = f"{title}\n"
        for c, up, bi, diff in data:
            msg += f"{c}: 업 {up:,} / 빗 {bi:,} / 차이 {diff:.2f}%\n"
        return msg

    if upbit_higher:
        send_telegram(format_msg("📈 업비트가 높은 코인 TOP10", upbit_higher))
    if bithumb_higher:
        send_telegram(format_msg("📉 빗썸이 높은 코인 TOP10", bithumb_higher))

    print("텔레그램 메시지 전송 완료 ✅")

# =========================
# 실행
# =========================
if __name__ == "__main__":
    compare_all()
