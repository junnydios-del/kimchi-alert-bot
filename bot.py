import requests
import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

COINS = [
    {"name":"세이프","symbol":"SAFE"}, {"name":"체인바운티","symbol":"BOUNTY"},
    {"name":"10 메탈","symbol":"MTL"}, {"name":"브레비스","symbol":"BREV"},
    {"name":"카이토","symbol":"KAITO"}, {"name":"골렘","symbol":"GLM"},
    {"name":"지케이싱크","symbol":"ZK"}, {"name":"폴카닷","symbol":"DOT"},
    {"name":"옵티미즘","symbol":"OP"}, {"name":"칠리즈","symbol":"CHZ"},
    {"name":"아반티스","symbol":"AVNT"}, {"name":"펌프닷펀","symbol":"PUMP"},
    {"name":"아카시 네트워크","symbol":"AKT"}, {"name":"모나드","symbol":"MON"},
    {"name":"캣인어독스월드","symbol":"MEW"}, {"name":"테더 골드","symbol":"XAUT"},
    {"name":"리스크","symbol":"LSK"}, {"name":"딥북","symbol":"DEEP"},
    {"name":"앱토스","symbol":"APT"}, {"name":"오브스","symbol":"ORBS"},
    {"name":"미나","symbol":"MINA"}, {"name":"휴미디파이","symbol":"WET"},
    {"name":"질리카","symbol":"ZIL"}, {"name":"렌더토큰","symbol":"RENDER"},
    {"name":"플룸","symbol":"PLUME"}, {"name":"너보스","symbol":"CKB"},
    {"name":"플록","symbol":"FLOCK"}, {"name":"소폰","symbol":"SOPH"},
    {"name":"매직 에덴","symbol":"ME"}, {"name":"폴리매쉬","symbol":"POLYX"},
    {"name":"제로지","symbol":"OG"}, {"name":"에이브","symbol":"AAVE"},
    {"name":"온톨로지","symbol":"ONT"}, {"name":"베라체인","symbol":"BERA"},
    {"name":"사하라에이아이","symbol":"SAHARA"}, {"name":"마스크네트워크","symbol":"MASK"},
    {"name":"크레딧코인","symbol":"CTC"}, {"name":"카우 프로토콜","symbol":"COW"},
    {"name":"아캄","symbol":"ARKM"}, {"name":"신퓨처스","symbol":"F"},
    {"name":"아크","symbol":"ARK"}, {"name":"애니메코인","symbol":"ANIME"},
    {"name":"월러스","symbol":"WAL"}, {"name":"하이퍼레인","symbol":"HYPER"},
    {"name":"에이셔","symbol":"ATH"}, {"name":"카브","symbol":"CARV"},
    {"name":"셀레스티아","symbol":"TIA"}, {"name":"카이버 네트워크","symbol":"KNC"},
    {"name":"스토리지","symbol":"STORJ"}, {"name":"엘프","symbol":"ELF"}
]

LAST_FILE = "last_diff.json"
ALERTED_FILE = "alerted.json"

def get_upbit_price(symbol):
    try:
        res = requests.get(f"https://api.upbit.com/v1/ticker?markets=KRW-{symbol}", timeout=10)
        return res.json()[0]["trade_price"]
    except:
        return None

def get_bithumb_price(symbol):
    try:
        res = requests.get(f"https://api.bithumb.com/public/ticker/{symbol}_KRW", timeout=10)
        return float(res.json()["data"]["closing_price"])
    except:
        return None

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message})

def price_watcher():
    last_diff = {}
    alerts = []

    try:
        with open(ALERTED_FILE,"r") as f:
            alerted = json.load(f)
    except:
        alerted = {}

    for coin in COINS:
        upbit = get_upbit_price(coin["symbol"])
        bithumb = get_bithumb_price(coin["symbol"])
        if upbit is None or bithumb is None:
            continue
        diff = (bithumb - upbit) / upbit * 100
        last_diff[coin["symbol"]] = {"upbit": upbit, "bithumb": bithumb, "diff_percent": diff}

        if abs(diff) >= 2 and alerted.get(coin["symbol"]) != round(diff,2):
            alerts.append(f"📌 {coin['name']} ({coin['symbol']})\nUpbit: {upbit} KRW\nBithumb: {bithumb} KRW\n차이: {diff:+.2f}%")
            alerted[coin["symbol"]] = round(diff,2)

    with open(LAST_FILE,"w") as f:
        json.dump(last_diff,f)
    with open(ALERTED_FILE,"w") as f:
        json.dump(alerted,f)

    if alerts:
        send_telegram("\n\n".join(alerts))

# 텔레그램 /recent_diff
async def recent_diff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(LAST_FILE,"r") as f:
            last_data = json.load(f)
        message = "📊 마지막 조회 시점 업비트/빗썸 가격 차이\n\n"
        for coin, data in last_data.items():
            sign = "+" if data["diff_percent"] >= 0 else ""
            message += f"{coin}: Upbit {data['upbit']} KRW / Bithumb {data['bithumb']} KRW ({sign}{data['diff_percent']:.2f}%)\n"
        await update.message.reply_text(message)
    except:
        await update.message.reply_text("마지막 조회 데이터가 없습니다.")

if __name__ == "__main__":
    price_watcher()  # GitHub Actions 실행 시 시세 감시
    # 텔레그램 봇
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("recent_diff", recent_diff))
    app.run_polling()
