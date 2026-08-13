from config import DB_PATH, MAX_RETRIES, RATE_LIMIT, SCRAPE_TIMEOUT


def test_scrape_timeout():
    assert SCRAPE_TIMEOUT == 30


def test_max_retries():
    assert MAX_RETRIES == 3


def test_rate_limit():
    assert RATE_LIMIT == 2.0


def test_db_path_is_set():
    assert DB_PATH.name == "events.db"
