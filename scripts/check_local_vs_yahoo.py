import pandas as pd
import yfinance as yf
from pathlib import Path

# -------- Base paths (portable) --------
BASE_DIR = Path(__file__).resolve().parents[1]   # .../Sectoral_Scanner
DATA_DIR = BASE_DIR / "data"

# 🔁 Change this ticker to any one you want to inspect
TICKER = "SBILIFE.NS"
SAFE_NAME = TICKER.replace(".", "_")
LOCAL_PATH = DATA_DIR / f"{SAFE_NAME}.csv"

print(f"Checking local vs Yahoo for: {TICKER}")
print(f"Local file: {LOCAL_PATH}")

# ---- Local file ----
if not LOCAL_PATH.exists():
    print("❌ Local file does not exist.")
else:
    df_local = pd.read_csv(LOCAL_PATH)
    if df_local.empty:
        print("❌ Local file is empty.")
    else:
        df_local["Date"] = pd.to_datetime(df_local["Date"], errors="coerce")
        df_local = df_local.dropna(subset=["Date"])
        print("Local last 5 dates:")
        print(df_local["Date"].tail())
        print("Local last date:", df_local["Date"].max().date())

# ---- Yahoo latest ----
print("\nDownloading last 15 days from Yahoo...")
df_yf = yf.download(
    TICKER,
    period="15d",
    interval="1d",
    auto_adjust=False,
    progress=False,
)

if df_yf.empty:
    print("❌ Yahoo returned no data.")
else:
    df_yf = df_yf.reset_index()
    df_yf["Date"] = pd.to_datetime(df_yf["Date"], errors="coerce")
    df_yf = df_yf.dropna(subset=["Date"])
    print("\nYahoo last 5 dates:")
    print(df_yf["Date"].tail())
    print("Yahoo last date:", df_yf["Date"].max().date())
