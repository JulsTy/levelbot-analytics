from __future__ import annotations
import json
import hashlib
import hmac
import time
from typing import Any, Dict, Final, Optional
from urllib.parse import quote_plus

import requests
from requests.adapters import HTTPAdapter, Retry

from config import API_KEY, API_SECRET
from utils.logger import logger

# ------------------------------------------------------------------
TIMEOUT: Final[int] = 5        # seconds per HTTP request
BASE_URL: Final[str] = "https://open-api.bingx.com"


class BingXAPI:
    """Lightweight wrapper around BingX swap endpoints (signed)."""

    def __init__(self, api_key: str, api_secret: str) -> None:
        self.api_key = api_key
        self.api_secret = api_secret.encode()

        # single Session with retry policy
        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(500, 502, 503, 504),
            allowed_methods=("GET", "POST"),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)

    def _sign(self, query: str) -> str:
        signature = hmac.new(self.api_secret, query.encode("utf-8"), hashlib.sha256).hexdigest()
        return signature

    def _headers(self) -> Dict[str, str]:
        return {
            "X-BX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        ordered_keys: Optional[list[str]] = None
    ) -> dict:
        if params is None:
            params = {}

        for k, v in params.items():
            params[k] = str(v).lower() if isinstance(v, bool) else str(v)

        if ordered_keys:
            for key in ordered_keys:
                if key not in params:
                    raise KeyError(f"Missing expected param: '{key}' for signing")
            query_string = "&".join(f"{key}={quote_plus(params[key])}" for key in ordered_keys)
        else:
            query_string = "&".join(f"{key}={quote_plus(params[key])}" for key, v in sorted(params.items()))

        signature = self._sign(query_string)
        params["signature"] = signature

        url = BASE_URL + path
        headers = self._headers()

        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params, timeout=TIMEOUT)
            else:
                response = self.session.post(url, headers=headers, data=params, timeout=TIMEOUT)
            return response.json()
        except ValueError:
            logger.error("Non-JSON response from BingX: %s", response.text)
            return {"code": -1, "msg": response.text}
        except requests.RequestException as e:
            logger.error("Network error BingX: %s", e)
            return {"code": -1, "msg": str(e)}

    
    def get_balance(self) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/openApi/swap/v2/user/balance",
            {
                "recvWindow": "60000",
                "timestamp": str(int(time.time() * 1000))
            },
            ["recvWindow", "timestamp"]
        )

    def get_price(self, symbol: str) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/openApi/swap/v2/quote/price",
            {
                "symbol": symbol,
                "recvWindow": "60000",
                "timestamp": str(int(time.time() * 1000))
            },
            ["symbol", "recvWindow", "timestamp"]
        )

    

api = BingXAPI(API_KEY, API_SECRET)




# ---------------------------------------------------------------------------
# Binance klines helper reusing same session (no key required)
# ---------------------------------------------------------------------------

class BinanceWrapper:
    def __init__(self):
        self.session = requests.Session()
        self.kline_url = "https://api.binance.com/api/v3/klines"

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 200):
        s = symbol.replace("-", "")
        try:
            r = self.session.get(
                self.kline_url,
                params={"symbol": s, "interval": interval, "limit": limit},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            logger.error("Binance klines error: %s", e)
            return None


# default instance creator (so main.py can stay concise)
api = BingXAPI(API_KEY, API_SECRET)
binance = BinanceWrapper()
