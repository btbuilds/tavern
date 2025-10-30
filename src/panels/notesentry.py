from textual import on
from textual.app import ComposeResult
from textual.widgets import Input, Button, Label, Rule, ListView, ListItem, Select, TextArea
from textual.containers import Vertical, Horizontal, Container
from panels.base_screen import BaseScreen
from panels.popup import PopupScreen, PopupType, NoteEntryPopup
from core.manager import SearchType

class NotesEntryScreen(BaseScreen):
    BINDINGS = [("escape", "app.pop_screen", "Close screen")]
    CSS_PATH = "../style/notesentry.tcss"

    def compose(self) -> ComposeResult:
        yield from super().compose()
        with Vertical(id="notes-entry-container"):
            yield Label("Notes Entry")
            yield Rule(line_style="heavy")
            # Search section
            with Horizontal(id="search-section"):
                yield Select(
                    [("Ticket Number", "ticket_number"), 
                    ("Customer Name", "name"), 
                    ("Customer Code", "code"), 
                    ("Phone", "phone")],
                    id="search-type",
                    prompt="Search Type"
                )
                yield Input(placeholder="Search...", id="search-input")
                yield Button("Search", id="search-btn", variant="primary")
        
            # Results section
            with Vertical(id="results-section"):
                yield Label("Search Results")
                yield ListView(id="search-results")

            with Container(id="ticket-fields-section"):
                with Horizontal(classes="four-column"): 
                    with Vertical(classes="col-25"):  
                        yield Label("Ticket Number")
                        with Horizontal():
                            yield Input(id="ticket-number", disabled=True)
                    with Vertical(classes="col-25"):  
                        yield Label("Customer Code")
                        with Horizontal():
                            yield Input(placeholder="Customer Code", id="code-input")
                    with Vertical(classes="col-25"):  
                        yield Label("Priority")
                        yield Select(
                            [("1 - High", "1"),
                            ("2", "2"),
                            ("3", "3"),
                            ("4", "4"),
                            ("5 - Low", "5")],
                            id="priority-select",
                            prompt="Priority"
                        )
                    with Vertical(classes="col-25"): 
                        yield Label("Ticket Type")
                        yield Select(
                            [("Inhouse", "inhouse"),
                            ("Onsite", "onsite"),
                            ("Remote", "remote")],
                            id="ticket-type-select",
                            prompt="Ticket Type"
                        )
                with Horizontal(classes="two-column"):
                    with Vertical():
                        yield Label("Contact Name")
                        yield Input(placeholder="Contact Name", id="name-input")
                    with Vertical():
                        yield Label("Phone Number")
                        yield Input(placeholder="Phone Number", id="phone-input")
                yield Label("Problem Description")
                yield TextArea(placeholder="Problem Description...", id="problem-input")
                yield Label("Equipment")
                yield ListView(id="equipment-container")
            yield Button("Enter Notes", id="enter", variant="primary")
            yield Button("Cancel", id="cancel", variant="error")
    
    def on_mount(self) -> None:
        self.current_ticket_id = ""
        self.query_one("#ticket-fields-section", Container).disabled = True
    
    def search_tickets(self) -> None:
        """Search for customers that match query and load matches in to list"""
        results_list = self.query_one("#search-results", ListView)
        results_list.clear()
        query = self.query_one("#search-input", Input).value
        search_type = self.query_one("#search-type", Select).value

        if str(search_type) == "Select.BLANK":
            self.app.push_screen(PopupScreen(f"Error: Must select a search type.", PopupType.ERROR))
            return 
        tickets = self.app.manager.tickets.search_tickets(query, SearchType(search_type))

        for ticket in tickets:
            customer_code = self.app.manager.customers.get_customer_code(ticket.customer_id)
            if len(ticket.description) > 80:
                item = ListItem(Label(f"{ticket.ticket_number} ({customer_code}) - {ticket.description[:80]}..."))
            else:
                item = ListItem(Label(f"{ticket.ticket_number} ({customer_code}) - {ticket.description}"))
            item.ticket_id = ticket.id # type: ignore[attr-defined]
            results_list.append(item)

    @on(Button.Pressed, "#search-btn")
    @on(Input.Submitted, "#search-input")
    def search(self):
        self.search_tickets()

    @on(ListView.Selected, "#search-results")
    def select_ticket(self, event: ListView.Selected) -> None:
        selected_item = event.item
        ticket_id = selected_item.ticket_id # type: ignore[attr-defined]

        eq_list = self.query_one("#equipment-container", ListView)
        eq_list.clear()

        ticket = self.app.manager.tickets.search_by_id(ticket_id)

        if ticket:
            self.current_ticket_id = ticket.id
            customer_code = self.app.manager.customers.get_customer_code(ticket.customer_id)
            # Update the form fields
            self.query_one("#ticket-number", Input).value = str(ticket.ticket_number)
            self.query_one("#code-input", Input).value = customer_code # type: ignore[attr-defined]
            self.query_one("#priority-select", Select).value = str(ticket.priority)
            self.query_one("#ticket-type-select", Select).value = ticket.ticket_type
            if ticket.contact_name:
                self.query_one("#name-input", Input).value = ticket.contact_name
            if ticket.contact_phone:
                self.query_one("#phone-input", Input).value = ticket.contact_phone
            self.query_one("#problem-input ", TextArea).text = ticket.description
            
            for equipment in ticket.equipment_list:
                list_item = ListItem(Label(f"{equipment.eq_type} ({equipment.model} - {equipment.serial_number})"))
                list_item.equipment_object = equipment # type: ignore[attr-defined]
                eq_list.append(list_item)
    
    def clear_equipment_fields(self) -> None:
        self.query_one("#eq-type", Select).clear()
        self.query_one("#eq-model", Input).clear()
        self.query_one("#eq-serial", Input).clear()
        self.query_one("#eq-notes", Input).clear()
    
    @on(Button.Pressed, "#enter")
    def push_note_entry_popup(self):
        self.app.push_screen(NoteEntryPopup(self.current_ticket_id))
        
    @on(Button.Pressed, "#cancel")
    def close_screen(self):
        self.app.pop_screen()