from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class MenuItem:
    def __init__(
        self, 
        name: str, 
        label: str, 
        path: Optional[str] = None, 
        icon: Optional[str] = None, 
        children: Optional[List['MenuItem']] = None,
        groups: Optional[List[str]] = None,
        sequence: int = 10
    ):
        self.name = name
        self.label = label
        self.path = path
        self.icon = icon
        self.children = children or []
        self.groups = groups or []  # Roles that can access this item
        self.sequence = sequence

    def to_dict(self, user_role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        # Filter by role
        if self.groups and user_role not in self.groups:
            return None
            
        res = {
            "name": self.name,
            "label": self.label,
            "path": self.path,
            "icon": self.icon,
            "sequence": self.sequence
        }
        
        if self.children:
            filtered_children = []
            for child in self.children:
                child_dict = child.to_dict(user_role)
                if child_dict:
                    filtered_children.append(child_dict)
            
            # If all children are filtered out but we had children, maybe hide parent?
            # Actually, standard Znova behavior usually hides parent if empty children.
            if not filtered_children:
                return None
            res["children"] = filtered_children
            
        return res

class MenuManager:
    def __init__(self):
        self._groups = {} # group_title -> [MenuItem]

    def add_item(self, group_title: str, item: MenuItem):
        if group_title not in self._groups:
            self._groups[group_title] = []
        self._groups[group_title].append(item)
        # Sort by sequence
        self._groups[group_title].sort(key=lambda x: x.sequence)

    def get_menu(self, user_role: Optional[str] = None) -> List[Dict[str, Any]]:
        res = []
        for title, items in self._groups.items():
            filtered_items = []
            for item in items:
                item_dict = item.to_dict(user_role)
                if item_dict:
                    filtered_items.append(item_dict)
            
            if filtered_items:
                res.append({
                    "title": title,
                    "items": filtered_items
                })
        return res

menu_manager = MenuManager()

# Initialize menus from data folder
try:
    from backend.data.menus import initialize_menus
    initialize_menus(menu_manager)
except ImportError:
    logger.warning("Could not import menu definitions from backend.data.menus")
