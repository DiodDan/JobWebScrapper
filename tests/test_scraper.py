from pathlib import Path

import requests_mock
from customtkinter import CTk
from sqlalchemy import create_engine, text

from src.app import App
from src.scraper import LinkedInScrapper


def test_init() -> None:
    assert LinkedInScrapper(key_words="Python Developer", location="Germany")


def test_scrape() -> None:
    scraper = LinkedInScrapper(
        key_words="Python Developer", location="Germany"
    )
    scraper.set_job_parse_amount(1)
    jobs_list_url = scraper._get_link_to_page()  # pylint: disable=W0212
    jobs_page_url = (
        "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/3810757390"
    )
    response_jobs_list = (
        Path(__file__).parent / "test_materials/jobs_list_page.html"
    )
    response_job_page = Path(__file__).parent / "test_materials/job_page.html"
    with requests_mock.Mocker() as mock:
        mock.get(jobs_list_url, text=response_jobs_list.read_text())
        mock.get(jobs_page_url, text=response_job_page.read_text())
        scraper.scrape(db_name="test_db")

    with create_engine(url="sqlite:///test_db.db").connect() as connection:
        job_data_path = Path(__file__).parent / "test_materials/job_data.txt"

        for elem in connection.execute(text("SELECT * FROM jobs")):
            job_data = job_data_path.read_text().split("\n")
            assert [str(elem[i]) == str(job_data[i]) for i in range(len(elem))]
        connection.execute(text("DROP TABLE jobs"))
        connection.commit()


def test_app() -> None:
    app = App(geometry="900x700")

    assert isinstance(app, CTk)
