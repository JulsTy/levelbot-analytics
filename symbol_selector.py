import requests
import time

# Cache for BingX contracts
_cached_bingx_symbols = None
_last_bingx_update = 0
_CACHE_DURATION = 900  # 15 minutes

def get_top_binance_symbols(limit=20):
    # Fetching trading pairs list from Binance
    url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(url)
    if response.status_code != 200:
        print("⚠️ Error while fetching data from Binance")
        return []

    data = response.json()
    filtered = []

    for item in data:
        symbol = item["symbol"]
        if not symbol.endswith("USDT") or any(x in symbol for x in ["DOWN", "UP", "BUSD", "FDUSD", "TUSD", "USDC", "DAI"]):
            continue

        price_change = float(item["priceChangePercent"])
        volume = float(item["quoteVolume"])

        filtered.append({
            "symbol": symbol.replace("USDT", "-USDT"),
            "change": price_change,
            "volume": volume
        })

    # Sorting by trading volume and price volatility
    sorted_symbols = sorted(filtered, key=lambda x: (x["volume"], abs(x["change"])), reverse=True)
    top_symbols = [s["symbol"] for s in sorted_symbols[:limit * 2]]

    # Fetching contract list from BingX (cached for 15 minutes)
    global _cached_bingx_symbols, _last_bingx_update
    now = time.time()

    if not _cached_bingx_symbols or now - _last_bingx_update > _CACHE_DURATION:
        print("🔁 Updating BingX contract list...")
        bingx_url = "https://open-api.bingx.com/openApi/swap/v2/quote/contracts"
        try:
            bingx_resp = requests.get(bingx_url).json()
            if bingx_resp.get("code") != 0:
                print("❌ BingX error:", bingx_resp)
                return []
            _cached_bingx_symbols = set(item["symbol"] for item in bingx_resp["data"])
            _last_bingx_update = now
        except Exception as e:
            print("❌ Error while requesting data from BingX:", e)
            return []

    # Filtering using cache
    valid_symbols = [s for s in top_symbols if s in _cached_bingx_symbols]

    print(f"🔍 All selected coins from Binance (top-{limit * 2}):", top_symbols)
    print(f"✅ Passed BingX filter:", valid_symbols[:limit])

    return valid_symbols[:limit]


# 🧪 For manual execution
if __name__ == "__main__":
    symbols = get_top_binance_symbols(limit=20)
    print("🔧 Retrieved symbols:", symbols)
