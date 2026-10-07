import os
import time
import requests
import yfinance as yf
import pandas as pd
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Tye is Alive!"

def run():
  app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ========== CONFIG ==========
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = "@tyesignalsvip"

def send_telegram_with_id(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.json().get("result", {}).get("message_id")

active_trades = {} # Stores open trades + time for cooldown
COOLDOWN = 1200 # 1200 seconds = 20 MINUTES

print("Tye V4.5 TRIPLE PAIR - LIVE")
print(f"Pairs: XAU/USD, GBP/USD, GBP/JPY | Cooldown: 20min")

# ========== FUNCTIONS ==========
def get_forex(pair):
    try:
        data = yf.Ticker(pair + "=X").history(period="1d", interval="1m")
        return data['Close'].iloc[-1]
    except:
        return None

def get_gold():
    try:
        data = yf.Ticker("XAUUSD=X").history(period="1d", interval="1m")
        return data['Close'].iloc[-1]
    except:
        return None

def check_sl_tp():
    global active_trades
    to_delete = []
    for pair, trade in active_trades.items():
        if pair == "XAUUSD":
            price = get_gold()
        else:
            price = get_forex(pair)
        
        if not price: continue

        action = trade["action"]
        entry = trade["entry"]
        sl = trade["sl"]
        tp = trade["tp"]

        if action == "BUY":
            if price >= tp:
                send_telegram_with_id(f"✅ *TYE TP HIT!* 🚀\n\n💰 {pair}\nEntry: {entry}\nTP: {tp}\nCurrent: {price:.2f}")
                to_delete.append(pair)
            elif price <= sl:
                send_telegram_with_id(f"❌ *TYE SL HIT* 📉\n\n💰 {pair}\nEntry: {entry}\nSL: {sl}\nCurrent: {price:.2f}")
                to_delete.append(pair)
        elif action == "SELL":
            if price <= tp:
                send_telegram_with_id(f"✅ *TYE TP HIT!* 🚀\n\n💰 {pair}\nEntry: {entry}\nTP: {tp}\nCurrent: {price:.2f}")
                to_delete.append(pair)
            elif price >= sl:
                send_telegram_with_id(f"❌ *TYE SL HIT* 📉\n\n💰 {pair}\nEntry: {entry}\nSL: {sl}\nCurrent: {price:.2f}")
                to_delete.append(pair)
    
    for pair in to_delete:
        del active_trades[pair]

def generate_signal(price):
    # Simple RSI + MA strategy
    # Replace this with your real strategy
    if price > 2000: return "SELL"
    if price < 1900: return "BUY"
    return "WAIT"

# ========== MAIN LOOP ==========
keep_alive()

while True:
    try:
        # 1. CHECK SL/TP FIRST
        check_sl_tp()

        # 2. GET PRICES
        xau = get_gold()
        gbp_usd = get_forex("GBPUSD")
        gbp_jpy = get_forex("GBPJPY")

        print(f"Prices: XAU={xau}, GBPUSD={gbp_usd}, GBPJPY={gbp_jpy}")

        # 3. XAUUSD SIGNAL
        if xau:
            action = generate_signal(xau)
            if "WAIT" not in action:
                # 20 MIN COOLDOWN
                if "XAUUSD" in active_trades:
                    if time.time() - active_trades["XAUUSD"]["time"] < COOLDOWN:
                        print("XAUUSD: Still in cooldown")
                    else:
                        sl = xau - 5 if action == "BUY" else xau + 5
                        tp = xau + 10 if action == "BUY" else xau - 10
                        msg = f"🚨 *TYE GOLD SIGNAL* 🔴\n\n💰 XAU/USD: ${xau:.2f}\n📍 Entry: ${xau:.2f}\n🛑 SL: ${sl:.2f}\n🎯 TP: ${tp:.2f}"
                        send_telegram_with_id(msg)
                        active_trades["XAUUSD"] = {"action": action, "entry": xau, "sl": sl, "tp": tp, "time": time.time()}
                else:
                    sl = xau - 5 if action == "BUY" else xau + 5
                    tp = xau + 10 if action == "BUY" else xau - 10
                    msg = f"🚨 *TYE GOLD SIGNAL* 🔴\n\n💰 XAU/USD: ${xau:.2f}\n📍 Entry: ${xau:.2f}\n🛑 SL: ${sl:.2f}\n🎯 TP: ${tp:.2f}"
                    send_telegram_with_id(msg)
                    active_trades["XAUUSD"] = {"action": action, "entry": xau, "sl": sl, "tp": tp, "time": time.time()}

        # 4. GBPUSD SIGNAL
        if gbp_usd:
            action = generate_signal(gbp_usd)
            if "WAIT" not in action:
                # 20 MIN COOLDOWN
                if "GBPUSD" in active_trades:
                    if time.time() - active_trades["GBPUSD"]["time"] < COOLDOWN:
                        print("GBPUSD: Still in cooldown")
                    else:
                        sl = gbp_usd - 0.0020 if action == "BUY" else gbp_usd + 0.0020
                        tp = gbp_usd + 0.0040 if action == "BUY" else gbp_usd - 0.0040
                        msg = f"🚨 *TYE GBP/USD SIGNAL* 🔴\n\n💰 GBP/USD: {gbp_usd:.5f}\n📍 Entry: {gbp_usd:.5f}\n🛑 SL: {sl:.5f}\n🎯 TP: {tp:.5f}"
                        send_telegram_with_id(msg)
                        active_trades["GBPUSD"] = {"action": action, "entry": gbp_usd, "sl": sl, "tp": tp, "time": time.time()}
                else:
                    sl = gbp_usd - 0.0020 if action == "BUY" else gbp_usd + 0.0020
                    tp = gbp_usd + 0.0040 if action == "BUY" else gbp_usd - 0.0040
                    msg = f"🚨 *TYE GBP/USD SIGNAL* 🔴\n\n💰 GBP/USD: {gbp_usd:.5f}\n📍 Entry: {gbp_usd:.5f}\n🛑 SL: {sl:.5f}\n🎯 TP: {tp:.5f}"
                    send_telegram_with_id(msg)
                    active_trades["GBPUSD"] = {"action": action, "entry": gbp_usd, "sl": sl, "tp": tp, "time": time.time()}

        # 5. GBPJPY SIGNAL
        if gbp_jpy:
            action = generate_signal(gbp_jpy)
            if "WAIT" not in action:
                # 20 MIN COOLDOWN
                if "GBPJPY" in active_trades:
                    if time.time() - active_trades["GBPJPY"]["time"] < COOLDOWN:
                        print("GBPJPY: Still in cooldown")
                    else:
                        sl = gbp_jpy - 20 if action == "BUY" else gbp_jpy + 20
                        tp = gbp_jpy + 40 if action == "BUY" else gbp_jpy - 40
                        msg = f"🚨 *TYE GBP/JPY SIGNAL* 🔴\n\n💰 GBP/JPY: {gbp_jpy:.2f}\n📍 Entry: {gbp_jpy:.2f}\n🛑 SL: {sl:.2f}\n🎯 TP: {tp:.2f}"
                        send_telegram_with_id(msg)
                        active_trades["GBPJPY"] = {"action": action, "entry": gbp_jpy, "sl": sl, "tp": tp, "time": time.time()}
                else:
                    sl = gbp_jpy - 20 if action == "BUY" else gbp_jpy + 20
                    tp = gbp_jpy + 40 if action == "BUY" else gbp_jpy - 40
                    msg = f"🚨 *TYE GBP/JPY SIGNAL* 🔴\n\n💰 GBP/JPY: {gbp_jpy:.2f}\n📍 Entry: {gbp_jpy:.2f}\n🛑 SL: {sl:.2f}\n🎯 TP: {tp:.2f}"
                    send_telegram_with_id(msg)
                    active_trades["GBPJPY"] = {"action": action, "entry": gbp_jpy, "sl": sl, "tp": tp, "time": time.time()}

        time.sleep(60) # Wait 1 minute

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(60)
