# Tavern - Tech Support Ticket Management System

A terminal-based ticket management system built with Python and Textual. Tavern provides a modern, interactive interface for managing tech support tickets, customers, and technician workflows.

## Features

- **Ticket Management**: Create, edit, and search tickets with comprehensive tracking
- **Customer Database**: Store and manage customer information with quick lookup capabilities
- **Time Tracking**: Log work hours and notes against tickets
- **Equipment Tracking**: Associate multiple pieces of equipment with each ticket
- **Technician Management**: User authentication and activity tracking
- **Advanced Search**: Find tickets by number, customer code, name, or phone number
- **Modern TUI**: Clean, intuitive interface built with Textual

## Requirements

- Python 3.10 or higher
- uv (Python package manager)

## Installation & Setup

1. **Clone the repository**
```bash
   git clone https://github.com/btbuilds/tavern.git
   cd tavern
```

2. **Install dependencies**
```bash
   uv sync
```

3. **Run the application**
```bash
   uv run ./src/main.py
```
   
   Or use the provided shell script:
```bash
   ./main.sh
```

## Usage

### First Time Setup
1. Launch the application
2. Create a technician account via the Technicians screen from the sidebar (press `s` to toggle)
3. Log in with your technician username via the Account screen

### Managing Customers
- **New Customer**: Create customer records with code, contact info, and business details
- **Edit Customer**: Search and update existing customer information

### Creating Tickets
1. Navigate to "New Ticket" from the sidebar (press `s` to toggle)
2. Enter customer code (or use Lookup to search)
3. Fill in ticket details, priority, and problem description
4. Add equipment as needed
5. Click Create to save the ticket

### Adding Notes
1. Open "Notes Entry" from the Ticket screen
2. Search for the ticket you want to update
3. Select the ticket from results
4. Click the ticket to open the note entry modal
5. Enter your notes, hours worked, and mileage (if applicable)

### Keyboard Shortcuts
- `s` - Toggle sidebar
- `Escape` - Close current screen/modal
- `Tab` - Navigate between form fields

## Data Storage

Tavern uses JSON files for data persistence, stored in `src/data/`:
- `customers.json` - Customer records
- `tickets.json` - Ticket information and notes
- `technicians.json` - Technician accounts
- `maxticket.txt` - Ticket number counter

## Development

This project was created as a learning exercise for Boot.dev's curriculum, focusing on:
- Python application architecture
- Terminal UI development with Textual
- Data modeling and persistence
- Form validation and user input handling

## License

Personal learning project - use as you wish!