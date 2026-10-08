**语言 / Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# ComiRadar

[![CI](https://github.com/dreamnight16/anime-con-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/dreamnight16/anime-con-radar/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-orange)](https://github.com/dreamnight16/anime-con-radar)

**自动发现未来 90 天内全国漫展、同人展、二次元演唱会等演出信息。**

抓取 B站会员购、大麦、秀动、猫眼、票星球、永乐等九大票务平台及微博、B站动态、小红书，统一规范化输出。

### 数据来源

Bilibili (会员购) · Damai (大麦) · Showstart (秀动) · Maoyan (猫眼) · Piaoxingqiu (票星球) · Yongle (永乐) · Weibo (微博) · Bilibili Dynamics · Xiaohongshu (小红书)

### 去重策略

两层去重：SHA256 指纹精确匹配 + 城市/日期/标题模糊合并，合并缺失字段。

## 使用

```bash
pip install -r requirements.txt
python main.py scrape   # 抓取所有平台
python main.py export   # 导出 events.json
python main.py notify   # 推送通知（需配置密钥）
python main.py run      # 一键三连
```

需要可选的模型提取时，执行 `pip install openai`（或 `uv sync --extra llm --no-install-project`）并设置 `DEEPSEEK_API_KEY`。没有 SDK 或密钥时，社交帖文使用确定性解析。

## Docker

```bash
# 构建并运行完整管线
docker compose run --rm comiradar

# 单独运行各步骤
docker compose run --rm scrape   # 仅抓取
docker compose run --rm export   # 仅导出
docker compose run --rm notify   # 仅通知

# 数据持久化于 ./data/
```

## 配置

编辑 `config.py` 设置通知密钥：

```python
NOTIFIERS = {
    "serverchan": {"key": "your-SendKey"},
    "bark": {"url": "https://api.day.app/your-key"},
}
```

## 环境变量

| 变量名 | 说明 |
|--------|------|
| `BILI_BUVID3` | B站 cookies 中的 `buvid3` |
| `BILI_SESSDATA` | B站 cookies 中的 `SESSDATA` |
| `BILI_BILI_JCT` | B站 cookies 中的 `bili_jct` |
| `DAMAI_M_H5_TK` | 大麦 cookies 中的 `m_h5_tk` |
| `DAMAI_COOKIE2` | 大麦 cookies 中的 `cookie2` |
| `DEEPSEEK_API_KEY` | 可选的 DeepSeek 密钥，用于结构化社交内容提取；未设置时使用确定性解析 |
| `COMI_EXPORT_PATH` | 导出路径（可选，默认输出到项目目录） |

## 与博客集成

本仓库通过 git submodule 引入 [Blog-mizuki](https://github.com/dreamnight16/Blog-mizuki)，由 GitHub Actions 定时运行，数据自动更新到 [演出页面](https://comi.dreamnight.net.cn)。

## 技术栈

- **抓取**: Python 3.11+ · Playwright · HTTPX
- **存储**: SQLite
- **调度**: GitHub Actions (cron)
- **集成**: Git submodule → Astro 博客

## 相关项目

- [chinese-scraper-utils](https://github.com/dreamnight16/chinese-scraper-utils) — 从本项目抽离的通用工具库
- [Blog-mizuki](https://github.com/dreamnight16/Blog-mizuki) — 演出数据展示在 dreamnight.net.cn/anime-events（当前）
- [myBlog](https://github.com/dreamnight16/myBlog) — 旧博客（已归档）

## 许可证

MIT

---

<div align="center">

**Language / 语言 / 言語**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
