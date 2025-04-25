# indicators.py — vectorised, side‑effect‑free, NumPy‑powered
# -----------------------------------------------------------------------------
# This file fully replaces the previous version. It includes:
#   • all calculations return scalars (no np.ndarray output);
#   • assess_confidence works reliably thanks to _sanitize();
#   • TrueRange / ATR, EMA, MACD — implemented without length distortion;
#   • volume_profile adapts bin_size to price volatility;
#   • evaluate_direction no longer mutates input structures.
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections import defaultdict
from typing import List, Dict, Tuple

import numpy as np

# ------------------------------------------------------------------
# generic helpers
# ------------------------------------------------------------------

def _sanitize(obj):
    if isinstance(obj, np.ndarray):
        return float(obj.item()) if obj.size == 1 else [_sanitize(x) for x in obj.tolist()]
    if isinstance(obj, (list, tuple)):
        return [_sanitize(x) for x in obj]
    return obj


def _ema(arr: np.ndarray, period: int) -> np.ndarray:
    alpha = 2 / (period + 1)
    out = np.empty_like(arr)
    out[0] = arr[0]
    for i in range(1, len(arr)):
        out[i] = alpha * arr[i] + (1 - alpha) * out[i - 1]
    return out


def _true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    prev_close = np.roll(close, 1)
    prev_close[0] = close[0]
    return np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))

# ------------------------------------------------------------------
# ATR / Trend / MACD
# ------------------------------------------------------------------

def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    if len(highs) < period + 1:
        return 0.0
    tr = _true_range(np.asarray(highs), np.asarray(lows), np.asarray(closes))
    atr = np.convolve(tr, np.ones(period) / period, mode="valid")[-1]
    return float(atr)


def calculate_trend(closes: List[float], atr: float, ema_period: int = 10) -> str:
    if len(closes) < 6:
        return "flat"
    if closes[-1] > closes[-5] + 0.2 * atr:
        return "up"
    elif closes[-1] < closes[-5] - 0.2 * atr:
        return "down"
    return "flat"


def calculate_normalized_macd(closes: List[float]) -> Dict[str, float]:
    if len(closes) < 26:
        return {}
    try:
        c = np.asarray([float(x[0]) if isinstance(x, list) else float(x) for x in closes])
    except Exception as e:
        print("[ERROR] Error while converting closes to float:", e)
        return {}
    macd_line = _ema(c, 12) - _ema(c, 26)
    signal = _ema(macd_line, 9)
    hist = macd_line - signal
    return {
        "macd": float(macd_line[-1]),
        "signal": float(signal[-1]),
        "histogram": float(hist[-1])
    }

# ------------------------------------------------------------------
# Volume Profile
# ------------------------------------------------------------------

def calculate_volume_profile(klines: List[List[str]], bin_size: float | None = None) -> Dict[str, object]:
    if len(klines) < 3:
        return {"poc": None, "low_volume_nodes": []}

    highs = np.array([float(k[2]) for k in klines])
    lows  = np.array([float(k[3]) for k in klines])
    vols  = np.array([float(k[5]) for k in klines])
    mid   = (highs + lows) / 2

    price_now = float(klines[-1][4])
    if bin_size is None:
        tick = max(price_now * 0.001, np.mean(highs - lows) * 0.2)
        bin_size = round(tick, 6) or 0.000001

    bins = np.round(mid / bin_size) * bin_size
    vol_by_bin: Dict[float, float] = defaultdict(float)
    for p, v in zip(bins, vols):
        vol_by_bin[float(p)] += v

    poc = max(vol_by_bin, key=vol_by_bin.get)
    avg_v = np.mean(list(vol_by_bin.values()))
    low_nodes = [p for p, v in vol_by_bin.items() if v < avg_v * 0.5]

    result = {
        "poc": float(poc) if poc is not None else None,
        "low_volume_nodes": [float(x) for x in low_nodes],
    }
    return _sanitize(result)

# ------------------------------------------------------------------
# Candle stats
# ------------------------------------------------------------------

def calculate_candle_stats(candle: List[str], atr: float, volume_series: List[float]) -> Dict[str, object]:
    o, h, l, c, v = map(float, (candle[1], candle[2], candle[3], candle[4], candle[5]))
    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l
    last = volume_series[-10:] if len(volume_series) >= 10 else volume_series
    avg_v = sum(last) / len(last)
    spike = v > avg_v * 1.6
    return {
        "body": body,
        "upper_wick": upper,
        "lower_wick": lower,
        "volume": v,
        "volume_spike": spike,
        "strong_body": body > atr * 0.6,
        "doji": body < atr * 0.1 and upper > body and lower > body,
        "weak_volume": v < avg_v * 0.8,
    }

# ------------------------------------------------------------------
# Direction logic (no side effects)
# ------------------------------------------------------------------

def evaluate_direction(current_price: float, swing_high: float, swing_low: float,
                       trend_1h: str, atr: float,
                       highs: List[float], lows: List[float],
                       candle_stats: Dict[str, object]) -> Tuple[str | None, List[str], bool]:
    """Determines trade direction based on breakout, bounce, and flat-breakout logic."""
    direction: str | None = None
    reasons: List[str] = []
    in_middle = swing_low < current_price < swing_high

        # breakout conditions
    breakout_up = (
        swing_high and current_price > swing_high + 0.1 * atr and
        candle_stats["strong_body"] and candle_stats["volume_spike"] and trend_1h == "up"
    )
    breakout_down = (
        swing_low and current_price < swing_low - 0.1 * atr and
        candle_stats["strong_body"] and candle_stats["volume_spike"] and trend_1h == "down"
    )

    # bounce conditions
    small_bounce = 1.2
    large_bounce = 1.8
    bounce_up = (
        swing_low and candle_stats["lower_wick"] > candle_stats["body"] * 1.5 and
        current_price > swing_low and trend_1h != "down"
    )
    bounce_down = (
        swing_high and candle_stats["upper_wick"] > candle_stats["body"] * 1.5 and
        current_price < swing_high and trend_1h != "up"
    )

    if breakout_up:
        direction = "LONG"; reasons.append("Breakout up + volume + 1H trend")
    elif breakout_down:
        direction = "SHORT"; reasons.append("Breakout down + volume + 1H trend")
    elif bounce_up and abs(current_price - swing_low) < large_bounce * atr:
        direction = "LONG"; reasons.append(f"Bounce from swing-LOW within {large_bounce} ATR")
    elif bounce_down and abs(current_price - swing_high) < large_bounce * atr:
        direction = "SHORT"; reasons.append(f"Bounce from swing-HIGH within {large_bounce} ATR")

    # flat-breakout: catching impulse without trend and without volume
    if direction is None:
        if current_price > swing_high:
            direction = "LONG"; reasons.append("Simple up breakout")
        elif current_price < swing_low:
            direction = "SHORT"; reasons.append("Simple down breakout")

    # flat-breakout with volume
    if direction is None and candle_stats["strong_body"] and candle_stats["volume_spike"]:
        if current_price > swing_high + 0.1 * atr:
            direction = "LONG"; reasons.append("Flat-breakout + volume")
        elif current_price < swing_low - 0.1 * atr:
            direction = "SHORT"; reasons.append("Flat-breakout + volume")

    return direction, reasons, in_middle

# ------------------------------------------------------------------
# Confidence score
# ------------------------------------------------------------------

def assess_confidence(
    direction: str | None,
    reasons: List[str],
    swing_age: int,
    trend_4h: str,
    vp: dict,
    macd_data: dict,
    current_price: float,
    atr: float
) -> Tuple[float, List[str]]:

    try:
        current_price = float(current_price)
        atr = float(atr)
    except Exception as e:
        reasons.append(f"float conversion error: {e}")
        return 0.0, reasons

    confidence = len(reasons)
    soft: List[str] = []

    # --- level age
    if swing_age <= 10:
        confidence += 1; reasons.append("fresh level")
    elif swing_age > 50:
        confidence -= 1; reasons.append("very old level")

    # --- 4H trend
    if direction == "LONG" and trend_4h == "up":
        confidence += 1; reasons.append("4H confirms")
    elif direction == "SHORT" and trend_4h == "down":
        confidence += 1; reasons.append("4H confirms")
    elif trend_4h == "flat":
        soft.append("4H flat")
    else:
        confidence -= 1; reasons.append("4H does not confirm")

    # --- volume profile
    poc_val = None
    try:
        raw_poc = vp.get("poc", None)
        if raw_poc is not None:
            poc_val = float(raw_poc)
    except Exception as e:
        reasons.append(f"poc error: {e}")
        poc_val = None

    print("[DEBUG] poc_val:", poc_val)

    if poc_val is not None:
        try:
            diff = abs(current_price - poc_val)
            if diff < 0.3 * atr:
                confidence -= 1; reasons.append("near POC")
            else:
                raw_nodes = vp.get("low_volume_nodes", [])
                float_nodes = []
                for n in raw_nodes:
                    try:
                        float_nodes.append(float(n))
                    except:
                        continue
                if any(abs(current_price - n) < 1e-9 for n in float_nodes):
                    confidence += 1; reasons.append("exit from low-volume area")
        except Exception as e:
            reasons.append(f"volume profile calc error: {e}")

    # --- MACD
    try:
        macd = float(macd_data.get("macd", 0))
        sig = float(macd_data.get("signal", 0))
        hist = float(macd_data.get("histogram", 0))
    except Exception as e:
        macd = sig = hist = 0
        reasons.append(f"macd error: {e}")

    if direction == "LONG":
        if macd > sig and hist > 0:
            confidence += 1; reasons.append("MACD confirms")
        elif hist > -0.002:
            soft.append("MACD weak")
        else:
            confidence -= 1; reasons.append("MACD does not confirm")
    elif direction == "SHORT":
        if macd < sig and hist < 0:
            confidence += 1; reasons.append("MACD conforms")
        elif hist < 0.002:
            soft.append("MACD weak")
        else:
            confidence -= 1; reasons.append("MACD does not confirm")

    if confidence >= 2 and soft:
        confidence -= 0.5
        reasons.extend(soft)

    result = round(confidence * 2) / 2
    print("[DEBUG] final confidence:", result)
    return result, reasons

# ------------------------------------------------------------------
# Market mode classifier
# ------------------------------------------------------------------

def classify_market_mode(trend_1h: str,
                         atr_fast: float,
                         atr_slow: float,
                         vols_15m: List[float]) -> str:
    spike = vols_15m[-1] > max(vols_15m[-5:-1])
    if trend_1h == "flat" and atr_fast < atr_slow * 0.6:
        return "flet"
    if trend_1h in ("up", "down") and spike:
        return "trend"
    if atr_fast > atr_slow * 1.8:
        return "scalp"
    return "neutral"
