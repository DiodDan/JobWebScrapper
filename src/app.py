from dataclasses import dataclass

from customtkinter import CTk
from customtkinter import CTkButton as Button
from customtkinter import CTkEntry as Entry
from customtkinter import CTkLabel as Label
from customtkinter import CTkProgressBar as ProgressBar
from customtkinter import CTkTabview as Tabview

from src.scraper import LinkedInScrapper


@dataclass
class FormEntry:
    entry_object: Entry | None = None
    label: str = ""
    base_value: str = ""


class TabView(Tabview):
    def __init__(self, master, **kwargs):
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

    def on_scrape_button_clicked(self):
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

    def on_job_scrape(self):
        print(100000000000000000000000)
        self.parsed_jobs += 1
        value = (self.parsed_jobs / self.jobs_to_parse_amount) * 100
        self.progressbar.set(value)

    def set_default_values_to_form(self) -> None:
        for form_entry in self.form.values():
            form_entry.entry_object.insert(0, form_entry.base_value)


class App(CTk):
    def __init__(self, geometry: str):
        super().__init__()
        self.geometry(geometry)

        self.tab_view = TabView(master=self)
        self.tab_view.pack()


if __name__ == "__main__":
    app = App(geometry="900x700")
    app.mainloop()
