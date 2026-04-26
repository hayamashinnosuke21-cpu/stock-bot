import requests
import time
import yfinance as yf
import pandas as pd

DISCORD_WEBHOOK_URL = "ここにWebhook"

SYMBOLS = ["7203.T","9984.T","6758.T"]

def send_discord(msg):
    requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})

def check_signal(df):
    if len(df) < 25:
        return None

    df["avg_volume"] = df["Volume"].rolling(20).mean()

    latest = df.iloc[-1]
    prev_high = df["High"].iloc[-6:-1].max()

    volume_spike = latest["Volume"] > latest["avg_volume"] * 2
    breakout = latest["Close"] > prev_high

    if volume_spike and breakout:
        return f"【ブレイク】価格:{latest['Close']} 出来高倍率:{latest['Volume']/latest['avg_volume']:.2f}"

    return None

# ★起動確認フラグ
first_run = True

while True:
    # ★最初の1回だけテスト通知
    if first_run:
        send_discord("✅ Render起動確認OK（テスト通知）")
        first_run = False

    for symbol in SYMBOLS:
        try:
            df = yf.download(symbol, interval="5m", period="1d", progress=False)
            signal = check_signal(df)

            if signal:
                send_discord(f"{symbol} {signal}")

        except Exception as e:
            print(e)

    time.sleep(60)
