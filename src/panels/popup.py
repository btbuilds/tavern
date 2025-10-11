from enum import Enum
from textual import on
from textual.app import ComposeResult
from textual.widgets import Button, Label, Input, Select, ListView, ListItem
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
        self.app.pop_screen()
    
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