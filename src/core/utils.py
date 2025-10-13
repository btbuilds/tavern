from core.models import Ticket, Equipment, TicketNote

def hydrate_ticket(ticket_dict: dict) -> Ticket:
    """Convert a raw ticket dictionary (from JSON) into a proper Ticket object."""
    equipment_list = [Equipment(**eq) for eq in ticket_dict.get("equipment_list", [])]
    notes_list = [TicketNote(**note) for note in ticket_dict.get("notes_list", [])]

    # Rebuild the ticket with nested objects
    return Ticket(
        **{
            **ticket_dict,
            "equipment_list": equipment_list,
            "notes_list": notes_list,
        }
    )
