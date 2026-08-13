# Contributing to ComiRadar

Thanks for your interest in contributing!

## Getting Started

```bash
git clone https://github.com/dreamnight16/anime-con-radar.git
cd ComiRadar
pip install -r requirements.txt
pytest
```

## Development Workflow

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Run `pytest` to verify all tests pass
4. Add tests for new functionality
5. Commit using [Conventional Commits][conv] format
6. Push and open a pull request

## Commit Convention

```
feat: add Maoyan scraper city/date/price fields
fix: prevent dedup merge direction bug
refactor: unify scrapers under AbstractScraper
test: add scraper integration tests
docs: update README with new platform support
```

Types: `feat` `fix` `refactor` `test` `docs` `chore` `perf` `ci`

## Code Style

- Full type hints on all public functions
- Use Pydantic models for data structures
- Scrapers must extend `AbstractScraper`
- Functions under 50 lines; files under 800 lines
- Follow PEP 8

## Adding a New Scraper

1. Create a new worker file in the project root
2. Extend `AbstractScraper` with `fetch_events()` method
3. Register in `main.py` scraper list
4. Add tests for dedup, normalization, edge cases

## Pull Request Checklist

- [ ] All tests pass (`pytest`)
- [ ] New scrapers extend `AbstractScraper`
- [ ] Type hints added for new public APIs
- [ ] README updated with new platform support
- [ ] `.gitignore` updated if new output files added

## Questions?

Open a [discussion](https://github.com/dreamnight16/anime-con-radar/discussions).

[conv]: https://www.conventionalcommits.org/
