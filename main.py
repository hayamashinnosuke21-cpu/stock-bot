import requests
import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# ===== 設定 =====
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1497821260208541816/AF2vg1ekJvqUCFYuGFXeZMpgVzMZCoaB5nSI3MYMZoOlwhWioaTBS2qfQ2JtrJ1Aoakz"

# ▼候補ユニバース（ここ重要：増やすほど精度UP）
CANDIDATES = [
    "4593.T","6619.T","7342.T","6526.T","4165.T",
    "5253.T","9229.T","5586.T","4894.T","4385.T",
    "7373.T","9553.T","5255.T","5132.T","4890.T",
    "4475.T","4882.T","7776.T","3681.T","4011.T"
]

# ===== 基本関数 =====
def send_discord(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})
    except Exception as e:
        print("通知エラー:", e)

def now_jst():
    return datetime.utcnow() + timedelta(hours=9)

def is_pick_time():
    n = now_jst()
    return n.hour == 8 and 45 <= n.minute <= 55

def is_trade_time():
    n = now_jst()
    return n.hour == 9 and n.minute <= 30

# ===== 銘柄抽出 =====
def pick_stocks():
    picked = []

    for symbol in CANDIDATES:
        try:
            df = yf.download(symbol, interval="5m", period="1d", progress=False)

            if len(df) < 2:
                continue

            change = (df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]

            if change > 0.02:
                picked.append((symbol, change))

        except:
            continue

    picked = sorted(picked, key=lambda x: x[1], reverse=True)
    return [p[0] for p in picked[:5]]

# ===== シグナル判定 =====
def check_signal(df):
    if len(df) < 25:
        return None

    df["avg_volume"] = df["Volume"].rolling(20).mean()

    latest = df.iloc[-1]
    prev_high = df["High"].iloc[-6:-1].max()

    volume_spike = latest["Volume"] > latest["avg_volume"] * 2
    breakout = latest["Close"] > prev_high

    change = (latest["Close"] - df["Close"].iloc[0]) / df["Close"].iloc[0]

    if volume_spike and breakout and change > 0.02:
        return f"【寄りブレイク】価格:{latest['Close']:.2f} 上昇率:{change*100:.2f}%"

    return None

# ===== メイン =====
print("起動中...")

selected_symbols = []
picked_today = False

while True:
    try:
        # ▼朝の自動銘柄ピック
        if is_pick_time() and not picked_today:
            selected_symbols = pick_stocks()

            if selected_symbols:
                send_discord("【本日の監視銘柄】\n" + "\n".join(selected_symbols))
            else:
                send_discord("銘柄なし（様子見）")

            picked_today = True

        # ▼寄り付き監視
        if is_trade_time() and selected_symbols:
            for symbol in selected_symbols:
                df = yf.download(symbol, interval="5m", period="1d", progress=False)
                signal = check_signal(df)

                if signal:
                    send_discord(f"{symbol} {signal}")

        # ▼日付リセット
        if now_jst().hour == 0 and now_jst().minute == 0:
            picked_today = False
            selected_symbols = []

    except Exception as e:
        print("エラー:", e)

    time.sleep(60)
