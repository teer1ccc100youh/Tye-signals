from flask import Flask
import threading
import os
app = Flask(__name__)
@app.route('/')
def home(): return "Tye is running!"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_web, daemon=True).start()

import requests, time, datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = 8935278631  # your ID - you already found it

print("Tye V4.4 TRIPLE PAIR - LIVE")
print("Pairs: XAU/USD, GBP/USD, GBP/JPY")

def get_gold():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return float(r.json()['price'])
    except:
        try:
            r = requests.get("https://data-asg.goldprice.org/dbXRates/USD", timeout=10)
            return float(r.json()['items'][0]['xauPrice'])
        except:
            return None

def get_forex():
    # GBP based pairs
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=GBP", timeout=10).json()
        gbp_usd = r['rates']['USD']
        gbp_jpy = r['rates']['JPY']
        return gbp_usd, gbp_jpy
    except:
        return None, None

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=10)
        print(f">> Sent: {msg[:30]}...")
    except Exception as e:
        print(f"Telegram fail: {e}")

while True:
    now = datetime.datetime.now().strftime("%H:%M:%S")
    gold = get_gold()
    gbp_usd, gbp_jpy = get_forex()

    # 1. XAU/USD
    if gold:
        if gold > 2680: action, sl, tp = "SELL 🔴", gold+15, gold-35
        elif gold < 2620: action, sl, tp = "BUY 🟢", gold-15, gold+35
        else: action, sl, tp = "WAIT 🟡", gold, gold
        
        print(f"[{now}] XAU/USD ${gold:.2f} - {action}")
        if "WAIT" not in action:
            msg = f"🚨 *TYE GOLD SIGNAL* 🔴\n\n💰 XAU/USD: ${gold:.2f}\n📊 Action: {action}\n🛑 SL: ${sl:.2f}\n🎯 TP: ${tp:.2f}\n⏰ {now} SAST\n\n_Tye V4.4_"
            send_telegram(msg)

    # 2. GBP/USD
    if gbp_usd:
        if gbp_usd > 1.34: action, sl, tp = "SELL 🔴", gbp_usd+0.0030, gbp_usd-0.0060
        elif gbp_usd < 1.30: action, sl, tp = "BUY 🟢", gbp_usd-0.0030, gbp_usd+0.0060
        else: action, sl, tp = "WAIT 🟡", gbp_usd, gbp_usd
        
        print(f"[{now}] GBP/USD {gbp_usd:.5f} - {action}")
        if "WAIT" not in action:
            msg = f"🚨 *TYE GBP/USD SIGNAL* \n\n💷 GBP/USD: {gbp_usd:.5f}\n📊 Action: {action}\n🛑 SL: {sl:.5f}\n🎯 TP: {tp:.5f}\n⏰ {now} SAST\n\n_Tye V4.4_"
            send_telegram(msg)

    # 3. GBP/JPY
    if gbp_jpy:
        if gbp_jpy > 195: action, sl, tp = "SELL 🔴", gbp_jpy+0.50, gbp_jpy-1.00
        elif gbp_jpy < 188: action, sl, tp = "BUY 🟢", gbp_jpy-0.50, gbp_jpy+1.00
        else: action, sl, tp = "WAIT 🟡", gbp_jpy, gbp_jpy

        print(f"[{now}] GBP/JPY {gbp_jpy:.2f} - {action}")
        if "WAIT" not in action:
            msg = f"🚨 *TYE GBP/JPY SIGNAL* \n\n💷 GBP/JPY: {gbp_jpy:.2f}\n📊 Action: {action}\n🛑 SL: {sl:.2f}\n🎯 TP: {tp:.2f}\n⏰ {now} SAST\n\n_Tye V4.4_"
            send_telegram(msg)

    time.sleep(900)
