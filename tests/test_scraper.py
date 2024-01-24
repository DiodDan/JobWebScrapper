from src.scraper import dummy


def test_init() -> None:
    assert dummy() == 1
