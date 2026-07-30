**語言 / Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# ComiRadar

[![CI](https://github.com/sixtdreanight/anime-con-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/sixtdreanight/anime-con-radar/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-orange)](https://github.com/sixtdreanight/anime-con-radar)

**自動發現未來 90 天內全國漫展、同人展、二次元演唱會等演出資訊。**

擷取 B站會員購、大麥、秀動、貓眼、票星球、永樂等九大票務平台及微博、B站動態、小紅書，統一規範化輸出。

### 資料來源

Bilibili (會員購) · Damai (大麥) · Showstart (秀動) · Maoyan (貓眼) · Piaoxingqiu (票星球) · Yongle (永樂) · Weibo (微博) · Bilibili Dynamics · Xiaohongshu (小紅書)

### 去重策略

兩層去重：SHA256 指紋精確匹配 + 城市/日期/標題模糊合併，合併缺失欄位。

## 使用

```bash
pip install -r requirements.txt
python main.py scrape   # 擷取所有平台
python main.py export   # 匯出 events.json
python main.py notify   # 推送通知（需設定金鑰）
python main.py run      # 一鍵三連
```

## Docker

```bash
# 構建並執行完整管線
docker compose run --rm comiradar

# 單獨執行各步驟
docker compose run --rm scrape   # 僅擷取
docker compose run --rm export   # 僅匯出
docker compose run --rm notify   # 僅通知

# 資料持久化於 ./data/
```

## 設定

編輯 `config.py` 設定通知金鑰：

```python
NOTIFIERS = {
    "serverchan": {"key": "your-SendKey"},
    "bark": {"url": "https://api.day.app/your-key"},
}
```

## 環境變數

| 變數名 | 說明 |
|--------|------|
| `BILI_BUVID3` | B站 cookies 中的 `buvid3` |
| `BILI_SESSDATA` | B站 cookies 中的 `SESSDATA` |
| `BILI_BILI_JCT` | B站 cookies 中的 `bili_jct` |
| `DAMAI_M_H5_TK` | 大麥 cookies 中的 `m_h5_tk` |
| `DAMAI_COOKIE2` | 大麥 cookies 中的 `cookie2` |
| `DEEPSEEK_API_KEY` | DeepSeek API 金鑰（用於 AI 資訊提取） |
| `COMI_EXPORT_PATH` | 匯出路徑（可選，預設輸出到專案目錄） |

## 與部落格整合

本倉庫透過 git submodule 引入 [Blog-mizuki](https://github.com/sixtdreanight/Blog-mizuki)，由 GitHub Actions 定時執行，資料自動更新到 [演出頁面](https://dreamnight.net.cn/anime-events)。

## 技術棧

- **擷取**: Python 3.11+ · Playwright · HTTPX
- **儲存**: SQLite
- **排程**: GitHub Actions (cron)
- **整合**: Git submodule → Astro 部落格

## 相關專案

- [chinese-scraper-utils](https://github.com/sixtdreanight/chinese-scraper-utils) — 從本專案抽離的通用工具庫
- [Blog-mizuki](https://github.com/sixtdreanight/Blog-mizuki) — 演出資料展示在 dreamnight.net.cn/anime-events（當前）
- [myBlog](https://github.com/sixtdreanight/myBlog) — 舊部落格（已歸檔）

## 授權條款

MIT

---

<div align="center">

**Language / 語言**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
