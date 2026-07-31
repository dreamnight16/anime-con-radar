# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] - 2026-06-05

### Security

- Remove hardcoded Damai APP_KEY default (CRITICAL — now requires an environment variable)
- URL-encode Bark notification messages to prevent injection
- Move ServerChan key from the URL path into the POST body
- Sanitize HTML/script tags from event data before JSON export
- Add shell metacharacter validation and explicit `shell=False` to subprocess execution
- Add explicit `verify=True` to all httpx clients

### Changed

- Document SHA256 fingerprint truncation used for dedup (non-cryptographic)
- Complete zh-Hant and ja README translations

### Fixed

- Remove deprecated license classifier (PEP 639)

### Added

- Community health files: CODE_OF_CONDUCT.md, SECURITY.md, CONTRIBUTING.md, .editorconfig
- GitHub issue/PR templates (`.github/`)
- Multi-language READMEs (EN, zh-CN, zh-Hant, JA)
- PyPI publish CI job on tag push (added and subsequently reverted in the same release)

## [0.3.0] - 2026-05-24

### Changed

- Unify the scraper base class and add `SubprocessScraper` with structured NDJSON subprocess IPC
- Bilibili, Nyato, Chinajoy, and CIEFC scrapers now inherit `SubprocessScraper`, gaining rate limiting, retry logic, and circuit breaker integration
- Enrich the Maoyan scraper to attempt extracting city/date/venue/price fields
- Replace `__import__` calls with proper imports in `main.py` and `dedup.py`; remove no-op `session.merge` in `store.py`

### Added

- Extract CIEFC's embedded Playwright script into `_ciefc_worker.py`
- GitHub Actions CI workflow running pytest on Python 3.11/3.12/3.13

### Removed

- Dead `_ai_worker.py` and unused variable in `_playwright_worker.py`

## [0.1.1] - 2026-05-24

### Security

- Fix 22 issues from code audit:
  - Add `.env` to `.gitignore` to prevent credential leaks
  - Remove auto `pip install` from `setup_cookies.py` (supply chain risk); cookies now read via stdin with file mode 600
  - Fix dedup merge direction bug where high-confidence events were discarded
  - Annotate Damai MD5 signing risk and move APP_KEY to an environment variable
  - Add IntegrityError handling in `store.py`, enforce `scraped_at` type safety, switch `utcnow()` to `timezone.utc`
  - Tighten dedup window (same-month to ±3-day) and prefix match (6 to 4 chars)
  - Add empty ID → UUID fallback and exception logging in `normalizer.py`, dynamic year in `_playwright_worker.py`, disable redirects and add jitter to backoff in `base.py`

### Changed

- Migrate to chinese-scraper-utils v0.2.1 — `EventExtractor` replaces the `_ai_worker` subprocess in the Weibo scraper
- Switch shared utilities (hash/date/city/category/UA) to cn-scraper-utils imports, removing ~120 lines of duplicated code
- Replace raw httpx calls in `_ai_worker.py` with DeepSeekClient
- Add English to the README (bilingual), humanize the English blurb, and add a Related projects section

### Added

- `pipeline/hotspot_discovery.py` — auto-discover events from social media
- MIT LICENSE

### Fixed

- Remove `_category.py` — business logic belongs in ComiRadar, not the shared library

## [0.1.0] - 2026-05-20

### Added

- Initial release — anime event scraper for China
- Bilibili scraper using the listV2 API with a subprocess worker, cookie support, anti-bot headers, and detail enrichment
- Weibo scraper via Playwright with a combined pipeline
- Nyato, Chinajoy, and CIEFC scrapers with venue schedules
- Multi-source dedup
- AI extractor with knowledge reasoning (deepseek-v4-flash) and future-only filtering
- Damai MTOP signing
- Cookie auto-extract script and `.env` support
- Health checks and stats
- 46 unit tests
- README
