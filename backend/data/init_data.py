RECORDS = {
    # Roles
    "role_admin": {
        "model": "role",
        "values": {
            "name": "admin",
            "description": "Full access with all permissions"
        },
        "noupdate": True
    },
    "role_user": {
        "model": "role",
        "values": {
            "name": "user",
            "description": "Standard user access"
        },
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
