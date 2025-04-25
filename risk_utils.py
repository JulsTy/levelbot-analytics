from typing import Optional, Tuple
from config import (
    STRUCTURAL_TARGET_RATIO, PARTIAL_TARGET_RATIO,
    DYNAMIC_ADJUSTMENT_MODE, DYNAMIC_TRIGGER_ATR, DYNAMIC_TRIGGER_PCT, 
    DYNAMIC_STEP_ATR
)

def select_structural_limit(entry_price: float, atr: float,
                        swing_high: Optional[float] = None,
                        swing_low: Optional[float] = None,
                        trendline_price: Optional[float] = None,
                        poc: Optional[float] = None,
                        low_volume_exit: Optional[float] = None,
                        side: str = "LONG") -> Optional[float]:
    """
    Determines the evaluation point for scenario rejection (formerly stop-loss)
    based on structural levels. Returns None if no valid level is found.
    """

    if atr <= 0:
        raise ValueError("ATR must be > 0")

    # 1️⃣ Trendline-based
    if trendline_price:
        buffer = 0.25 * atr
        raw = trendline_price - buffer if side == "LONG" else trendline_price + buffer
        dist = abs(entry_price - raw)
        if dist < 6 * atr and ((side == "LONG" and raw < entry_price) or (side == "SHORT" and raw > entry_price)):
            print(f"[DEBUG] ✅ Evaluation level selected from trendline: {raw:.5f}")
            return raw
        else:
            print(f"[DEBUG] ❌ Trendline rejected: dist={dist:.5f} with ATR={atr:.5f}")

    # 2️⃣ Swing-level
    if side == "LONG" and swing_low:
        raw = swing_low * 0.997 - 0.25 * atr
        dist = abs(entry_price - raw)
        if raw < entry_price and dist < 3 * atr:
            print(f"[DEBUG] ✅ Evaluation level selected from swing-low: {raw:.5f}")
            return raw
    elif side == "SHORT" and swing_high:
        raw = swing_high * 1.003 + 0.25 * atr
        dist = abs(entry_price - raw)
        if raw > entry_price and dist < 3 * atr:
            print(f"[DEBUG] ✅ Evaluation level selected from swing-high: {raw:.5f}")
            return raw

    # 3️⃣ POC-based
    if poc:
        raw = poc - 0.25 * atr if side == "LONG" else poc + 0.25 * atr
        dist = abs(entry_price - raw)
        if (side == "LONG" and raw < entry_price) or (side == "SHORT" and raw > entry_price):
            if dist < 3 * atr:
                print(f"[DEBUG] ✅ Evaluation level selected from POC: {raw:.5f}")
                return raw

    # 4️⃣ Low-volume zone exit
    if low_volume_exit:
        raw = low_volume_exit - 0.25 * atr if side == "LONG" else low_volume_exit + 0.25 * atr
        dist = abs(entry_price - raw)
        if (side == "LONG" and raw < entry_price) or (side == "SHORT" and raw > entry_price):
            if dist < 3 * atr:
                print(f"[DEBUG] ✅ Evaluation level selected from low-volume area exit: {raw:.5f}")
                return raw

    print(f"[DEBUG] ❌ No evaluation level found for {side} at price {entry_price:.4f}")
    return None


def select_structural_target(entry_price: float, structural_limit: float, atr: float,
                          swing_high: Optional[float] = None,
                          swing_low: Optional[float] = None,
                          next_swing_high: Optional[float] = None,
                          next_swing_low: Optional[float] = None,
                          trendline_target: Optional[float] = None,
                          poc: Optional[float] = None,
                          low_volume_exit: Optional[float] = None,
                          side: str = "LONG",
                          breakout: bool = False,
                          confidence: float = 0.0) -> Tuple[float, Optional[float], bool]:
    """
    Determines the scenario validation target (formerly take-profit).
    Includes fallback calculation if structural targets are not available.
    Returns (target, partial_target, dynamic_adjustment_trigger).
    """
    stop_dist = abs(entry_price - structural_limit)
    target = None
    rr_used = None
    partial_target = None
    dynamic_adjustment = False

    # 1️⃣ Swing targets
    if breakout:
        if side == "LONG" and next_swing_high:
            candidate = next_swing_high * 0.995
            if candidate > entry_price:
                target = candidate
        elif side == "SHORT" and next_swing_low:
            candidate = next_swing_low * 1.005
            if candidate < entry_price:
                target = candidate
    else:
        if side == "LONG" and swing_high:
            candidate = swing_high * 0.995
            if candidate > entry_price:
                target = candidate
        elif side == "SHORT" and swing_low:
            candidate = swing_low * 1.005
            if candidate < entry_price:
                target = candidate

    # 2️⃣ POC
    if target is None and poc:
        if (side == "LONG" and poc > entry_price) or (side == "SHORT" and poc < entry_price):
            target = poc

    # 3️⃣ Trend target
    if target is None and trendline_target:
        if (side == "LONG" and trendline_target > entry_price) or (side == "SHORT" and trendline_target < entry_price):
            target = trendline_target

    # 4️⃣ Low-volume area exit
    if target is None and low_volume_exit:
        if (side == "LONG" and low_volume_exit > entry_price) or (side == "SHORT" and low_volume_exit < entry_price):
            target = low_volume_exit

    # 5️⃣ Fallback by structural ratio
    if target is None:
        target = entry_price + stop_dist * STRUCTURAL_TARGET_RATIO * (1 if side == "LONG" else -1)

    rr_used = abs(target - entry_price) / stop_dist

    # 🟡 Apply partial target and dynamic adjustment if RR > MAX
    if rr_used > STRUCTURAL_TARGET_RATIO:
        partial_target = entry_price + stop_dist * PARTIAL_TARGET_RATIO * (1 if side == "LONG" else -1)
        dynamic_adjustment = True

    return target, partial_target, dynamic_adjustment
