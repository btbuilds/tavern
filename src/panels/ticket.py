from textual import on
from textual.app import ComposeResult
from textual.widgets import Input, Button, Label, Rule, ListView, ListItem, Checkbox, Select, TextArea
from textual.containers import Vertical, Horizontal
from panels.base_screen import BaseScreen
from panels.popup import PopupScreen, PopupType, CustomerLookupScreen
from core.models import Equipment

class TicketScreen(BaseScreen):
    BINDINGS = [("escape", "app.pop_screen", "Close screen")]
    CSS_PATH = "../style/tickets.tcss"

    def compose(self) -> ComposeResult:
        yield from super().compose() # This gets header/sidebar/footer
        with Vertical(id="form-content"):
            yield Label("Tickets")
            yield Button("New Ticket", id="new", variant="primary")
            yield Button("Edit Ticket", id="edit", variant="primary")
            yield Button("Search Tickets", id="search", variant="primary")
    
    @on(Button.Pressed, "#new")
    def new_ticket(self):
        self.app.pop_screen()
        self.app.push_screen(NewTicketScreen())

    @on(Button.Pressed, "#edit")
    def edit_ticket(self):
        self.app.pop_screen()
        # self.app.push_screen(EditTicketScreen())

    @on(Button.Pressed, "#search")
    def search_tickets(self):
        self.app.pop_screen()
        # self.app.push_screen(SearchTicketScreen())

class NewTicketScreen(BaseScreen):
    BINDINGS = [("escape", "app.pop_screen", "Close screen")]
    CSS_PATH = "../style/newticket.tcss"

    def compose(self) -> ComposeResult:
        yield from super().compose()
        with Vertical(id="new-ticket-content"):
            yield Label("New Ticket")
            yield Rule(line_style="heavy")
            with Horizontal(classes="three-column"): 
                with Vertical(classes="col-50"):  # 50% width
                    yield Label("Customer Code")
                    with Horizontal():
                        yield Input(placeholder="Customer Code", id="code-input")
                        yield Button("Lookup", id="lookup", variant="primary")
                with Vertical(classes="col-25"):  # 25% width
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
                with Vertical(classes="col-25"):  # 25% width
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
                    yield Label("Contact Name") # Maybe automatically populate this when a valid customer code is put in
                    yield Input(placeholder="Contact Name", id="name-input")
                with Vertical():
                    yield Label("Phone Number")
                    yield Input(placeholder="Phone Number", id="phone-input")
            yield Label("Problem Description")
            yield TextArea(placeholder="Problem Description...", id="problem-input")
            yield Label("Equipment")
            with Horizontal(id="equipment-row"):
                yield Select(
                    [("Desktop", "desktop"),
                    ("Laptop", "laptop"),
                    ("Printer", "printer"),
                    ("Other", "other")],
                    id="eq-type",
                    prompt="Type"
                )
                yield Input(placeholder="Model", id="eq-model")
                yield Input(placeholder="Serial", id="eq-serial")
                yield Input(placeholder="Notes", id="eq-notes")
            with Horizontal(id="equipment-btns"):
                yield Button("+ Add Equipment", id="add-equipment", classes="equipment-btn", variant="success")
                yield Button("- Remove Equipment", id="remove-equipment", classes="equipment-btn", variant="error", disabled=True)
            yield Label("Equipment List")
            yield ListView(id="equipment-container")
            yield Button("Create", id="create", variant="primary", disabled=True)
            yield Button("Cancel", id="cancel", variant="error")
    
    def on_mount(self) -> None:
        not_focusable = ["#lookup", "#add-equipment", "#remove-equipment"]
        for button in not_focusable:
            self.query_one(button, Button).can_focus = False
    
    @on(Button.Pressed, "#lookup")
    def push_lookup_customer(self) -> None:
        def set_code(customer_code):
            self.query_one("#code-input", Input).value = customer_code
        self.app.push_screen(CustomerLookupScreen(), set_code)

    @on(Button.Pressed, "#add-equipment")
    def handle_add_equipment(self) -> None:
        eq_type = str(self.query_one("#eq-type", Select).value) # Cast to string just to make pylance happy
        eq_model = self.query_one("#eq-model", Input).value 
        eq_serial = self.query_one("#eq-serial", Input).value
        eq_notes = self.query_one("#eq-notes", Input).value
        if eq_type == "Select.BLANK" or not eq_model or not eq_serial:
            self.app.push_screen(PopupScreen(f"Error: Equipment Type, Model, and Serial are required.", PopupType.ERROR))
            return        
        equipment = Equipment(eq_type, eq_model, eq_serial, eq_notes)
        eq_list = self.query_one("#equipment-container", ListView)
        item = ListItem(Label(f"{eq_type} ({eq_model} - {eq_serial})"))
        item.equipment_object = equipment # type: ignore[attr-defined]
        eq_list.append(item)
        self.clear_equipment_fields()
    
    @on(Button.Pressed, "#remove-equipment")
    def handle_remove_equipment(self) -> None:
        eq_list = self.query_one("#equipment-container", ListView)
        if eq_list.highlighted_child:
            eq_list.highlighted_child.remove()
            self.query_one("#remove-equipment", Button).disabled = True
    
    @on(ListView.Highlighted, "#equipment-container")
    def enable_remove_equipment(self) -> None:
        self.query_one("#remove-equipment", Button).disabled = False
    
    def clear_equipment_fields(self) -> None:
        self.query_one("#eq-type", Select).clear()
        self.query_one("#eq-model", Input).clear()
        self.query_one("#eq-serial", Input).clear()
        self.query_one("#eq-notes", Input).clear()
    
    @on(Input.Changed)
    @on(TextArea.Changed)
    def check_valid(self) -> None:
        if self.validate_ticket_form():
            self.query_one("#create", Button).disabled = False
        else:
            self.query_one("#create", Button).disabled = True
    
    @on(Button.Pressed, "#create")
    def create_ticket(self):
        is_valid = self.validate_ticket_form()
        if not is_valid:
            self.app.push_screen(PopupScreen("Please fill out the entire form.", PopupType.ERROR))
            return
        
        data = self.gather_form_data()
        if data:
            try:
                ticket = self.app.manager.tickets.create_ticket(**data)
                self.app.push_screen(PopupScreen(f"Ticket {ticket} created!", PopupType.SUCCESS))
            except Exception as e:
                self.app.push_screen(PopupScreen(f"Error: {e}", PopupType.ERROR))

    def validate_ticket_form(self) -> bool:
        """
        Validate form data.
        """
        priority_valid = self.query_one("#priority-select", Select).value != "Select.BLANK"
        ticket_type_valid = self.query_one("#ticket-type-select", Select).value != "Select.BLANK"
        if (self.query_one("#code-input", Input).value and 
            self.query_one("#name-input", Input).value and 
            self.query_one("#phone-input", Input).value and
            self.query_one("#problem-input", TextArea).text and
            priority_valid and
            ticket_type_valid):
            return True
        else:
            return False
    
    def gather_form_data(self) -> dict:
        """Extract all form data into a dict"""
        code = self.query_one("#code-input", Input).value
        customer_id = self.app.manager.customers.get_customer_id(code)
        if not customer_id:
            self.app.push_screen(PopupScreen(f"Error: Customer not found.", PopupType.ERROR))
            return {}
        priority = self.query_one("#priority-select", Select).value
        ticket_type = self.query_one("#ticket-type-select", Select).value
        name = self.query_one("#name-input", Input).value
        phone = self.query_one("#phone-input", Input).value
        current_tech = self.app.current_technician.username # type: ignore[attr-defined]
        description = self.query_one("#problem-input", TextArea).text
        equipment_list_objects = [] # List of Equipment objects
        eq_list = self.query_one("#equipment-container", ListView) # ListView of Equipment
        for item in eq_list.children:
            equipment_list_objects.append(item.equipment_object) # type: ignore[attr-defined]
        data = {"customer_id":customer_id,
                "ticket_type":ticket_type,
                "priority":priority,
                "description":description,
                "equipment_list":equipment_list_objects,
                "created_by":current_tech,
                "contact_name":name,
                "contact_phone":phone}
        return data
        

    @on(Button.Pressed, "#cancel")
    def close_screen(self):
        self.app.pop_screen()