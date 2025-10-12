from core.models import Ticket, Customer, TicketNote, Technician
from typing import Optional
from dataclasses import asdict
from core.storage import load_data, save_data
from core.constants import COUNTER_FILE
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
                if field_value == cleaned_query:
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
    
    def get_customer_tickets(self, customer_id: str):
        ticket_dicts = load_data("tickets")
        customer_tickets = []

        for ticket_dict in ticket_dicts:
            if ticket_dict["customer_id"] == customer_id:
                customer_tickets.append(Ticket(**ticket_dict))

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
    
    def add_time_entry(self, 
                       ticket_id: str, 
                       ticket_number: int, 
                       technician: str, 
                       notes: str, 
                       hours: float, 
                       mileage: int):
        ticket_dicts = load_data("tickets")

        ticket_note = TicketNote(ticket_id=ticket_id,
                                 ticket_number=ticket_number,
                                 technician=technician,
                                 notes=notes,
                                 ticket_time=hours,
                                 mileage=mileage)
        
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
    
    def award_xp(self, tech_id, xp_amount):
        # TODO: Update XP and handle leveling up
        pass