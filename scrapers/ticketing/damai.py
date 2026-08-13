import hashlib
import json
import os
import re
import time

from logger import get_logger
from scrapers.base import TicketingScraper

_log = get_logger(__name__)


class DamaiScraper(TicketingScraper):
    platform = "damai"
    base_url = "https://mtop.damai.cn"
    rate_limit = 3.0
    cookies = {
        "cookie2": os.environ.get("DAMAI_COOKIE2", ""),
        "_m_h5_tk": os.environ.get("DAMAI_M_H5_TK", ""),
    }
    APP_KEY = os.environ.get("DAMAI_APP_KEY")

    def _get_token(self) -> str:
        cookie = self.cookies.get("_m_h5_tk", "")
        m = re.search(r"([a-f0-9]+)_", cookie)
        if not m:
            raise RuntimeError("Damai _m_h5_tk cookie not found or invalid format")
        return m.group(1)

    def _sign(self, data: dict) -> dict:
        if not self.APP_KEY:
            raise RuntimeError("DAMAI_APP_KEY environment variable is not set")
        t = str(int(time.time() * 1000))
        token = self._get_token()
        data_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        raw = f"{token}&{t}&{self.APP_KEY}&{data_str}"
        # NOTE: MD5 为服务端要求的签名算法，无法单方面更换
        sign = hashlib.md5(raw.encode()).hexdigest()  # nosec B324  # MD5 required by Damai API signing
        return {
            "jsv": "2.7.2", "appKey": self.APP_KEY, "t": t, "sign": sign,
            "api": "mtop.alibaba.damai.detail.search.search", "v": "1.0",
            "type": "originaljson", "dataType": "json", "valueType": "original",
            "data": data_str, "forceAntiCreep": "true", "AntiCreep": "true",
            "useH5": "true",
        }

    async def _refresh_token(self):
        try:
            resp = await self.client.get(
                "/h5/mtop.alibaba.damai.detail.search.search/1.0/",
                params=self._sign({"keyword": "test", "pageIndex": 1, "pageSize": 1}),
                headers={"Referer": "https://m.damai.cn/"},
            )
            for c in resp.cookies:
                if c.name == "_m_h5_tk" and c.value:
                    self.cookies["_m_h5_tk"] = c.value
        except Exception as e:
            _log.warning(f"[damai] token refresh failed: {e}")

    async def scrape(self) -> list[dict]:
        results = []
        keywords = ["漫展", "二次元", "同人展", "Cosplay", "动漫"]
        for kw in keywords:
            for page in range(1, 6):
                raw = await self.fetch(
                    "/h5/mtop.alibaba.damai.detail.search.search/1.0/",
                    params=self._sign({"keyword": kw, "pageIndex": page, "pageSize": 30}),
                )
                data = self.parse(raw)
                if not data:
                    break
                results.extend(data)
                if len(data) < 30:
                    break
        return results

    def parse(self, raw: str) -> list[dict]:
        try:
            obj = json.loads(raw)
            ret = obj.get("ret", [])
            if isinstance(ret, str):
                ret = json.loads(ret)
            return ret if isinstance(ret, list) else ret.get("list", []) or []
        except (json.JSONDecodeError, KeyError, TypeError):
            return []
