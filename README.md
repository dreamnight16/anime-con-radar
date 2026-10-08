**Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# ComiRadar

[![CI](https://github.com/dreamnight16/anime-con-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/dreamnight16/anime-con-radar/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-orange)](https://github.com/dreamnight16/anime-con-radar)

**Automatically discovers anime cons, doujin fairs, and ACG concerts across China for the next 90 days.**

Scrapes 9 ticketing platforms (Bilibili, Damai, Showstart, Maoyan, Piaoxingqiu, Yongle, etc.) plus Weibo, Bilibili feeds, and Xiaohongshu. Each platform has its own parser, unified into a normalized event schema.

### Data Sources

Bilibili (会员购) · Damai (大麦) · Showstart (秀动) · Maoyan (猫眼) · Piaoxingqiu (票星球) · Yongle (永乐) · Weibo (微博) · Bilibili Dynamics · Xiaohongshu (小红书)

### Deduplication Strategy

Two-layer dedup: SHA256 fingerprint for exact matches + fuzzy merge on city/date/title for near-duplicates. Merged events combine fields from multiple sources.

## Usage

```bash
pip install -r requirements.txt
python main.py scrape   # Scrape all platforms
python main.py export   # Export events.json
python main.py notify   # Push notifications (configure keys first)
python main.py run      # All three steps
```

For optional model extraction, install `pip install openai` (or `uv sync --extra llm --no-install-project`) and set `DEEPSEEK_API_KEY`. Without the SDK or key, social posts use deterministic parsing.

## Docker

```bash
# Build and run the full pipeline
docker compose run --rm comiradar

# Run individual steps
docker compose run --rm scrape   # scrape only
docker compose run --rm export   # export only
docker compose run --rm notify   # notifications only

# Data persists in ./data/
```

## Configuration

Edit `config.py` to set notification keys:

```python
NOTIFIERS = {
    "serverchan": {"key": "your-SendKey"},
    "bark": {"url": "https://api.day.app/your-key"},
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BILI_BUVID3` | Bilibili cookie `buvid3` |
| `BILI_SESSDATA` | Bilibili cookie `SESSDATA` |
| `BILI_BILI_JCT` | Bilibili cookie `bili_jct` |
| `DAMAI_M_H5_TK` | Damai cookie `m_h5_tk` |
| `DAMAI_COOKIE2` | Damai cookie `cookie2` |
| `DEEPSEEK_API_KEY` | Optional DeepSeek key for structured social-post extraction; deterministic parsing is used without it |
| `COMI_EXPORT_PATH` | Export path (optional, defaults to project directory) |

## Blog Integration

This repo is included as a git submodule in [Blog-mizuki](https://github.com/dreamnight16/Blog-mizuki). GitHub Actions runs the scraper on schedule, and results auto-sync to the [events page](https://comi.dreamnight.net.cn).

## Tech Stack

- **Scraping**: Python 3.11+ · Playwright · HTTPX
- **Storage**: SQLite
- **Scheduling**: GitHub Actions (cron)
- **Integration**: Git submodule → Astro blog

## Related

- [chinese-scraper-utils](https://github.com/dreamnight16/chinese-scraper-utils) — Shared utilities extracted from this project
- [Blog-mizuki](https://github.com/dreamnight16/Blog-mizuki) — Events data displayed at dreamnight.net.cn/anime-events (current)
- [myBlog](https://github.com/dreamnight16/myBlog) — Previous blog (archived)

## License

MIT

---

<div align="center">

**Language / 语言 / 言語**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
