import os
from pathlib import Path

from chinese_scraper_utils import UA_POOL  # noqa: F401 — re-exported for scrapers.base

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "events.db"
HEALTH_PATH = BASE_DIR / "health.json"
EXPORT_PATH = Path(os.environ.get("COMI_EXPORT_PATH", BASE_DIR / "events.json"))
DAYS_AHEAD = 90
SCRAPE_TIMEOUT = 30
MAX_RETRIES = 3
RATE_LIMIT = 2.0

NOTIFIERS: dict[str, dict] = {
    "serverchan": {"key": os.environ.get("SERVERCHAN_KEY", "")},
    "bark": {"url": os.environ.get("BARK_URL", "")},
}

# B站 Cookie 用于绕过风控。在浏览器登录 show.bilibili.com 后，
# F12 → Application → Cookies → 复制 buvid3, SESSDATA, bili_jct
BILIBILI_COOKIES: dict[str, str] = {
    "buvid3": os.environ.get("BILI_BUVID3", ""),
    "SESSDATA": os.environ.get("BILI_SESSDATA", ""),
    "bili_jct": os.environ.get("BILI_BILI_JCT", ""),
}


def validate_config() -> list[str]:
    """Check required config at startup. Returns list of warnings."""
    warnings: list[str] = []
    if not os.environ.get("DEEPSEEK_API_KEY"):
        warnings.append("DEEPSEEK_API_KEY not set — LLM extraction & hotspot discovery disabled")
    if not any(BILIBILI_COOKIES.values()):
        warnings.append("BILIBILI_COOKIES not set — Bilibili scraper may fail")
    if not os.environ.get("DAMAI_APP_KEY"):
        warnings.append("DAMAI_APP_KEY not set — Damai scraper will fail")
    sc_key = NOTIFIERS.get("serverchan", {}).get("key", "")
    bark_url = NOTIFIERS.get("bark", {}).get("url", "")
    if not sc_key and not bark_url:
        warnings.append("No notifiers configured — push notifications disabled")
    return warnings
