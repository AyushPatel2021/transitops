from enum import Enum

class RoleName(str, Enum):
    ADMIN = "admin"
    USER = "user"

class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    CREATE = "create"
    DELETE = "delete"

# Note: DEFAULT_POLICIES and DEFAULT_DOMAIN_RULES have been moved to individual models
# under the _role_permissions attribute for better modularity and easier access.
