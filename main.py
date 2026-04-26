import requests
import time
import yfinance as yf
import pandas as pd

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1497821260208541816/AF2vg1ekJvqUCFYuGFXeZMpgVzMZCoaB5nSI3MYMZoOlwhWioaTBS2qfQ2JtrJ1Aoakz"

SYMBOLS = ["7203.T", "9984.T", "6758.T"]

def send_discord(msg):
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})
    except Exception as e:
        print("通知エラー:", e)

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

# ▼最初の1回だけテスト通知
first_run = True

while True:
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
            print("取得エラー:", e)

    time.sleep(60)
