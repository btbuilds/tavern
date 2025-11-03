from enum import Enum
from core.utils import format_date
from textual import on
from textual.app import ComposeResult
from textual.widgets import Button, Label, Input, Select, ListView, ListItem, Rule, TextArea
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from core.manager import SearchType

class PopupType(Enum):
    ERROR = "error"
    SUCCESS = "success"

class PopupScreen(ModalScreen):
    CSS_PATH = "../style/popup.tcss"
    def __init__(self, message: str, type: PopupType):
        super().__init__()
        self.message = message
        self.type = type

    def compose(self) -> ComposeResult:
        popup_classes = "popup-error" if self.type == PopupType.ERROR else "popup-success"
        with Vertical(id="popup", classes=popup_classes):
            yield Label(content=self.message)
            yield Button("Close", id="close", variant="success")
    
    @on(Button.Pressed, "#close")
    def close_screen(self):
        if self.type == PopupType.SUCCESS:
            self.app.pop_screen() # Close the modal
            self.app.pop_screen() # Close the screen we were on
        elif self.type == PopupType.ERROR:
            self.app.pop_screen() # Close only the modal

class CustomerLookupScreen(ModalScreen):
    CSS_PATH = "../style/custlookup.tcss"

    def compose(self) -> ComposeResult:        
        with Vertical(id="search-customer-content"):
            # Search section
            with Horizontal(id="search-section"):
                yield Select(
                    [("Code", "code"), 
                    ("Name", "name"), 
                    ("Email", "email"), 
                    ("Phone", "phone")],
                    id="search-type",
                    value="code"
                )
                yield Input(placeholder="Search...", id="search-input")
                yield Button("Search", id="search-btn", variant="primary")
            
            # Results section
            with Vertical(id="results-section"):
                yield Label("Search Results")
                yield ListView(id="customer-results")
            
            with Horizontal(id="bottom-btns"):
                yield Button("Select Customer", id="select-btn", classes="bottom-btn", variant="success", disabled=True)
                yield Button("Cancel", id="cancel-btn", classes="bottom-btn", variant="error")

    def on_mount(self) -> None:
        self.current_customer_code = None
    
    @on(Button.Pressed, "#cancel-btn")
    def close_screen(self):
        self.dismiss("")
    
    def search_customers(self):
        """Search for customers that match query and load matches in to list"""
        results_list = self.query_one("#customer-results", ListView)
        results_list.clear()
        query = self.query_one("#search-input", Input).value
        search_type = self.query_one("#search-type", Select).value
        customers = self.app.manager.customers.search_customers(query, SearchType(search_type)) # type: ignore[attr-defined]

        for customer in customers:
            item = ListItem(Label(f"{customer.name} ({customer.code})"))
            item.customer_id = customer.id # type: ignore[attr-defined]
            results_list.append(item)
    
    @on(Button.Pressed, "#search-btn")
    @on(Input.Submitted, "#search-input")
    def search(self):
        self.search_customers()
    
    @on(ListView.Selected, "#customer-results")
    def select_customer(self, event: ListView.Selected) -> None:
        selected_item = event.item
        customer_id = selected_item.customer_id # type: ignore[attr-defined]

        customer = self.app.manager.customers.find_by_id(customer_id) # type: ignore[attr-defined]

        if customer:
            self.query_one("#select-btn", Button).disabled = False
            self.current_customer_code = customer.code
    
    @on(Button.Pressed, "#select-btn")
    def return_customer(self):
        self.dismiss(self.current_customer_code)

class NoteEntryPopup(ModalScreen):
    CSS_PATH = "../style/noteentrypopup.tcss"

    def __init__(self, ticket_id: str):
        super().__init__()
        self.ticket_id = ticket_id

    def compose(self) -> ComposeResult:
        with Vertical(id="note-entry-section"):
            yield Label("Note Entry")
            yield Rule(line_style="heavy")
            yield Label("Previous Notes")
            yield ListView(id="previous-notes")
            yield Rule(line_style="heavy")
            yield Label("Notes")
            yield TextArea(placeholder="Notes...", id="notes-input")
            with Horizontal(id="text-boxes"):
                with Vertical(id="hours-col"):
                    yield Label("Hours")
                    yield Input(placeholder="Hours (example: 1.25)", type="number", id="hours-input")
                with Vertical(id="mileage-col"):
                    yield Label("Mileage")
                    yield Input(placeholder="Mileage", type="integer", id="mileage-input")
            with Horizontal(id="buttons"):
                yield Button("Save Note", id="save", variant="primary", disabled=True)
                yield Button("Cancel", id="cancel", variant="error")
    
    def on_mount(self) -> None:
        notes_list_view = self.query_one("#previous-notes", ListView)
        notes_list = self.app.manager.tickets.get_ticket_notes(self.ticket_id) # type: ignore[attr-defined]
        for note in notes_list:
            formatted_date = format_date(note["date_created"])
            if len(note["notes"]) > 80:
                item = ListItem(Label(f"{formatted_date} - {note["notes"][:80]}..."))
            else:
                item = ListItem(Label(f"{formatted_date} - {note["notes"]}"))
            notes_list_view.append(item)

    @on(Input.Changed)
    @on(TextArea.Changed)
    def check_valid(self) -> None:
        if self.validate_notes_form():
            self.query_one("#save", Button).disabled = False
        else:
            self.query_one("#save", Button).disabled = True

    @on(Button.Pressed, "#cancel")
    def close_screen(self):
        self.dismiss("")
    
    @on(Button.Pressed, "#save")
    def save_notes(self):
        is_valid = self.validate_notes_form()
        if not is_valid:
            self.app.push_screen(PopupScreen("Please enter notes before saving.", PopupType.ERROR))
            return
        
        data = self.gather_form_data()
        if data:
            try:
                data["ticket_id"] = self.ticket_id
                self.app.manager.tickets.add_time_entry(**data) # type: ignore[attr-defined]
                self.app.push_screen(PopupScreen(f"Notes successfully entered!", PopupType.SUCCESS))
            except Exception as e:
                self.app.push_screen(PopupScreen(f"Error: {e}", PopupType.ERROR))

    def gather_form_data(self) -> dict:
        """Extract all form data into a dict"""
        notes = self.query_one("#notes-input", TextArea).text
        ticket_time = "0"
        mileage = "0"
        if self.query_one("#hours-input", Input).value:
            ticket_time = self.query_one("#hours-input", Input).value
        if self.query_one("#mileage-input", Input).value:
            mileage = self.query_one("#mileage-input", Input).value
        current_tech = self.app.current_technician.username # type: ignore[attr-defined]
        tech_id = self.app.manager.technicians.get_technician_id(current_tech) # type: ignore[attr-defined]
        
        data = {"technician":tech_id,
                "notes":notes,
                "ticket_time":ticket_time,
                "mileage":mileage}
        return data
    
    def validate_notes_form(self):
        if self.query_one("#notes-input", TextArea).text: # Mileage and Ticket Time are optional
            return True
        else:
            return False