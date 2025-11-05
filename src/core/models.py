from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid

class TicketState(Enum):
    OPEN = "open"
    IN_PROGRESS = "in progress"
    WAITING_FOR_PARTS = "waiting for parts"
    WAITING_FOR_CUSTOMER = "waiting for customer"
    CLOSED = "closed"

@dataclass
class Customer:
    # Internal ID (UUID, never shown to humans)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Human-friendly 6-char code, must be unique
    code: str = ""

    name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""

    # True if business, False if individual
    is_business: bool = False

@dataclass
class Equipment:
    eq_type: str = ""
    model: str = ""
    serial_number: str = ""
    notes: str = ""

@dataclass
class TicketNote:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    technician: str = ""
    date_created: datetime = field(default_factory=datetime.now)
    notes: str = ""
    ticket_time: float = 0 # amount of time spent on work
    mileage: int = 0 # for onsite mileage reimbursement

@dataclass
class Ticket:
    # Internal ID (UUID)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Human-friendly incrementing number
    ticket_number: int = 0

    date_created: datetime = field(default_factory=datetime.now)
    created_by: str = "" # username or tech name

    ticket_state: TicketState = TicketState.OPEN

    date_started: Optional[datetime] = None # When work began
    date_completed: Optional[datetime] = None # When ticket was finished

    ticket_type: str = "" # inhouse, onsite, remote

    customer_id: str = "" # points back to Customer.id

    contact_name: Optional[str] = None # in case the contact is different from the customer
    contact_phone: Optional[str] = None

    priority: int = 0 # Priority level 1-5

    description: str = "" 
    equipment_list: List[Equipment] = field(default_factory=list)
    notes_list: List[TicketNote] = field(default_factory=list)

@dataclass
class Technician:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    name: str = ""
    username: str = ""  # login name
    email: str = ""

    is_active: bool = True
