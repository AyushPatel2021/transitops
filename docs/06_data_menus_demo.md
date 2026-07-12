# Data, Menus, And Demo Records

Module data belongs in `backend/data` and `backend/demo`.

## Init Data

`backend/data/init_data.py` uses symbolic record ids:

```python
RECORDS = {
    "role_engineering": {
        "model": "role",
        "values": {
            "name": "engineering",
            "description": "Engineering users",
        },
        "noupdate": True,
    },
    "stage_draft": {
        "model": "plm.eco.stage",
        "values": {
            "name": "Draft",
            "sequence": 10,
        },
        "noupdate": True,
    },
}
```

Reference another record with `@xml_id`:

```python
"stage_id": "@stage_draft"
```

The loader supports keeping a real `user_id` if the target model defines that field.

## Menus

Menus are initialized in `backend/data/menus.py`.

Example:

```python
def initialize_menus(menu_manager: "MenuManager"):
    from backend.core.menu_manager import MenuItem

    group = "PLM"
    menu_manager.add_item(group, MenuItem(
        "plm_eco",
        "Engineering Changes",
        "/models/plm.eco",
        "Settings",
        sequence=10,
        groups=["admin", "engineering", "approver"],
    ))
    menu_manager.add_item(group, MenuItem(
        "mrp_bom",
        "Bills of Materials",
        "/models/mrp.bom",
        "Box",
        sequence=20,
        groups=["admin", "engineering"],
    ))
```

Menu path for generic model screens:

```text
/models/{model_name}
```

Do not create frontend routes for normal models.

## Icons

Use icon names supported by `frontend/src/components/layout/MainLayout.vue`.

Current useful icons include:

- `LayoutDashboard`
- `MonitorSmartphone`
- `Users`
- `ShieldCheck`
- `Building2`
- `LayoutGrid`
- `ClipboardList`
- `Box`
- `Clock`
- `Database`
- `Settings`
- `BarChart3`

If a module needs a new generic icon, add it to the framework icon map once. Do not hardcode a module-specific menu component.

## Demo Data

Put sample records in `backend/demo`. Demo data should be safe to delete and recreate.

Use demo records to prove:

- forms load
- lists render
- relations display
- search/group-by works
- action buttons can be clicked

## Data Loading Rules

Keep data files simple:

- no business logic in data files
- use symbolic references for relationships
- use `noupdate=True` for records that should not be overwritten
- keep demo data separate from required init data
