import time
from abc import ABC, abstractmethod
from typing import Callable, override

import requests
from bs4 import BeautifulSoup, Tag
from colorama import Fore, Style
from sqlalchemy.orm import Session

from src.models import Job, create_session_maker


def alert(text: str) -> None:
    print(Fore.RED + text, Style.RESET_ALL)


class IScrapper(ABC):
    @abstractmethod
    def __init__(
        self,
        location: str,
        key_words: str,
        request_delay: int,
        job_parse_amount: int,
    ) -> None:
        ...

    @abstractmethod
    def scrape(self, db_name: str) -> None:
        ...

    @abstractmethod
    def set_request_delay(self, request_delay: int) -> None:
        ...

    @abstractmethod
    def set_job_parse_amount(self, job_parse_amount: int) -> None:
        ...

    @abstractmethod
    def set_key_words(self, key_words: str) -> None:
        ...

    @abstractmethod
    def set_location(self, location: str) -> None:
        ...

    @abstractmethod
    def get_jobs_parse_amount(self) -> int:
        ...

    @abstractmethod
    def set_retries(self, retries: int) -> None:
        ...


class LinkedInScrapper(IScrapper):
    @override
    def __init__(  # pylint: disable=R0913
        self,
        location: str = "",
        key_words: str = "",
        request_delay: int = 1,
        job_parse_amount: int = 10,
        retries: int = 10,
    ) -> None:
        self._location = location.replace(" ", "%20")
        self._key_words = key_words.replace(" ", "%20")
        self._request_delay = request_delay
        self._job_parse_amount = job_parse_amount
        self._retries: int = retries
        self._timeout = 1000

    def _get_link_to_page(self, start: int = 0) -> str:
        """
        Generates link to page with list of jobs
        :param start: index of first job to show
        """
        base_link = (
            "https://www.linkedin.com/jobs-guest/"
            + "jobs/api/seeMoreJobPostings/search?"
        )
        arguments = f"keywords={self._key_words}"
        arguments += f"&location={self._location}"
        arguments += f"&start={start}"
        return base_link + arguments

    @staticmethod
    def _get_job_links_from_page(page_html: bytes) -> list[str]:
        """
        Scrapes all links to jobs from given page
        :param page_html: source from which links will be parsed
        """
        soup = BeautifulSoup(page_html, "html.parser")
        class_id = "base-card__full-link"
        job_kinks = [
            job_node["href"].split("?")[0]
            for job_node in soup.find_all("a", class_=class_id)
        ]
        return job_kinks

    @staticmethod
    def _get_job_data_object(  # pylint: disable=R0914
        soup: BeautifulSoup, job_link: str
    ) -> Job:
        """
        Gets Data from page given in soup variable
        :param soup: source from which data will be parsed
        :param job_link: link to job which will be added into object data
        """
        def prettify(string: str) -> str:
            return string.strip("\n").strip(" ").strip("\n")

        def safe_find(name: str, class_: str) -> str:
            value = soup.find(name, class_=class_)
            if isinstance(value, Tag):
                return value.get_text()
            raise BrokenPipeError(
                "Something went wrong during job page parsing"
            )

        class_name = "top-card-layout__title"
        title = safe_find("h2", class_name)

        class_name = "description__job-criteria-text"
        grade, employment_type, industry, duties = map(
            Tag.get_text, soup.find_all("span", class_=class_name)
        )

        salary = "Not stated"  # implement celery scraping(I haven't found it)

        class_name = "topcard__flavor topcard__flavor--bullet"
        location = safe_find("span", class_name)

        class_name = "topcard__org-name-link topcard__flavor--black-link"
        company_name = safe_find("a", class_name)

        class_name = "show-more-less-html__markup"
        description = safe_find("div", class_name)

        return Job(
            title=title,
            grade=prettify(grade),
            salary=salary,
            location=prettify(location),
            company_name=prettify(company_name),
            employment_type=prettify(employment_type),
            industry=prettify(industry),
            description=prettify(description),
            link=job_link,
            duties=prettify(duties),
        )

    def _get_jobs_data(
        self,
        job_links: list[str],
        session: Session,
        on_save_function: Callable[[], None],
    ) -> None:
        """
        Parses and saves data from links given
        :param job_links: Links to job pages
        :param session: ORM session object used for saving data
        :param on_save_function: function that is called when data is saved
        """
        base_job_link = (
            "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/"
        )

        retries = self._retries

        while job_links and retries:
            print("requesting....", len(job_links))

            job_link = job_links.pop()

            print(base_job_link + job_link.split("-")[-1])

            page_html = requests.get(
                base_job_link + job_link.split("-")[-1],
                cookies={"lang": "v=2&lang=en-us"},
                timeout=self._timeout,
            ).content
            soup = BeautifulSoup(page_html, "html.parser")

            try:
                self._save_job_data(
                    self._get_job_data_object(soup=soup, job_link=job_link),
                    session,
                    on_save_function,
                )

                retries = self._retries

            except (
                ValueError,
                AttributeError,
                BrokenPipeError,
                ConnectionError,
            ) as exception:
                print(exception)
                retries -= 1
                job_links = [job_link] + job_links
            finally:
                time.sleep(self._request_delay)

    def _get_job_links(self) -> list[str]:
        """Gets links to jobs"""
        job_links: list[str] = []
        while len(job_links) < self._job_parse_amount:
            response = requests.get(
                self._get_link_to_page(start=len(job_links)),
                timeout=self._timeout,
            )
            if response.status_code == 400:
                break
            job_links += self._get_job_links_from_page(response.content)
            print(len(job_links))
            time.sleep(self._request_delay)
        return job_links

    @staticmethod
    def _save_job_data(
        job_data: Job, session: Session, on_save_function: Callable[[], None]
    ) -> None:
        """
        Saves Job info into database
        :param job_data: Job object to save
        :param session: ORM session object used for saving data
        :param on_save_function: function that is called when data is saved
        """
        job_data.add_to_commit(session=session)
        session.commit()
        on_save_function()

    @override
    def scrape(
        self, db_name: str, on_save_function: Callable[[], None] = lambda: None
    ) -> None:
        """
        Scrapes and saves data from website into database
        :param db_name: name of database to save
        :param on_save_function: function that is called when data is saved
        """
        alert("Started Scrapping")
        job_links = self._get_job_links()

        print(f"Scraped {len(job_links)} job links")
        self._job_parse_amount = len(job_links)

        session_maker = create_session_maker(db_name)
        with session_maker() as session:
            self._get_jobs_data(job_links, session, on_save_function)

    @override
    def set_request_delay(self, request_delay: int) -> None:
        self._request_delay = request_delay

    @override
    def set_job_parse_amount(self, job_parse_amount: int) -> None:
        self._job_parse_amount = job_parse_amount

    @override
    def set_key_words(self, key_words: str) -> None:
        self._key_words = key_words.replace(" ", "%20")

    @override
    def set_location(self, location: str) -> None:
        self._location = location.replace(" ", "%20")

    @override
    def get_jobs_parse_amount(self) -> int:
        return self._job_parse_amount

    @override
    def set_retries(self, retries: int) -> None:
        self._retries = retries


if __name__ == "__main__":
    parser = LinkedInScrapper(location="Germany", key_words="Python Developer")
    parser.scrape("jobs")
