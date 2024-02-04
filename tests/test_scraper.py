from src.scraper import LinkedInScrapper


def test_init() -> None:
    assert LinkedInScrapper(key_words="Python Developer", location="Germany")


# def test_scrape() -> None:
#     scraper = LinkedInScrapper(key_words="Python Developer",
#     location="Germany")
#     scraper.set_job_parse_amount(1)
#     jobs_list_url = "https://www.linkedin.com/jobs-guest/jobs/api/
#     seeMoreJobPostings/search?keywords=Python%20Developer&location=Germany&start=0"
#     response_jobs_list = Path(__file__).parent / "jobs_list_page.txt"
#     with requests_mock.Mocker() as mock:
#         mock.get(jobs_list_url, text=response_jobs_list.read_text())
#         scraper.scrape()
