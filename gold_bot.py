import os, time, requests, yfinance as yf, pandas as pd
from flask import Flask
from threading import Thread
import ta

app = Flask('')
@app.route('/')
def home():
    return "Tye V5.0 LIVE - EMA 9/21 + MA 8/50"

def run():
  app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("✅ Flask keep_alive started")

# ========== CONFIG ==========
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = "@tyesignalsvip"
RR = 4
COOLDOWN = 600

if not TELEGRAM_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not set in Render Env Vars!")
else:
    print(f"✅ Token found: {TELEGRAM_TOKEN[:10]}...")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"Telegram sent: {r.status_code}")
        return r.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"Telegram error: {e}")
        return None

active_trades = {}
print(f"🔥 Tye V5.0 LIVE | EMA 9/21 + MA 8/50 + RSI | 1:{RR} RR | Checking XAU, GU, GJ")

def get_data(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2d", interval="5m")
        if len(df) < 60:
            print(f"{symbol}: only {len(df)} candles")
            return None
        return df
    except Exception as e:
        print(f"get_data {symbol} error: {e}")
        return None

def check_strategy(df):
    try:
        close = df['Close']
        ema9 = ta.trend.EMAIndicator(close, window=9).ema_indicator()
        ema21 = ta.trend.EMAIndicator(close, window=21).ema_indicator()
        ma8 = ta.trend.SMAIndicator(close, window=8).sma_indicator()
        ma50 = ta.trend.SMAIndicator(close, window=50).sma_indicator()
        rsi = ta.momentum.RSIIndicator(close, window=14).rsi()
        
        curr_ema9 = ema9.iloc[-1]
        curr_ema21 = ema21.iloc[-1]
        prev_ema9 = ema9.iloc[-2]
        prev_ema21 = ema21.iloc[-2]
        curr_ma8 = ma8.iloc[-1]
        curr_ma50 = ma50.iloc[-1]
        curr_rsi = rsi.iloc[-1]
        price = close.iloc[-1]

        if prev_ema9 <= prev_ema21 and curr_ema9 > curr_ema21:
            if curr_ma8 > curr_ma50 and 45 < curr_rsi < 72:
                return "BUY", price
        if prev_ema9 >= prev_ema21 and curr_ema9 < curr_ema21:
            if curr_ma8 < curr_ma50 and 28 < curr_rsi < 55:
                return "SELL", price
        return "WAIT", price
    except Exception as e:
        print(f"check_strategy error: {e}")
        return "WAIT", None

# ========== START ==========
keep_alive()
time.sleep(2)

# SEND TEST THAT SHE IS ALIVE
send_telegram("🚀 *TYE V5.0 RESTARTED*\n\n✅ EMA 9/21 + MA 8/50 + RSI\n✅ XAUUSD + GBPUSD + GBPJPY\n✅ 1:4 RR\n\nWatching market...")

while True:
    try:
        pairs = [("XAUUSD","GC=F",15.0), ("GBPUSD","GBPUSD=X",0.0020), ("GBPJPY","GBPJPY=X",0.20)]
        for pair_name, symbol, sl_pips in pairs:
            if pair_name in active_trades:
                if time.time() - active_trades[pair_name]["time"] < COOLDOWN:
                    continue
            df = get_data(symbol)
            action, price = check_strategy(df)
            if price:
                print(f"{pair_name}: {price:.2f} | {action} | RSI check")
            if action != "WAIT" and price:
                if action == "BUY":
                    sl = price - sl_pips
                    tp = price + (sl_pips * RR)
                    emoji = "🟢"
                else:
                    sl = price + sl_pips
                    tp = price - (sl_pips * RR)
                    emoji = "🔴"
                
                if pair_name == "XAUUSD":
                    msg = f"🚨 *TYE GOLD {action} SIGNAL* {emoji}\n\n💰 XAU/USD: ${price:.2f}\n📍 Entry: ${price:.2f}\n📊 {action} - EMA 9/21 + MA 8/50 + RSI\n🛑 SL: ${sl:.2f}\n🎯 TP: ${tp:.2f} | *1:{RR} RR*"
                elif pair_name == "GBPUSD":
                    msg = f"🚨 *TYE GBP/USD {action} SIGNAL* {emoji}\n\n💰 GBP/USD: {price:.5f}\n📊 {action}\n🛑 SL: {sl:.5f}\n🎯 TP: {tp:.5f} | *1:{RR} RR*"
                else:
                    msg = f"🚨 *TYE GBP/JPY {action} SIGNAL* {emoji}\n\n💰 GBP/JPY: {price:.2f}\n📊 {action}\n🛑 SL: {sl:.2f}\n🎯 TP: {tp:.2f} | *1:{RR} RR*"
                
                send_telegram(msg)
                active_trades[pair_name] = {"action": action, "entry": price, "sl": sl, "tp": tp, "time": time.time()}
        time.sleep(60)
    except Exception as e:
        print(f"MAIN LOOP ERROR: {e}")
        time.sleep(60)
