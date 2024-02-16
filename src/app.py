import csv
import time
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox
from typing import Any

from customtkinter import CTk
from customtkinter import CTkButton as Button
from customtkinter import CTkEntry as Entry
from customtkinter import CTkLabel as Label
from customtkinter import CTkOptionMenu as OptionMenu
from customtkinter import CTkProgressBar as ProgressBar
from customtkinter import CTkTabview as Tabview
from sqlalchemy import create_engine, text

from src.scraper import LinkedInScrapper


@dataclass
class FormEntry:
    entry_object: Entry = None
    label: str = ""
    base_value: str = ""


class TabView(Tabview):  # type: ignore  # pylint: disable=R0901,R0902
    def __init__(self, master: Any, **kwargs: dict[str, str]) -> None:
        super().__init__(master, **kwargs)

        # create tabs
        self.add("Scrapper")
        self.add("Data")

        self.scrapper = LinkedInScrapper()
        self.parsed_jobs = 0
        self.jobs_to_parse_amount = 0

        self.scrapper_tab = self.tab("Scrapper")
        self.data_tab = self.tab("Data")

        self.form: dict[str, FormEntry] = {
            "location": FormEntry(label="Location", base_value="Potsdam"),
            "key_words": FormEntry(
                label="Search Keywords", base_value="Python Developer"
            ),
            "request_delay": FormEntry(
                label="Request Delay(Seconds)", base_value="1"
            ),
            "job_parse_amount": FormEntry(
                label="Job Parse Amount", base_value="10"
            ),
            "retries": FormEntry(label="Retries", base_value="20"),
            "db_name": FormEntry(label="Data Base name", base_value="mydb"),
        }
        self.create_input_form()
        self.set_default_values_to_form()

        # add widgets on tabs
        self.scrape_button = Button(
            self.scrapper_tab,
            text="Scrape",
            command=self.on_scrape_button_clicked,
        )
        self.scrape_button.grid(row=0, column=3, pady=20, padx=10)

        self.progressbar = ProgressBar(
            self.scrapper_tab, orientation="horizontal"
        )
        self.progressbar.set(0)
        self.progressbar.grid(
            row=len(self.form) + 1, column=1, pady=20, padx=10
        )

        self.option_menu = OptionMenu(self.data_tab, values=[])
        self.option_menu.grid(row=1, column=0, pady=20, padx=10)

        self.refresh_button = Button(
            self.data_tab,
            text="Refresh",
            command=self.on_refresh_button_clicked,
        )
        self.refresh_button.grid(row=0, column=0, pady=20, padx=10)

        self.export_button = Button(
            self.data_tab,
            text="Export",
            command=self.on_export_button_clicked,
        )
        self.export_button.grid(row=1, column=1, pady=20, padx=10)

        self.on_refresh_button_clicked()
        self.option_menu.set("Choose file to export")

    def create_input_form(self) -> None:
        for index, widget_name in enumerate(self.form.keys()):
            widget = Entry(
                self.scrapper_tab,
                placeholder_text=self.form[widget_name].label,
                width=200,
            )
            widget.grid(row=index, column=1, pady=20, padx=10)

            label = Label(self.scrapper_tab, text=self.form[widget_name].label)
            label.grid(row=index, column=0, pady=20, padx=10)
            self.form[widget_name].entry_object = widget

    def on_export_button_clicked(self) -> None:
        if self.option_menu.get() == "Choose file to export":
            messagebox.showerror("Python Error", "Choose file to export")
        else:
            db_name = self.option_menu.get().replace(".db", "")
            engine = create_engine(url=f"sqlite:///{db_name}.db")

            with engine.connect() as connection:
                query = "SELECT * FROM jobs"
                result = connection.execute(text(query))

                with open(
                    f"{db_name}.csv", "w", newline="", encoding="utf-8"
                ) as csvfile:
                    fieldnames = list(result.keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                    for elem in result:
                        writer.writerow(
                            {
                                fieldnames[i]: elem[i]
                                for i in range(len(fieldnames))
                            }
                        )

    def on_scrape_button_clicked(self) -> None:
        messagebox.showinfo("Scraping...", "Press Ok to start scraping")

        self.parsed_jobs = 0
        self.jobs_to_parse_amount = int(
            self.form["job_parse_amount"].entry_object.get()
        )
        self.scrapper.set_location(self.form["location"].entry_object.get())
        self.scrapper.set_key_words(self.form["key_words"].entry_object.get())
        self.scrapper.set_request_delay(
            int(self.form["request_delay"].entry_object.get())
        )
        self.scrapper.set_job_parse_amount(self.jobs_to_parse_amount)
        self.scrapper.set_retries(int(self.form["retries"].entry_object.get()))
        db_name = self.form["db_name"].entry_object.get()

        self.scrapper.scrape(
            db_name=db_name, on_save_function=self.on_job_scrape
        )

    def on_refresh_button_clicked(self) -> None:
        options = [
            i.name
            for i in Path(__file__).parent.iterdir()
            if i.name.endswith(".db")
        ]
        self.option_menu.configure(values=options)

    def on_job_scrape(self) -> None:
        self.parsed_jobs += 1
        value = (self.parsed_jobs / self.jobs_to_parse_amount) * 100
        self.progressbar.set(value)
        time.sleep(1)

    def set_default_values_to_form(self) -> None:
        for form_entry in self.form.values():
            form_entry.entry_object.insert(0, form_entry.base_value)

    def bind(
        self, sequence: Any = None, command: Any = None, add: Any = None
    ) -> None:
        super().bind(sequence=sequence, command=command, add=add)

    def unbind(self, sequence: Any = None, funcid: Any = None) -> None:
        super().unbind(sequence=sequence, funcid=funcid)


class App(CTk):  # type: ignore
    def __init__(self, geometry: str):
        super().__init__()
        self.geometry(geometry)

        self.tab_view = TabView(master=self)
        self.tab_view.pack()


if __name__ == "__main__":
    app = App(geometry="900x700")
    app.mainloop()
