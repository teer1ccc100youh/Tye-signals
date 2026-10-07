import os
import time
import requests
import yfinance as yf
from threading import Thread
from flask import Flask

# ========== TELEGRAM SETUP ==========
BOT_TOKEN = "8132767542:AAE7j6E3bH-OsF6P5W7XKQvZ1Y2L3M4N5O6"
CHAT_ID = "-1002758391047"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# ========== KEEP ALIVE FOR RENDER ==========
app = Flask('')

@app.route('/')
def home():
    return "Tye V4.6 is Alive!"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# ========== BOT CONFIG ==========
COOLDOWN = 1200 # 20 minutes
SL_PIPS_GOLD = 15.00
SL_PIPS_FX = 0.0020 # 20 pips
RR = 3 # 1:3 Risk to Reward

last_signal_time = {"XAUUSD": 0, "GBPUSD": 0, "GBPJPY": 0}
active_trades = {} # store {pair: {entry, sl, tp, direction}}

# ========== PRICE FETCHER ==========
def get_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            return round(data['Close'][-1], 5)
    except:
        pass
    return None

# ========== TP/SL CHECKER ==========
def check_sl_tp():
    global active_trades
    to_delete = []
    for pair, trade in active_trades.items():
        price = get_price(trade['yf_symbol'])
        if not price: continue
        
        if trade['direction'] == "BUY":
            if price >= trade['tp']:
                send_telegram(f"✅ <b>TYE TP HIT!</b>\n\n💰 {pair}\n🎯 TP: {trade['tp']}\n📈 Profit: 1:3 RR")
                to_delete.append(pair)
            elif price <= trade['sl']:
                send_telegram(f"❌ <b>TYE SL HIT</b>\n\n💰 {pair}\n🛑 SL: {trade['sl']}")
                to_delete.append(pair)
        
        elif trade['direction'] == "SELL":
            if price <= trade['tp']:
                send_telegram(f"✅ <b>TYE TP HIT!</b>\n\n💰 {pair}\n🎯 TP: {trade['tp']}\n📈 Profit: 1:3 RR")
                to_delete.append(pair)
            elif price >= trade['sl']:
                send_telegram(f"❌ <b>TYE SL HIT</b>\n\n💰 {pair}\n🛑 SL: {trade['sl']}")
                to_delete.append(pair)
    
    for pair in to_delete:
        del active_trades[pair]

# ========== SIGNAL LOGIC ==========
def check_pair(pair, yf_symbol, sl_pips):
    global last_signal_time, active_trades
    
    # Cooldown check
    if time.time() - last_signal_time[pair] < COOLDOWN:
        print(f"{pair}: Still in cooldown")
        return
    
    price = get_price(yf_symbol)
    if not price:
        print(f"{pair}: No price")
        return
    
    # FAKE SIGNAL LOGIC - REPLACE WITH YOUR REAL STRATEGY
    # For now we signal every 20min just to test
    # YOU WILL ADD YOUR RSI/MACD/EMA LOGIC HERE
    
    # Randomly pick BUY or SELL for demo
    import random
    direction = random.choice(["BUY", "SELL"])
    
    if direction == "BUY":
        sl = round(price - sl_pips, 5)
        tp = round(price + (sl_pips * RR), 5)
        emoji = "🟢"
        dir_text = "BUY"
    else:
        sl = round(price + sl_pips, 5)
        tp = round(price - (sl_pips * RR), 5)
        emoji = "🔴"
        dir_text = "SELL"
    
    message = f"""{emoji} <b>TYE {dir_text} SIGNAL</b> {emoji}

💰 <b>{pair}</b>
📍 Entry: {price}
🛑 SL: {sl} | Risk
🎯 TP: {tp} | +{(tp-price) if direction=='BUY' else (price-tp):.2f} 1:{RR} RR

⚠️ Manage your risk. Not financial advice."""
    
    send_telegram(message)
    last_signal_time[pair] = time.time()
    active_trades[pair] = {"entry": price, "sl": sl, "tp": tp, "direction": direction, "yf_symbol": yf_symbol}
    print(f"{pair}: {dir_text} signal sent at {price}")

# ========== MAIN LOOP ==========
def main():
    keep_alive()
    send_telegram("🚀 <b>TYE V4.6 LIVE</b>\n\nTriple Pair | 1:3 RR | TP/SL Tracker ON")
    print("Tye V4.6 TRIPLE PAIR - LIVE")
    
    while True:
        check_sl_tp() # Check TP/SL first
        
        check_pair("XAUUSD", "GC=F", SL_PIPS_GOLD)
        check_pair("GBPUSD", "GBPUSD=X", SL_PIPS_FX)
        check_pair("GBPJPY", "GBPJPY=X", SL_PIPS_FX)
        
        time.sleep(60) # Check every 60 seconds

if __name__ == "__main__":
    main()
