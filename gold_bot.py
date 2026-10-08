import os, time, requests, yfinance as yf
from flask import Flask
from threading import Thread
import ta
from datetime import datetime, timezone

app = Flask('')
@app.route('/')
def home():
    return "Tye V5.5 LIVE - 5 PAIRS - 15MIN - WINRATE"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("✅ Flask keep_alive started")

# ========== CONFIG - YOUR COMMANDS ==========
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = "@tyesignalsvip"
RR = 4  # Your 1:4
COOLDOWN = 900  # Your 15 min - not 1 hour

PAIRS = {
    "XAUUSD": ("GC=F", 15.0),        # $15 SL
    "GBPUSD": ("GBPUSD=X", 0.0020),   # 20 pips
    "GBPJPY": ("GBPJPY=X", 0.20),     # 20 pips
    "EURUSD": ("EURUSD=X", 0.0020),   # NEW - 20 pips
    "USDJPY": ("USDJPY=X", 0.20)      # NEW - 20 pips
}

# NEVER DELETE - history kept per your command
active_trades = {k: [] for k in PAIRS}
last_signal_time = {}
last_daily_report_date = None

def fmt(price, pair):
    if pair in ["GBPUSD", "EURUSD"]:
        return f"{price:.5f}"
    return f"{price:.2f}"

def send_telegram(message):
    if not TELEGRAM_TOKEN:
        print("No token")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"TG error {e}")

def get_data(symbol):
    try:
        df = yf.Ticker(symbol).history(period="2d", interval="5m")
        if df is None or len(df) < 60:
            return None
        return df
    except Exception as e:
        print(f"data {symbol} {e}")
        return None

def check_strategy(df):
    try:
        close = df['Close']
        ema9 = ta.trend.EMAIndicator(close, window=9).ema_indicator()
        ema21 = ta.trend.EMAIndicator(close, window=21).ema_indicator()
        ma8 = ta.trend.SMAIndicator(close, window=8).sma_indicator()
        ma50 = ta.trend.SMAIndicator(close, window=50).sma_indicator()
        rsi = ta.momentum.RSIIndicator(close, window=14).rsi()
        curr_ema9, prev_ema9 = ema9.iloc[-1], ema9.iloc[-2]
        curr_ema21, prev_ema21 = ema21.iloc[-1], ema21.iloc[-2]
        curr_ma8, curr_ma50 = ma8.iloc[-1], ma50.iloc[-1]
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
        print(f"strat {e}")
        return "WAIT", None

def get_winrate():
    total_tp = 0
    total_sl = 0
    total_open = 0
    per_pair = {}
    for pair_name in PAIRS:
        tp = sum(1 for t in active_trades[pair_name] if "TP" in t["status"])
        sl = sum(1 for t in active_trades[pair_name] if "SL" in t["status"])
        op = sum(1 for t in active_trades[pair_name] if t["status"] == "OPEN")
        total_tp += tp
        total_sl += sl
        total_open += op
        total = tp + sl
        wr = (tp / total * 100) if total > 0 else 0
        per_pair[pair_name] = {"tp": tp, "sl": sl, "open": op, "wr": wr}
    total_closed = total_tp + total_sl
    total_wr = (total_tp / total_closed * 100) if total_closed > 0 else 0
    return total_tp, total_sl, total_open, total_wr, per_pair

def check_all_trades():
    # TP/SL Tracker - checks every open trade, never deletes
    for pair_name in PAIRS:
        symbol, _ = PAIRS[pair_name]
        df = get_data(symbol)
        if df is None:
            continue
        high, low = df['High'].iloc[-1], df['Low'].iloc[-1]
        curr = df['Close'].iloc[-1]
        for trade in active_trades[pair_name]:
            if trade["status"] != "OPEN":
                continue
            hit = None
            if trade["action"] == "BUY":
                if low <= trade["sl"]:
                    hit = "SL"
                elif high >= trade["tp"]:
                    hit = "TP"
            else:
                if high >= trade["sl"]:
                    hit = "SL"
                elif low <= trade["tp"]:
                    hit = "TP"
            if hit:
                trade["status"] = f"{hit} HIT"
                trade["closed_price"] = curr
                trade["closed_time"] = time.time()
                if pair_name == "XAUUSD":
                    pnl_str = f"${abs(trade['tp'] - trade['entry']):.2f}"
                else:
                    mult = 10000 if pair_name in ["GBPUSD", "EURUSD"] else 100
                    pnl_str = f"{abs(trade['tp'] - trade['entry'])*mult:.0f} pips"
                if hit == "TP":
                    msg = f"✅ *TP HIT - {pair_name} {trade['action']}* 🟢\n\n📍 Entry: {fmt(trade['entry'], pair_name)}\n🎯 Closed: {fmt(curr, pair_name)}\n💸 Profit: +{pnl_str} | 1:{RR}"
                else:
                    msg = f"❌ *SL HIT - {pair_name} {trade['action']}* 🔴\n\n📍 Entry: {fmt(trade['entry'], pair_name)}\n🛑 Closed: {fmt(curr, pair_name)}\n💸 Loss: -{pnl_str}"
                send_telegram(msg)

keep_alive()
time.sleep(2)
send_telegram("🚀 *TYE V5.5 RESTARTED*\n\n✅ 5 Pairs: XAU, GU, GJ, EU, UJ\n✅ 15min signals\n✅ History kept - no delete\n✅ TP/SL Tracker LIVE\n✅ Daily 23:00 SAST winrate\n✅ 1:4 RR")

while True:
    try:
        check_all_trades()

        # Daily 23:00 SAST = 21:00 UTC
        now_utc = datetime.now(timezone.utc)
        if now_utc.hour == 21 and now_utc.minute == 0:
            today_str = now_utc.strftime("%Y-%m-%d")
            global last_daily_report_date
            if last_daily_report_date != today_str:
                tp, sl, op, wr, per_pair = get_winrate()
                if tp + sl > 0:
                    msg = f"📊 *TYE DAILY WINRATE - {today_str}* 📊\n\n"
                    msg += f"*TOTAL: {tp} TP | {sl} SL | {op} OPEN*\n"
                    msg += f"*Winrate: {wr:.1f}%*\n\n"
                    for pair, stats in per_pair.items():
                        if stats["tp"] + stats["sl"] > 0:
                            msg += f"{pair}: {stats['tp']}W / {stats['sl']}L / {stats['open']}O - {stats['wr']:.0f}%\n"
                    msg += f"\n🔥 Keep grinding VIP!"
                    send_telegram(msg)
                last_daily_report_date = today_str

        for pair_name, (symbol, sl_size) in PAIRS.items():
            if pair_name in last_signal_time:
                if time.time() - last_signal_time[pair_name] < COOLDOWN:
                    continue
            df = get_data(symbol)
            if df is None:
                continue
            action, price = check_strategy(df)
            if price is None:
                continue
            open_cnt = len([t for t in active_trades[pair_name] if t["status"] == "OPEN"])
            print(f"{pair_name}: {fmt(price, pair_name)} | {action} | Open:{open_cnt}")

            if action != "WAIT":
                sl = price - sl_size if action == "BUY" else price + sl_size
                tp = price + (sl_size * RR) if action == "BUY" else price - (sl_size * RR)
                emoji = "🟢" if action == "BUY" else "🔴"

                if pair_name == "XAUUSD":
                    msg = f"🚨 *TYE GOLD {action} SIGNAL* {emoji}\n\n💰 XAU/USD: ${price:.2f}\n📍 Entry: ${price:.2f}\n📊 {action} - EMA 9/21 + MA 8/50 + RSI\n🛑 SL: ${sl:.2f}\n🎯 TP: ${tp:.2f} | *1:{RR} RR*"
                elif pair_name == "GBPUSD":
                    msg = f"🚨 *TYE GBP/USD {action} SIGNAL* {emoji}\n\n💰 GBP/USD: {fmt(price, pair_name)}\n📍 Entry: {fmt(price, pair_name)}\n📊 {action} - EMA 9/21 + MA 8/50 + RSI\n🛑 SL: {fmt(sl, pair_name)}\n🎯 TP: {fmt(tp, pair_name)} | *1:{RR} RR*"
                elif pair_name == "GBPJPY":
                    msg = f"🚨 *TYE GBP/JPY {action} SIGNAL* {emoji}\n\n💰 GBP/JPY: {fmt(price, pair_name)}\n📍 Entry: {fmt(price, pair_name)}\n📊 {action} - EMA 9/21 + MA 8/50 + RSI\n🛑 SL: {fmt(sl, pair_name)}\n🎯 TP: {fmt(tp, pair_name)} | *1:{RR} RR*"
                elif pair_name == "EURUSD":
                    msg = f"🚨 *TYE EUR/USD {action} SIGNAL* {emoji}\n\n💰 EUR/USD: {fmt(price, pair_name)}\n📍 Entry: {fmt(price, pair_name)}\n📊 {action} - EMA 9/21 + MA 8/50 + RSI\n🛑 SL: {fmt(sl, pair_name)}\n🎯 TP: {fmt(tp, pair_name)} | *1:{RR} RR*"
                else:
                    msg = f"🚨 *TYE USD/JPY {action} SIGNAL* {emoji}\n\n💰 USD/JPY: {fmt(price, pair_name)}\n📍 Entry: {fmt(price, pair_name)}\n📊 {action} - EMA 9/21 + MA 8/50 + RSI\n🛑 SL: {fmt(sl, pair_name)}\n🎯 TP: {fmt(tp, pair_name)} | *1:{RR} RR*"

                send_telegram(msg)
                active_trades[pair_name].append({
                    "action": action, "entry": price, "sl": sl, "tp": tp,
                    "time": time.time(), "status": "OPEN"
                })
                last_signal_time[pair_name] = time.time()

        time.sleep(60)
    except Exception as e:
        print(f"LOOP ERR: {e}")
        time.sleep(60)
