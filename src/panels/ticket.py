from textual import on
from textual.app import ComposeResult
from textual.widgets import Button, Label
from textual.containers import Vertical
from panels.base_screen import BaseScreen
from panels.newticket import NewTicketScreen
from panels.editticket import EditTicketScreen
from panels.notesentry import NotesEntryScreen

class TicketScreen(BaseScreen):
    BINDINGS = [("escape", "app.pop_screen", "Close screen")]
    CSS_PATH = "../style/tickets.tcss"

    def compose(self) -> ComposeResult:
        yield from super().compose() # This gets header/sidebar/footer
        with Vertical(id="form-content"):
            yield Label("Tickets")
            yield Button("New Ticket", id="new", variant="primary")
            yield Button("Edit/Search Tickets", id="edit", variant="primary")
            yield Button("Notes Entry", id="notes", variant="primary")
    
    @on(Button.Pressed, "#new")
    def new_ticket(self):
        self.app.pop_screen()
        self.app.push_screen(NewTicketScreen())

    @on(Button.Pressed, "#edit")
    def edit_ticket(self):
        self.app.pop_screen()
        self.app.push_screen(EditTicketScreen())

    @on(Button.Pressed, "#notes")
    def search_tickets(self):
        self.app.pop_screen()
        self.app.push_screen(NotesEntryScreen())