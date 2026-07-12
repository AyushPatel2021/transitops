from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.core.menu_manager import MenuManager, MenuItem

def initialize_menus(menu_manager: 'MenuManager'):
    from backend.core.menu_manager import MenuItem

    # --- Main Group ---
    menu_manager.add_item("Main", MenuItem(
        "dashboard", "Dashboard", "/dashboard", "LayoutDashboard", sequence=10
    ))

    # --- Settings Group ---
    settings_group = "Settings"
    menu_manager.add_item(settings_group, MenuItem(
        "users", "Users", "/models/user", "Users", sequence=10, groups=['admin', 'user']
    ))
    menu_manager.add_item(settings_group, MenuItem(
        "sequences", "Sequences", "/models/sequence", "LayoutGrid", sequence=30, groups=['admin']
    ))
    menu_manager.add_item(settings_group, MenuItem(
        "crons", "Cron Jobs", "/models/cron", "Clock", sequence=40, groups=['admin']
    ))
