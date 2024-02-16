from typing import Callable

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


def create_session_maker(data_base_name: str) -> Callable[[], Session]:
    engine = create_engine(f"sqlite:///{data_base_name}.db", echo=True)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


class Job(Base):  # pylint: disable=R0902
    __tablename__ = "jobs"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    title = Column("title", String)
    grade = Column("grade", String)
    salary = Column("salary", String)
    location = Column("location", String)
    company_name = Column("company_name", String)
    employment_type = Column("employment_type", String)
    industry = Column("industry", String)
    description = Column("description", String)
    link = Column("link", String)
    duties = Column("duties", String)

    def __init__(  # pylint: disable=R0913, R0914
        self,
        title: str,
        grade: str,
        salary: str,
        location: str,
        company_name: str,
        employment_type: str,
        industry: str,
        description: str,
        link: str,
        duties: str,
    ):
        self.title = title
        self.grade = grade
        self.salary = salary
        self.location = location
        self.company_name = company_name
        self.employment_type = employment_type
        self.industry = industry
        self.description = description
        self.link = link
        self.duties = duties

    def add_to_commit(self, session: Session) -> None:
        session.add(self)
