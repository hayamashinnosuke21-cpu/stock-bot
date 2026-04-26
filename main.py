import requests
import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# ▼Webhook
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1497821260208541816/AF2vg1ekJvqUCFYuGFXeZMpgVzMZCoaB5nSI3MYMZoOlwhWioaTBS2qfQ2JtrJ1Aoakz"

# ▼監視候補（ここは後で増やすと精度UP）
CANDIDATES = [
    "4593.T","6619.T","7342.T","6526.T","4165.T",
    "5253.T","9229.T","5586.T","4894.T","4385.T"
]

def send_discord(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})
    except:
        pass

def is_market_open():
    now = datetime.utcnow() + timedelta(hours=9)  # JST変換
    return now.hour == 9 and now.minute <= 30

def pick_active_stocks():
    selected = []

    for symbol in CANDIDATES:
        try:
            df = yf.download(symbol, interval="5m", period="1d", progress=False)

            if len(df) < 2:
                continue

            change = (df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]

            # ▼上昇率2%以上を抽出（疑似ランキング）
            if change > 0.02:
                selected.append(symbol)

        except:
            continue

    return selected

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

print("起動中...")

selected_symbols = []

while True:
    try:
        if is_market_open():
            # ▼9:00〜9:30だけ銘柄選定
            if not selected_symbols:
                selected_symbols = pick_active_stocks()
                send_discord(f"監視銘柄: {selected_symbols}")

            for symbol in selected_symbols:
                df = yf.download(symbol, interval="5m", period="1d", progress=False)
                signal = check_signal(df)

                if signal:
                    send_discord(f"{symbol} {signal}")

        else:
            selected_symbols = []  # リセット

    except Exception as e:
        print("エラー:", e)

    time.sleep(60)
