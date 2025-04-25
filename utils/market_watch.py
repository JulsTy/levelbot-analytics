# utils/market_watch.py  (новый файл)
import requests, time
from collections import deque

BINANCE_TICKER_24H = "https://api.binance.com/api/v3/ticker/24hr"

def top_liquid_pairs(limit=20):
    data = requests.get(BINANCE_TICKER_24H, timeout=5).json()
    # filter only USDT pairs and sort by volume quote
    liquid = sorted(
        (d for d in data if d["symbol"].endswith("USDT")),
        key=lambda x: float(x["quoteVolume"]),
        reverse=True
    )
    return [d["symbol"].replace("USDT","-USDT") for d in liquid[:limit]]

# basic volatility spike check (1-minute ATR relative to 1-hour ATR)
class VolatilityGuard:
    def __init__(self, max_factor=4, cool_off=300):
        self.max_factor = max_factor
        self.cool_off = cool_off
        self.last_trigger = 0
        self.window = deque(maxlen=60)   # 1-minute ATR history

    def push(self, atr_1m):
        self.window.append(atr_1m)
        if len(self.window) < 60:        # wait for one hour of historical data
            return False
        atr_hour = sum(self.window)/60
        if atr_1m > atr_hour * self.max_factor:
            self.last_trigger = time.time()
            return True
        return False

    def in_cool_off(self):
        return (time.time() - self.last_trigger) < self.cool_off

def bingx_supported_symbols() -> set[str]:
    """
    Returns a set of all BingX contracts like BTC-USDT, ETH-USDT, etc.
    """
    url = "https://open-api.bingx.com/openApi/swap/v2/quote/contracts"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json().get("data", [])
        return {entry["symbol"] for entry in data if "symbol" in entry}
    except Exception as e:
        print(f"⚠️ Error fetching contract list from BingX: {e}")
        return set()
