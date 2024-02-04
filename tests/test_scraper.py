from src.scraper import LinkedInScrapper


def test_init() -> None:
    assert LinkedInScrapper(key_words="Python Developer", location="Germany")