from core.models import Ticket, Customer, TicketNote, Technician, Equipment
from typing import Optional
from dataclasses import asdict
from core.storage import load_data, save_data
from core.constants import COUNTER_FILE
from core.utils import hydrate_ticket
from enum import Enum
import re

class TicketSystemManager:
    def __init__(self):        
        # Create individual managers
        self.customers = CustomerManager()
        self.tickets = TicketManager()
        self.technicians = TechnicianManager()

class SearchType(Enum):
    CODE = "code"
    NAME = "name"
    PHONE = "phone"
    EMAIL = "email"
    TICKET_NUMBER = "ticket_number"

class CustomerManager:    
    def create_customer(self, 
                        code: str, 
                        name: str, 
                        phone: str, 
                        email: str, 
                        address: str, 
                        is_business: bool):
        customer_dicts = load_data("customers")

        self.check_unique_code(code)
            
        cleaned_phone = re.sub(r'\D', '', phone) # Strips everything but digits

        customer = Customer(code=code,
                            name=name,
                            phone=cleaned_phone,
                            email=email,
                            address=address,
                            is_business=is_business)
        
        customer_dicts.append(asdict(customer))

        save_data("customers", customer_dicts)
    
    def update_customer(self,
                        id: str, 
                        code: str, 
                        name: str, 
                        phone: str, 
                        email: str, 
                        address: str, 
                        is_business: bool):
        customer_dicts = load_data("customers")

        if not code or not name or not phone:
            raise ValueError("Customer Code, Name, and Phone are required.")

        for customer_dict in customer_dicts:
            if customer_dict["id"] == id:
                self.check_unique_code(code, id)
                cleaned_phone = re.sub(r'\D', '', phone) # Strips everything but digits
                customer_dict["code"] = code
                customer_dict["name"] = name
                customer_dict["phone"] = cleaned_phone
                customer_dict["email"] = email
                customer_dict["address"] = address
                customer_dict["is_business"] = is_business
                save_data("customers", customer_dicts)
                return  # Exit early after successful update
    
        # If we get here, the ID wasn't found
        # Should not be possible with proper UI, just here in case
        raise ValueError(f"Customer with ID {id} not found")
    
    def check_unique_code(self, code, id: Optional[str] = ""):
        customer_dicts = load_data("customers")

        for customer_dict in customer_dicts:
            if customer_dict["code"] == code and customer_dict["id"] != id:
                raise ValueError(f"Customer code {code} already exists.")
    
    def search_customers(self, query_data, search_type: SearchType):
        customer_dicts = load_data("customers")
        results = []
        field_name = search_type.value

        for customer_dict in customer_dicts:
            field_value = customer_dict[field_name]

            if search_type == SearchType.PHONE:
                cleaned_query = re.sub(r'\D', '', query_data) # Strips everything but digits
                cleaned_field = re.sub(r'\D', '', field_value) # Just in case it managed to get saved with symbols or something
                if cleaned_field == cleaned_query:
                    results.append(Customer(**customer_dict))
            else:
                if query_data.lower() in field_value.lower():
                    results.append(Customer(**customer_dict))
        
        return results
    
    def find_by_id(self, id: str):
        customer_dicts = load_data("customers")
        for customer_dict in customer_dicts:
            if customer_dict["id"] == id:
                return Customer(**customer_dict)
    
    def get_customer_id(self, code: str):
        customer_dicts = load_data("customers")
        for customer_dict in customer_dicts:
            if customer_dict["code"] == code:
                return customer_dict["id"]
    
    def get_customer_code(self, id: str):
        customer_dicts = load_data("customers")
        for customer_dict in customer_dicts:
            if customer_dict["id"] == id:
                return customer_dict["code"]

    
    def get_customer_tickets(self, customer_id: str):
        ticket_dicts = load_data("tickets")
        customer_tickets = []

        for ticket_dict in ticket_dicts:
            if ticket_dict["customer_id"] == customer_id:
                customer_tickets.append(hydrate_ticket(ticket_dict))

        return customer_tickets

class TicketManager:        
    def create_ticket(self, 
                      customer_id: str, 
                      ticket_type: str,
                      priority: str, 
                      description: str, 
                      equipment_list: list, 
                      created_by: str, 
                      contact_name: Optional[str] = "", 
                      contact_phone: Optional[str] = ""):
        customer_dicts = load_data("customers")
        valid_id = False
        for customer_dict in customer_dicts:
            if customer_dict["id"] == customer_id:
                valid_id = True
                break
        if not valid_id:
            raise ValueError("Customer ID not found.")
        ticket_dicts = load_data("tickets")
        ticket_number = self.get_next_ticket_number()
        prio_int = int(priority)
        cleaned_phone = ""
        if contact_phone:
            cleaned_phone = re.sub(r'\D', '', contact_phone) # Strips everything but digits

        ticket = Ticket(ticket_number=ticket_number, 
                        created_by=created_by, 
                        ticket_type=ticket_type,
                        priority=prio_int,
                        customer_id=customer_id,
                        description=description,
                        equipment_list=equipment_list,
                        contact_name=contact_name,
                        contact_phone=cleaned_phone)
        
        ticket_dicts.append(asdict(ticket))

        save_data("tickets", ticket_dicts)
        return ticket_number
    
    def update_ticket(self,
                      id: str,
                      customer_id: str,
                      ticket_type: str,
                      priority: str, 
                      description: str, 
                      equipment_list: list,
                      contact_name: Optional[str] = "", 
                      contact_phone: Optional[str] = ""):
        ticket_dicts = load_data("tickets")
        prio_int = int(priority)
        cleaned_phone = ""
        if contact_phone:
            cleaned_phone = re.sub(r'\D', '', contact_phone) # Strips everything but digits
        
        for ticket_dict in ticket_dicts:
            if ticket_dict["id"] == id:
                ticket_dict["customer_id"] = customer_id
                ticket_dict["ticket_type"] = ticket_type
                ticket_dict["priority"] = prio_int
                ticket_dict["description"] = description
                ticket_dict["equipment_list"] = equipment_list
                ticket_dict["contact_name"] = contact_name
                ticket_dict["contact_phone"] = cleaned_phone
                save_data("tickets", ticket_dicts)
                return  # Exit early after successful update
    
        # If we get here, the ID wasn't found
        # Should not be possible with proper UI, just here in case
        raise ValueError(f"Ticket with ID {id} not found")

    def search_tickets(self, query_data, search_type: SearchType):
        if not query_data:
            return []
        results = []
        if search_type == SearchType.PHONE:
            results = self.search_by_phone(query_data)
        elif search_type == SearchType.CODE:
            results = self.search_by_code(query_data)
        elif search_type == SearchType.NAME:
            results = self.search_by_name(query_data)
        elif search_type == SearchType.TICKET_NUMBER:
            results = self.search_by_ticket_number(query_data)
        return results
    
    def search_by_phone(self, phone_number):
        ticket_dicts = load_data("tickets")
        customer_dicts = load_data("customers")
        cleaned_query = re.sub(r'\D', '', phone_number) # Strips everything but digits
        results = []
        customer_ids = [] # customers that have this phone number

        for customer_dict in customer_dicts:
            field_value = customer_dict["phone"]
            cleaned_field = re.sub(r'\D', '', field_value) # Just in case it managed to get saved with symbols or something
            if cleaned_query and cleaned_field == cleaned_query: # Only match if query isn't empty
                customer_ids.append(customer_dict["id"])

        for ticket_dict in ticket_dicts:
            field_value = ticket_dict["contact_phone"]
            cleaned_field = re.sub(r'\D', '', field_value) # Just in case it managed to get saved with symbols or something
            if cleaned_field == cleaned_query or ticket_dict["customer_id"] in customer_ids:
                results.append(hydrate_ticket(ticket_dict))
        return results
    
    def search_by_code(self, customer_code):
        ticket_dicts = load_data("tickets")
        customer_dicts = load_data("customers")
        customer_id = ""
        results = []

        for customer_dict in customer_dicts:
            if customer_dict["code"] == customer_code:
                customer_id = customer_dict["id"]
                break
        else:
            return []
        for ticket_dict in ticket_dicts:
            if ticket_dict["customer_id"] == customer_id:
                results.append(hydrate_ticket(ticket_dict))
        return results
    
    def search_by_name(self, customer_name):
        ticket_dicts = load_data("tickets")
        customer_dicts = load_data("customers")
        customer_ids = []
        results = []

        for customer_dict in customer_dicts:
            if customer_dict["name"] == customer_name:
                customer_ids.append(customer_dict["id"])
        
        if not customer_ids:
            return []
        
        for ticket_dict in ticket_dicts:
            if ticket_dict["customer_id"] in customer_ids:
                results.append(hydrate_ticket(ticket_dict))
        return results
    
    def search_by_ticket_number(self, ticket_number):
        ticket_dicts = load_data("tickets")

        # Convert to int if it's a string
        try:
            ticket_num = int(ticket_number)
        except (ValueError, TypeError):
            return []
        
        for ticket_dict in ticket_dicts:
            if ticket_dict["ticket_number"] == ticket_num:
                return [hydrate_ticket(ticket_dict)]
        else:
            return []
    
    def search_by_id(self, id):
        ticket_dicts = load_data("tickets")

        for ticket_dict in ticket_dicts:
            if ticket_dict["id"] == id:
                return hydrate_ticket(ticket_dict)


    
    def add_time_entry(self, 
                       ticket_id: str, 
                       technician: str, 
                       notes: str, 
                       ticket_time: str, 
                       mileage: str):
        ticket_dicts = load_data("tickets")
        try:
            hours = float(ticket_time)
            miles = int(mileage)
        except Exception as e:
            raise ValueError(f"Invalid entry in hours or mileage. {e}")

        ticket_note = TicketNote(technician=technician,
                                 notes=notes,
                                 ticket_time=hours,
                                 mileage=miles)
        
        ticket = {}

        for ticket_dict in ticket_dicts:
            if ticket_dict["id"] == ticket_id:
                ticket = ticket_dict
                break

        if not ticket:
            raise ValueError(f"Ticket with ID {ticket_id} not found")
        
        ticket["notes_list"].append(asdict(ticket_note))

        save_data("tickets", ticket_dicts)
    
    def calculate_xp_for_completion(self, ticket):
        # RPG XP logic
        pass

    def get_next_ticket_number(self):
        try:
            with open(COUNTER_FILE, 'r') as f:
                current_max = int(f.read().strip())
        except (FileNotFoundError, ValueError):
            # Fallback or initialize to 0
            current_max = 0
        
        next_number = current_max + 1
        
        with open(COUNTER_FILE, 'w') as f:
            f.write(str(next_number))
        
        return next_number
    
    def get_ticket_notes(self, id):
        ticket_dicts = load_data("tickets")

        for ticket_dict in ticket_dicts:
            if ticket_dict["id"] == id:
                return ticket_dict["notes_list"]

class TechnicianManager:
    def create_technician(self, 
                          name: str, 
                          username: str, 
                          email: str):
        tech_dicts = load_data("technicians")
        
        for tech_dict in tech_dicts:
            if tech_dict["username"] == username: # Match username
                if tech_dict["email"] == email: # Match username AND email
                    raise ValueError(f"A technician with username {username} and email {email} already exists")
                raise ValueError(f"A technician with username {username} already exists")
            
            if tech_dict["email"] == email: # Match email but not username
                raise ValueError(f"A technician with email {email} already exists")
        
        technician = Technician(name=name,
                                username=username,
                                email=email)
        
        tech_dicts.append(asdict(technician))

        save_data("technicians", tech_dicts)
    
    def update_technician(self, id: str, name: str, username: str, email: str, is_active: bool):
        tech_dicts = load_data("technicians")
        
        for tech_dict in tech_dicts:
            if tech_dict["id"] == id:
                tech_dict["name"] = name
                tech_dict["username"] = username
                tech_dict["email"] = email
                tech_dict["is_active"] = is_active
                save_data("technicians", tech_dicts)
                return  # Exit early after successful update
    
        # If we get here, the ID wasn't found
        # Should not be possible with proper UI, just here in case
        raise ValueError(f"Technician with ID {id} not found")

    def login(self, username):
        # Handle technician sessions
        tech_dicts = load_data("technicians")
        for tech_dict in tech_dicts:
            if tech_dict["username"] == username:
                return Technician(**tech_dict) # Convert the dict to a Technician object

    def list_technicians(self):
        tech_dicts = load_data("technicians")
        tech_objects = []
        for tech_dict in tech_dicts:
            tech_objects.append(Technician(**tech_dict))
        return tech_objects
    
    def find_by_id(self, id: str):
        tech_dicts = load_data("technicians")
        for tech_dict in tech_dicts:
            if tech_dict["id"] == id:
                return Technician(**tech_dict)
    
    def get_technician_id(self, username: str):
        tech_dicts = load_data("technicians")
        for tech_dict in tech_dicts:
            if tech_dict["username"] == username:
                return tech_dict["id"]
    
    def award_xp(self, tech_id, xp_amount):
        # TODO: Update XP and handle leveling up
        pass