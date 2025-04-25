from statistics import mean
from config import SWING_LOOKBACK
from collections import Counter

class LevelsDetector:
    def __init__(self, api):
        self.api = api

    def _cluster_level(self, values, tol_pct=0.15):
        if not values:
            return None, 0
        spread = max(values) - min(values)
        tol = spread * tol_pct or 1e-8  # ← защита от деления на 0
        buckets = Counter(round(v / tol) for v in values)
        most_common_bucket, freq = buckets.most_common(1)[0]
        level_vals = [v for v in values if round(v / tol) == most_common_bucket]
        return mean(level_vals), freq

    def detect_swing_levels(self, symbol, interval="1h"):
        data = self.api.get_klines(symbol, interval, limit=SWING_LOOKBACK)
        if not data:
            return None

        highs = [float(c[2]) for c in data]
        lows  = [float(c[3]) for c in data]

        swing_high, tests_high = self._cluster_level(highs)
        swing_low,  tests_low  = self._cluster_level(lows)

        if swing_high is None or swing_low is None:
            return {}

        # 👇 ADDED: detecting the next level
        next_highs = [h for h in highs if h > swing_high * 1.01]
        next_lows  = [l for l in lows if l < swing_low * 0.99]

        next_swing_high, _ = self._cluster_level(next_highs, tol_pct=0.10)
        next_swing_low, _  = self._cluster_level(next_lows, tol_pct=0.10)

        def _age(level, series):
            for idx in range(len(series) - 1, -1, -1):
                if abs(series[idx] - level) < 1e-8:
                    return len(series) - idx
            return len(series)

        age_high = _age(swing_high, highs)
        age_low  = _age(swing_low,  lows)

        return {
            "swing_high": swing_high,
            "swing_low":  swing_low,
            "swing_age":  min(age_high, age_low),
            "tests_high": tests_high,
            "tests_low":  tests_low,
            "next_swing_high": next_swing_high,
            "next_swing_low":  next_swing_low
        }
