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
    return "Tye V4.8 is Alive! EMA Strategy + 1:4 RR"

def run():
  app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ========== CONFIG ==========
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = "@tyesignalsvip"
RR = 4 # 1:4 YOU ASKED FOR 1/4

def send_telegram_with_id(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.json().get("result", {}).get("message_id")

active_trades = {}
COOLDOWN = 1200 # 20 MINUTES

print("Tye V4.8 TRIPLE PAIR - LIVE EMA STRATEGY")
print(f"Pairs: XAU/USD, GBP/USD, GBP/JPY | Cooldown: 20min | RR: 1:{RR}")

# ========== FUNCTIONS ==========
def get_forex(pair):
    try:
        data = yf.Ticker(pair + "=X").history(period="1d", interval="1m")
        return data['Close'].iloc[-1]
    except:
        return None

def get_gold():
    try:
        # Use GC=F for better data, fallback to XAUUSD=X
        data = yf.Ticker("GC=F").history(period="2d", interval="5m")
        if data.empty:
            data = yf.Ticker("XAUUSD=X").history(period="1d", interval="1m")
        return data
    except:
        return None

def get_forex_data(pair):
    try:
        data = yf.Ticker(pair + "=X").history(period="2d", interval="5m")
        return data
    except:
        return None

def check_strategy(df):
    """EMA 9/21 Crossover + MA50 + RSI - YOUR STRATEGY TWIN"""
    try:
        if df is None or len(df) < 60:
            return "WAIT", None

        close = df['Close']
        ema9 = ta.trend.EMAIndicator(close, window=9).ema_indicator()
        ema21 = ta.trend.EMAIndicator(close, window=21).ema_indicator()
        ma50 = ta.trend.SMAIndicator(close, window=50).sma_indicator()
        rsi = ta.momentum.RSIIndicator(close, window=14).rsi()

        curr_ema9 = ema9.iloc[-1]
        curr_ema21 = ema21.iloc[-1]
        prev_ema9 = ema9.iloc[-2]
        prev_ema21 = ema21.iloc[-2]
        curr_ma50 = ma50.iloc[-1]
        curr_rsi = rsi.iloc[-1]
        price = close.iloc[-1]

        # BUY: EMA9 crossed above EMA21 + price above MA50 + RSI 50-70
        if prev_ema9 <= prev_ema21 and curr_ema9 > curr_ema21 and price > curr_ma50 and 50 < curr_rsi < 70:
            return "BUY", price

        # SELL: EMA9 crossed below EMA21 + price below MA50 + RSI 30-50
        if prev_ema9 >= prev_ema21 and curr_ema9 < curr_ema21 and price < curr_ma50 and 30 < curr_rsi < 50:
            return "SELL", price

        return "WAIT", price
    except Exception as e:
        print(f"Strategy error: {e}")
        return "WAIT", None

def check_sl_tp():
    global active_trades
    to_delete = []
    for pair, trade in active_trades.items():
        if pair == "XAUUSD":
            df = get_gold()
            price = df['Close'].iloc[-1] if df is not None and not df.empty else None
        else:
            price = get_forex(pair)

        if not price: continue

        action = trade["action"]
        entry = trade["entry"]
        sl = trade["sl"]
        tp = trade["tp"]

        if action == "BUY":
            if price >= tp:
                send_telegram_with_id(f"✅ *TYE TP HIT!* 🚀\n\n💰 {pair} {action}\nEntry: {entry}\nTP: {tp}\n1:{RR} RR WIN!")
                to_delete.append(pair)
            elif price <= sl:
                send_telegram_with_id(f"❌ *TYE SL HIT* 📉\n\n💰 {pair} {action}\nEntry: {entry}\nSL: {sl}")
                to_delete.append(pair)
        elif action == "SELL":
            if price <= tp:
                send_telegram_with_id(f"✅ *TYE TP HIT!* 🚀\n\n💰 {pair} {action}\nEntry: {entry}\nTP: {tp}\n1:{RR} RR WIN!")
                to_delete.append(pair)
            elif price >= sl:
                send_telegram_with_id(f"❌ *TYE SL HIT* 📉\n\n💰 {pair} {action}\nEntry: {entry}\nSL: {sl}")
                to_delete.append(pair)

    for pair in to_delete:
        del active_trades[pair]

# ========== MAIN LOOP ==========
keep_alive()

while True:
    try:
        check_sl_tp()

        # GET DATA FOR STRATEGY
        xau_df = get_gold()
        gbp_usd_df = get_forex_data("GBPUSD")
        gbp_jpy_df = get_forex_data("GBPJPY")

        # CURRENT PRICES
        xau_price = xau_df['Close'].iloc[-1] if xau_df is not None and not xau_df.empty else get_forex("XAUUSD")
        gbp_usd_price = gbp_usd_df['Close'].iloc[-1] if gbp_usd_df is not None and not gbp_usd_df.empty else get_forex("GBPUSD")
        gbp_jpy_price = gbp_jpy_df['Close'].iloc[-1] if gbp_jpy_df is not None and not gbp_jpy_df.empty else get_forex("GBPJPY")

        print(f"Prices: XAU={xau_price}, GBPUSD={gbp_usd_price}, GBPJPY={gbp_jpy_price}")

        # 3. XAUUSD SIGNAL - 1:4 RR
        if xau_df is not None:
            action, price = check_strategy(xau_df)
            if "WAIT" not in action:
                if "XAUUSD" in active_trades:
                    if time.time() - active_trades["XAUUSD"]["time"] < COOLDOWN:
                        print("XAUUSD: Still in cooldown")
                    else:
                        sl = price - 15 if action == "BUY" else price + 15
                        tp = price + (15*RR) if action == "BUY" else price - (15*RR)
                        emoji = "🟢" if action == "BUY" else "🔴"
                        msg = f"🚨 *TYE GOLD {action} SIGNAL* {emoji}\n\n💰 XAU/USD: ${price:.2f}\n📍 Entry: ${price:.2f}\n📊 *DIRECTION: {action}*\n🛑 SL: ${sl:.2f}\n🎯 TP: ${tp:.2f} | 1:{RR} RR\n\n⚡ Strategy: EMA 9/21 + MA50"
                        send_telegram_with_id(msg)
                        active_trades["XAUUSD"] = {"action": action, "entry": price, "sl": sl, "tp": tp, "time": time.time()}
                else:
                    sl = price - 15 if action == "BUY" else price + 15
                    tp = price + (15*RR) if action == "BUY" else price - (15*RR)
                    emoji = "🟢" if action == "BUY" else "🔴"
                    msg = f"🚨 *TYE GOLD {action} SIGNAL* {emoji}\n\n💰 XAU/USD: ${price:.2f}\n📍 Entry: ${price:.2f}\n📊 *DIRECTION: {action}*\n🛑 SL: ${sl:.2f}\n🎯 TP: ${tp:.2f} | 1:{RR} RR\n\n⚡ Strategy: EMA 9/21 + MA50"
                    send_telegram_with_id(msg)
                    active_trades["XAUUSD"] = {"action": action, "entry": price, "sl": sl, "tp": tp, "time": time.time()}

        # 4. GBPUSD SIGNAL - 1:4 RR
        if gbp_usd_df is not None:
            action, price = check_strategy(gbp_usd_df)
            if "WAIT" not in action:
                if "GBPUSD" in active_trades:
                    if time.time() - active_trades["GBPUSD"]["time"] < COOLDOWN:
                        print("GBPUSD: Still in cooldown")
                    else:
                        sl = price - 0.0020 if action == "BUY" else price + 0.0020
                        tp = price + (0.0020*RR) if action == "BUY" else price - (0.0020*RR)
                        emoji = "🟢" if action == "BUY" else "🔴"
                        msg = f"🚨 *TYE GBP/USD {action} SIGNAL* {emoji}\n\n💰 GBP/USD: {price:.5f}\n📍 Entry: {price:.5f}\n📊 *DIRECTION: {action}*\n🛑 SL: {sl:.5f}\n🎯 TP: {tp:.5f} | 1:{RR} RR"
                        send_telegram_with_id(msg)
                        active_trades["GBPUSD"] = {"action": action, "entry": price, "sl": sl, "tp": tp, "time": time.time()}
                else:
                    sl = price - 0.0020 if action == "BUY" else price + 0.0020
                    tp = price + (0.0020*RR) if action == "BUY" else price - (0.0020*RR)
                    emoji = "🟢" if action == "BUY" else "🔴"
                    msg = f"🚨 *TYE GBP/USD {action} SIGNAL* {emoji}\n\n💰 GBP/USD: {price:.5f}\n📍 Entry: {price:.5f}\n📊 *DIRECTION: {action}*\n🛑 SL: {sl:.5f}\n🎯 TP: {tp:.5f} | 1:{RR} RR"
                    send_telegram_with_id(msg)
                    active_trades["GBPUSD"] = {"action": action, "entry": price, "sl": sl, "tp": tp, "time": time.time()}

        # 5. GBPJPY SIGNAL - FIXED PIPS + 1:4 RR
        if gbp_jpy_df is not None:
            action, price = check_strategy(gbp_jpy_df)
            if "WAIT" not in action:
                if "GBPJPY" in active_trades:
                    if time.time() - active_trades["GBPJPY"]["time"] < COOLDOWN:
                        print("GBPJPY: Still in cooldown")
                    else:
                        sl = price - 0.20 if action == "BUY" else price + 0.20
                        tp = price + (0.20*RR) if action == "BUY" else price - (0.20*RR)
                        emoji = "🟢" if action == "BUY" else "🔴"
                        msg = f"🚨 *TYE GBP/JPY {action} SIGNAL* {emoji}\n\n💰 GBP/JPY: {price:.2f}\n📍 Entry: {price:.2f}\n📊 *DIRECTION: {action}*\n🛑 SL: {sl:.2f}\n🎯 TP: {tp:.2f} | 1:{RR} RR"
                        send_telegram_with_id(msg)
                        active_trades["GBPJPY"] = {"action": action, "entry": price, "sl": sl, "tp": tp, "time": time.time()}
                else:
                    sl = price - 0.20 if action == "BUY" else price + 0.20
                    tp = price + (0.20*RR) if action == "BUY" else price - (0.20*RR)
                    emoji = "🟢" if action == "BUY" else "🔴"
                    msg = f"🚨 *TYE GBP/JPY {action} SIGNAL* {emoji}\n\n💰 GBP/JPY: {price:.2f}\n📍 Entry: {price:.2f}\n📊 *DIRECTION: {action}*\n🛑 SL: {sl:.2f}\n🎯 TP: {tp:.2f} | 1:{RR} RR"
                    send_telegram_with_id(msg)
                    active_trades["GBPJPY"] = {"action": action, "entry": price, "sl": sl, "tp": tp, "time": time.time()}

        time.sleep(60)

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(60)
