# config.py — Configuration for LevelBot Analytics Engine (non-trading)
# 🔑 API-keys от BingX (making later)

API_KEY = ""
API_SECRET = ""
# ------------------------------------------------------------------
# 🪙 Analyzed symbols
TRADING_PAIRS = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "DOGE-USDT", "XRP-USDT"]

# ------------------------------------------------------------------
# 📊 Market & indicator settings
SWING_LOOKBACK              = 100   # Number of candles to look back for swing level detection
VOLUME_PROFILE_LOOKBACK     = 100   # Number of candles for volume profile calculation
EMA_PERIOD                  = 50    # EMA period for trend assessment
ADX_TREND_THRESHOLD         = 20    # ADX value to confirm strong trend
ADX_FLAT_THRESHOLD          = 15    # ADX value to detect flat/range markets
VOLUME_SPIKE_MULTIPLIER     = 1.2   # Multiplier to detect volume spikes
ATR_PERIOD                  = 14    # ATR calculation period

# ------------------------------------------------------------------
# 🧪 Scenario validation parameters (formerly RR / stop-loss / take-profit logic)
STRUCTURAL_TARGET_RATIO     = 3.0   # Former TP_SL_RATIO, ratio between structural limit and structural target
PARTIAL_TARGET_RATIO        = 1.5   # Former PARTIAL_TP_RATIO, ratio for optional partial target
DYNAMIC_ADJUSTMENT_MODE     = "volatility"   # Adjustment mode: "volatility", "momentum", or "off"
DYNAMIC_TRIGGER_ATR         = 1.0   # Trigger adjustment if ATR exceeds this multiple
DYNAMIC_TRIGGER_PCT         = 2.0   # Or if % distance is exceeded (alternative trigger)
DYNAMIC_STEP_ATR            = 0.5   # Step size for adjustment (ATR-based)
DYNAMIC_STEP_PCT            = 1.0   # Step size for adjustment (percent-based)

# ------------------------------------------------------------------
# ⚙️ Scenario quality filters
RR_MIN                      = 3.0              # Minimum structural RR ratio required
RR_MAX                      = 10.0             # Maximum structural RR ratio before applying partial/dynamic adjustment
ENTRY_CONFIRMATION_REQUIRED = "auto"           # Confirmation mode: 'trend', 'flex', False, or 'auto'
REQUIRE_VOLUME_SPIKE        = True             # Whether a volume spike is required for entry confirmation
FORCE_ENTRY_MIN_SCORE       = 3                # Minimum score to force scenario validation
FORCE_ENTRY_MIN_RR          = 1.8              # Minimum RR ratio to force scenario validation

# ------------------------------------------------------------------
# 📂 Data paths
LOG_PATH                    = "data/analytics_log.csv"  # Path for analytics logs (CSV)
DAILY_REJECTION_LIMIT = 10     # Maximum REJECTED scenarios per day before pausing analysis          
MAX_CONSECUTIVE_REJECTIONS = 3  # Maximum consecutive REJECTED scenarios before temporary skipping 
        
# This is NOT related to trading risk management.
# These limits serve to avoid noisy conditions where too many scenarios
# fail validation (poor market structure, excessive volatility, etc.).
#
# Purpose: maintain analysis hygiene and prevent spamming weak scenarios.
# ------------------------------------------------------------------
# 📢 Telegram notifications (optional)
TELEGRAM_BOT_TOKEN          = ""                # Leave empty if not using Telegram notifications
TELEGRAM_CHAT_ID            = ""
