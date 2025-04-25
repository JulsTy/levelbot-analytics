from typing import List, Tuple, Dict, Optional
import numpy as np

class TrendlineDetector:
    def __init__(self, api, min_touches: int = 2, min_slope: float = 0.0002, tolerance_pct: float = 0.01):
        self.api = api
        self.min_touches = min_touches
        self.min_slope = min_slope
        self.tolerance_pct = tolerance_pct

    def _find_trendline(self, prices: List[float], kind: str = "high") -> Optional[Dict]:
        n = len(prices)
        for i in range(n):
            for j in range(i + 3, n):
                x1, x2 = i, j
                y1, y2 = prices[i], prices[j]
                slope = (y2 - y1) / (x2 - x1)

                if kind == "high" and slope >= -self.min_slope:
                    continue
                if kind == "low" and slope <= self.min_slope:
                    continue

                hits = 0
                for k in range(i + 1, j):
                    y_k = y1 + slope * (k - x1)
                    price_k = prices[k]
                    diff_pct = abs(price_k - y_k) / y_k
                    if diff_pct < self.tolerance_pct:
                        hits += 1

                if hits >= self.min_touches - 2:
                    return {
                        "slope": slope,
                        "points": [(x1, y1), (x2, y2)],
                        "touches": hits + 2,
                        "age": n - x2,
                        "price_now": y2 + slope * (n - x2)
                    }

        return None

    def detect_trendlines(self, symbol: str, interval: str = "1h", lookback: int = 50) -> Dict[str, Dict]:
        klines = self.api.get_klines(symbol, interval, limit=lookback)
        if not klines or len(klines) < 10:
            return {}

        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]

        down = self._find_trendline(highs, kind="high")
        up = self._find_trendline(lows, kind="low")

        return {
            "down_trendline": down,
            "up_trendline": up
        }

    def detect_trendlines_multi(self, symbol: str, lookbacks: Dict[str, int] = {"15m": 50, "1h": 50}) -> Dict[str, Dict[str, Dict]]:
        result = {}
        for interval, lb in lookbacks.items():
            trendlines = self.detect_trendlines(symbol, interval=interval, lookback=lb)
            result[interval] = trendlines
        return result

    def detect_combined_levels(self, symbol: str, levels: Dict[str, object]) -> Dict[str, object]:
        """
        Extends the level dictionary with swing levels and trendlines. Should be called from the same place where detect_swing_levels is used.
        """
        trendlines = self.detect_trendlines_multi(symbol)
        levels.update({
            "trendline_15m_down": trendlines.get("15m", {}).get("down_trendline"),
            "trendline_15m_up": trendlines.get("15m", {}).get("up_trendline"),
            "trendline_1h_down": trendlines.get("1h", {}).get("down_trendline"),
            "trendline_1h_up": trendlines.get("1h", {}).get("up_trendline"),
        })
        return levels

    def check_trendline_breakout(self, current_price: float, direction: str, key_levels: Dict[str, object]) -> List[str]:
        reasons = []
        if direction == "LONG":
            for tf in ["15m", "1h"]:
                up = key_levels.get(f"trendline_{tf}_up")
                if up and current_price > up.get("price_now", float("inf")):
                    reasons.append(f"breakout of upward trendline {tf}")
        elif direction == "SHORT":
            for tf in ["15m", "1h"]:
                down = key_levels.get(f"trendline_{tf}_down")
                if down and current_price < down.get("price_now", float("-inf")):
                    reasons.append(f"breakout of downward trendline {tf}")
        return reasons

    def get_trendline_value_at_index(self, trendline: dict, index: int) -> Optional[float]:
        if not trendline or "points" not in trendline or "slope" not in trendline:
            return None
        try:
            (x1, y1), _ = trendline["points"]
            slope = trendline["slope"]
            return y1 + slope * (index - x1)
        except Exception:
            return None