from enum import Enum

class RoleName(str, Enum):
    ADMIN = "admin"
    FLEET_MANAGER = "fleet_manager"
    DRIVER = "driver"
    SAFETY_OFFICER = "safety_officer"
    FINANCIAL_ANALYST = "financial_analyst"

class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    CREATE = "create"
    DELETE = "delete"

# Note: DEFAULT_POLICIES and DEFAULT_DOMAIN_RULES have been moved to individual models
# under the _role_permissions attribute for better modularity and easier access.
