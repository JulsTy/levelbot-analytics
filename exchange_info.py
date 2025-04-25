# ---------------------------------------------------------------------------
# Helper module (same file for convenience) — production: split into exchange_info.py
# ---------------------------------------------------------------------------

import requests
from math import floor

class ExchangeInfo:
    """Lightweight cache of precision / stepSize per symbol."""

    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._binance_info_url = "https://api.binance.com/api/v3/exchangeInfo"

    def _fetch_symbol(self, symbol: str) -> dict:
        # Convert "BTC-USDT" → "BTCUSDT"
        s = symbol.replace("-", "")
        if s in self._cache:
            return self._cache[s]

        data = requests.get(self._binance_info_url, timeout=5).json()
        for itm in data.get("symbols", []):
            if itm.get("symbol") == s:
                # Precision parameters from Binance
                price_precision = itm.get("quotePrecision", 8)

                # Lot step (LOT_SIZE)
                lot_filter = next(
                    (f for f in itm.get("filters", []) if f.get("filterType") == "LOT_SIZE"),
                    {}
                )
                qty_step = float(lot_filter.get("stepSize", 1e-8))

                # Minimum notional (MIN_NOTIONAL), if any
                notional_filter = next(
                    (f for f in itm.get("filters", []) if f.get("filterType") == "MIN_NOTIONAL"),
                    None
                )
                min_notional = (
                    float(notional_filter["minNotional"])
                    if notional_filter and "minNotional" in notional_filter
                    else 0.0
                )

                precisions = {
                    "price_precision": price_precision,
                    "qty_step":         qty_step,
                    "min_notional":     min_notional,
                }

                self._cache[s] = precisions
                return precisions

        raise ValueError(f"Symbol {symbol} not found in exchangeInfo")


    # ----------------- rounding helpers -----------------
    def round_price(self, symbol: str, price: float) -> float:
        if price is None:
            raise ValueError(f"[round_price] 🚫 Price for {symbol} is not defined (None), cannot round")
        info = self._fetch_symbol(symbol)
        prec = info["price_precision"]
        return round(price, prec)


    def round_qty(self, symbol: str, qty: float) -> float:
        info = self._fetch_symbol(symbol)
        step = info["qty_step"]
        return floor(qty / step) * step