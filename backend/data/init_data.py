RECORDS = {
    # Roles
    "role_admin": {
        "model": "role",
        "values": {
            "name": "admin",
            "display_name": "Administrator",
            "description": "Full access with all permissions"
        },
        "noupdate": True
    },
    "role_fleet_manager": {
        "model": "role",
        "values": {
            "name": "fleet_manager",
            "display_name": "Fleet Manager",
            "description": "Owns vehicles, maintenance, regions, and fleet efficiency"
        },
        "noupdate": True
    },
    "role_driver": {
        "model": "role",
        "values": {
            "name": "driver",
            "display_name": "Driver",
            "description": "Creates and manages own trips"
        },
        "noupdate": True
    },
    "role_safety_officer": {
        "model": "role",
        "values": {
            "name": "safety_officer",
            "display_name": "Safety Officer",
            "description": "Owns driver compliance and safety scores"
        },
        "noupdate": True
    },
    "role_financial_analyst": {
        "model": "role",
        "values": {
            "name": "financial_analyst",
            "display_name": "Financial Analyst",
            "description": "Owns fuel logs, expenses, and cost reports"
        },
        "noupdate": True
    },
    # Regions
    "region_north": {
        "model": "region",
        "values": {"name": "North Zone", "code": "NZ", "active": True},
        "noupdate": True
    },
    "region_south": {
        "model": "region",
        "values": {"name": "South Zone", "code": "SZ", "active": True},
        "noupdate": True
    },
    "region_east": {
        "model": "region",
        "values": {"name": "East Zone", "code": "EZ", "active": True},
        "noupdate": True
    },
    "region_west": {
        "model": "region",
        "values": {"name": "West Zone", "code": "WZ", "active": True},
        "noupdate": True
    },
    "region_central": {
        "model": "region",
        "values": {"name": "Central Zone", "code": "CZ", "active": True},
        "noupdate": True
    },
    # Admin User
    "user_admin": {
        "model": "user",
        "values": {
            "email": "admin@example.com",
            "full_name": "Administrator",
            "hashed_password": "$P$admin123", # Hashed automatically by loader
            "role_id": "@role_admin",        # Symbolic reference
            "timezone_id": "@tz_utc",        # Default to UTC timezone
            "is_active": True
        },
        "noupdate": True
    },
}
