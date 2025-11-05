from textual.app import App
from textual.reactive import reactive
from panels.home import HomeScreen
from core.manager import TicketSystemManager

class TicketRPGApp(App):
    CSS_PATH = "style/style.tcss"
    current_technician = reactive(None)
    manager = TicketSystemManager()
   
    def on_mount(self) -> None:
        self.title = "Tavern"
        self.sub_title = "A simple ticket management system"
        self.theme = "monokai"
        self.push_screen(HomeScreen())
    
    def login_user(self, technician):
        self.current_technician = technician
        self.sub_title = f"A simple ticket management system -- Current User: {technician.username}"
    
    def logout_user(self):
        self.current_technician = None
        self.sub_title = "A simple ticket management system"

if __name__ == "__main__":
    app = TicketRPGApp()
    app.run()