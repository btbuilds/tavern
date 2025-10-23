from textual import on
from textual.app import ComposeResult
from textual.widgets import Input, Button, Label, Rule, ListView, ListItem, Checkbox, Select, TextArea
from textual.containers import Vertical, Horizontal, Container
from panels.base_screen import BaseScreen
from panels.popup import PopupScreen, PopupType, CustomerLookupScreen
from core.models import Equipment
from core.manager import SearchType

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
        self.app.push_screen(EditTicketScreen())

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
            if customer_code:
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

class EditTicketScreen(BaseScreen):
    BINDINGS = [("escape", "app.pop_screen", "Close screen")]
    CSS_PATH = "../style/editticket.tcss"

    def compose(self) -> ComposeResult:
        yield from super().compose()
        with Vertical(id="edit-ticket-container"):
            yield Label("Edit Ticket")
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
                yield Button("Save", id="save", variant="primary", disabled=True)
                yield Button("Cancel", id="cancel", variant="error")
    
    def on_mount(self) -> None:
        not_focusable = ["#search-btn", "#add-equipment", "#remove-equipment"]
        for button in not_focusable:
            self.query_one(button, Button).can_focus = False
        self.query_one("#ticket-fields-section", Container).disabled = True
        self.current_ticket_id = ""
    
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
        self.query_one("#ticket-fields-section", Container).disabled = False
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
            self.query_one("#save", Button).disabled = False
        else:
            self.query_one("#save", Button).disabled = True
    
    @on(Button.Pressed, "#save")
    def save_ticket(self):
        is_valid = self.validate_ticket_form()
        if not is_valid:
            self.app.push_screen(PopupScreen("Please fill out the entire form.", PopupType.ERROR))
            return
        
        data = self.gather_form_data()
        if data:
            try:
                self.app.manager.tickets.update_ticket(**data)
                self.app.push_screen(PopupScreen(f"Ticket updated!", PopupType.SUCCESS))
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
        description = self.query_one("#problem-input", TextArea).text
        equipment_list_objects = [] # List of Equipment objects
        eq_list = self.query_one("#equipment-container", ListView) # ListView of Equipment
        for item in eq_list.children:
            equipment_list_objects.append(item.equipment_object) # type: ignore[attr-defined]
        data = {"id":self.current_ticket_id,
                "customer_id":customer_id,
                "ticket_type":ticket_type,
                "priority":priority,
                "description":description,
                "equipment_list":equipment_list_objects,
                "contact_name":name,
                "contact_phone":phone}
        return data
        

    @on(Button.Pressed, "#cancel")
    def close_screen(self):
        self.app.pop_screen()