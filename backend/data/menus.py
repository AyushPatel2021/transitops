from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.core.menu_manager import MenuManager, MenuItem

def initialize_menus(menu_manager: 'MenuManager'):
    from backend.core.menu_manager import MenuItem

    all_roles = ["admin", "fleet_manager", "driver", "safety_officer", "financial_analyst"]
    admin_fleet = ["admin", "fleet_manager"]
    finance_roles = ["admin", "fleet_manager", "financial_analyst"]
    reports_roles = ["admin", "fleet_manager", "financial_analyst"]

    menu_manager.add_item("Main", MenuItem(
        "dashboard", "Dashboard", "/dashboard", "LayoutDashboard", sequence=10, groups=all_roles
    ))

    menu_manager.add_item("Fleet", MenuItem(
        "vehicles", "Vehicles", "/models/vehicle", "BusFront", sequence=10, groups=all_roles
    ))
    menu_manager.add_item("Fleet", MenuItem(
        "regions", "Regions", "/models/region", "MapPinned", sequence=20, groups=admin_fleet
    ))

    menu_manager.add_item("Drivers", MenuItem(
        "driver_directory", "Driver Directory", "/models/driver", "UserRoundCheck", sequence=10,
        groups=["admin", "fleet_manager", "safety_officer"]
    ))

    menu_manager.add_item("Trips", MenuItem(
        "trip_board", "Trip Board", "/models/trip", "Route", sequence=10, groups=["admin", "fleet_manager"]
    ))
    menu_manager.add_item("Trips", MenuItem(
        "my_trips", "My Trips", "/models/trip", "Navigation", sequence=20, groups=["driver"]
    ))

    menu_manager.add_item("Maintenance", MenuItem(
        "maintenance_log", "Maintenance Log", "/models/maintenance.log", "Wrench", sequence=10, groups=admin_fleet
    ))

    menu_manager.add_item("Finance", MenuItem(
        "fuel_logs", "Fuel Logs", "/models/fuel.log", "Fuel", sequence=10, groups=finance_roles
    ))
    menu_manager.add_item("Finance", MenuItem(
        "expenses", "Expenses", "/models/expense", "ReceiptText", sequence=20, groups=finance_roles
    ))

    menu_manager.add_item("Reports", MenuItem(
        "fuel_efficiency_report", "Fuel Efficiency", "/models/fuel.log?report=fuel_efficiency", "Gauge", sequence=10, groups=reports_roles
    ))
    menu_manager.add_item("Reports", MenuItem(
        "fleet_utilization_report", "Fleet Utilization", "/models/vehicle?report=fleet_utilization", "Activity", sequence=20, groups=reports_roles
    ))
    menu_manager.add_item("Reports", MenuItem(
        "operational_cost_report", "Operational Cost", "/models/expense?report=operational_cost", "TrendingUp", sequence=30, groups=reports_roles
    ))
    menu_manager.add_item("Reports", MenuItem(
        "roi_report", "ROI", "/models/vehicle?report=roi", "BadgeDollarSign", sequence=40, groups=reports_roles
    ))

    menu_manager.add_item("Settings", MenuItem(
        "users", "Users", "/models/user", "UserCog", sequence=10, groups=["admin"]
    ))
