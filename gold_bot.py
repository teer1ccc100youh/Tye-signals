import os
import time
import requests
import yfinance as yf
import pandas as pd
from flask import Flask
from threading import Thread
import ta

app = Flask('')
@app.route('/')
def home():
    return "Tye V4.9 FINAL - EMA 9/21 + MA 8/50 + RSI + 1:4 RR"

def run():
  app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ========== CONFIG ==========
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = "@tyesignalsvip"
RR = 4 # 1:4 as you said

def send_telegram_with_id(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"Telegram error: {e}")
        return None

active_trades = {}
COOLDOWN = 1200

print(f"Tye V4.9 LIVE | EMA 9/21 + MA 8/50 + RSI | 1:{RR} RR")

# ========== DATA FUNCTIONS ==========
def get_data(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2d", interval="5m")
        if len(df) < 60:
            return None
        return df
    except:
        return None

def check_strategy(df):
    """FINAL STRATEGY: EMA 9/21 + MA 8/50 + RSI"""
    if df is None or len(df) < 60:
        return "WAIT", None

    close = df['Close']

    # Your indicators
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

    # BUY: EMA9 crossed above EMA21 AND MA8 above MA50 AND RSI 50-68
    if prev_ema9 <= prev_ema21 and curr_ema9 > curr_ema21:
        if curr_ma8 > curr_ma50 and 50 < curr_rsi < 68 and price > curr_ma50:
            return "BUY", price

    # SELL: EMA9 crossed below EMA21 AND MA8 below MA50 AND RSI 32-50
    if prev_ema9 >= prev_ema21 and curr_ema9 < curr_ema21:
        if curr_ma8 < curr_ma50 and 32 < curr_rsi < 50 and price < curr_ma50:
            return "SELL", price

    return "WAIT", price

def check_sl_tp():
    global active_trades
    to_delete = []
    for pair, trade in active_trades.items():
        symbol = "GC=F" if pair == "XAUUSD" else pair + "=X"
        df = get_data(symbol)
        if df is None: continue
        price = df['Close'].iloc[-1]

        action = trade["action"]
        if action == "BUY":
            if price >= trade["tp"]:
                send_telegram_with_id(f"✅ *TYE TP HIT 1:{RR}!* 🚀\n\n💰 {pair} {action}\nProfit: +{RR}R")
                to_delete.append(pair)
            elif price <= trade["sl"]:
                send_telegram_with_id(f"❌ *TYE SL HIT* {pair} {action}")
                to_delete.append(pair)
        else: # SELL
            if price <= trade["tp"]:
                send_telegram_with_id(f"✅ *TYE TP HIT 1:{RR}!* 🚀\n\n💰 {pair} {action}\nProfit: +{RR}R")
                to_delete.append(pair)
            elif price >= trade["sl"]:
                send_telegram_with_id(f"❌ *TYE SL HIT* {pair} {action}")
                to_delete.append(pair)

    for pair in to_delete:
        del active_trades[pair]

# ========== MAIN LOOP ==========
keep_alive()

while True:
    try:
        check_sl_tp()

        # ALL 3 PAIRS WITH NEW STRATEGY
        pairs = [
            ("XAUUSD", "GC=F", 15.0),
            ("GBPUSD", "GBPUSD=X", 0.0020),
            ("GBPJPY", "GBPJPY=X", 0.20) # FIXED! was 20
        ]

        for pair_name, symbol, sl_pips in pairs:
            # Cooldown check
            if pair_name in active_trades:
                if time.time() - active_trades[pair_name]["time"] < COOLDOWN:
                    print(f"{pair_name}: Cooldown")
                    continue

            df = get_data(symbol)
            action, price = check_strategy(df)

            if price:
                print(f"{pair_name}: {price:.2f} | {action}")

            if "WAIT" not in action:
                # 1:4 RR CALCULATION
                if action == "BUY":
                    sl = price - sl_pips
                    tp = price + (sl_pips * RR)
                    emoji = "🟢"
                else:
                    sl = price + sl_pips
                    tp = price - (sl_pips * RR)
                    emoji = "🔴"

                if pair_name == "XAUUSD":
                    msg = f"🚨 *TYE GOLD {action} SIGNAL* {emoji}\n\n💰 XAU/USD: ${price:.2f}\n📍 Entry: ${price:.2f}\n📊 *{action} - EMA 9/21 + MA 8/50 + RSI*\n🛑 SL: ${sl:.2f}\n🎯 TP: ${tp:.2f} | *1:{RR} RR*\n\n⚠️ VIP Group"
                elif pair_name == "GBPUSD":
                    msg = f"🚨 *TYE GBP/USD {action} SIGNAL* {emoji}\n\n💰 GBP/USD: {price:.5f}\n📊 *{action}*\n🛑 SL: {sl:.5f}\n🎯 TP: {tp:.5f} | *1:{RR} RR*"
                else:
                    msg = f"🚨 *TYE GBP/JPY {action} SIGNAL* {emoji}\n\n💰 GBP/JPY: {price:.2f}\n📊 *{action}*\n🛑 SL: {sl:.2f}\n🎯 TP: {tp:.2f} | *1:{RR} RR*"

                send_telegram_with_id(msg)
                active_trades[pair_name] = {"action": action, "entry": price, "sl": sl, "tp": tp, "time": time.time()}

        time.sleep(60)

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(60)
