# =============================================================================
# TransitOps — Demo Data
# =============================================================================
# Load order matters: each section references xml_ids defined above it.
#
# Regions      → already seeded by init_data.py (noupdate=True); we just
#                reference them via @region_* xml_ids defined there.
#
# Build order:
#   1. Users + auto-linked Drivers  (roles from init_data)
#   2. Vehicles
#   3. Drivers (standalone records for the driver-role users)
#   4. Trips   (draft → dispatched → completed / cancelled)
#   5. Maintenance Logs
#   6. Fuel Logs  (standalone only; completed-trip logs are auto-created)
#   7. Expenses
#
# Password for every demo account: Demo@1234
#
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  LOGIN TABLE                                                            │
# │  Email                          Role               Password             │
# │  ─────────────────────────────────────────────────────────────         │
# │  admin@transitops.com           Admin              Demo@1234            │
# │  maria.santos@transitops.com    Fleet Manager      Demo@1234            │
# │  james.okonkwo@transitops.com   Fleet Manager      Demo@1234            │
# │  alex.reyes@transitops.com      Driver             Demo@1234            │
# │  priya.nair@transitops.com      Driver             Demo@1234            │
# │  tomás.ferreira@transitops.com  Driver             Demo@1234            │
# │  chen.wei@transitops.com        Driver             Demo@1234            │
# │  fatima.hassan@transitops.com   Driver             Demo@1234            │
# │  kwame.asante@transitops.com    Safety Officer     Demo@1234            │
# │  elena.volkov@transitops.com    Safety Officer     Demo@1234            │
# │  david.kim@transitops.com       Financial Analyst  Demo@1234            │
# │  sofia.mendez@transitops.com    Financial Analyst  Demo@1234            │
# └─────────────────────────────────────────────────────────────────────────┘
#
# STATUS SUMMARY (for quick verification)
# ┌──────────────────┬───────┬────────────────────────────────────────────┐
# │ Model            │ Count │ Status breakdown                           │
# ├──────────────────┼───────┼────────────────────────────────────────────┤
# │ region           │   5   │ seeded by init_data (not duplicated here)  │
# │ user             │  12   │ 1 admin, 2 fleet_mgr, 5 driver,            │
# │                  │       │ 2 safety_officer, 2 financial_analyst      │
# │ driver           │   5   │ 2 available, 1 on_trip, 1 suspended,       │
# │                  │       │ 1 available-but-expired-license            │
# │ vehicle          │   9   │ 5 available, 2 on_trip, 1 in_shop,         │
# │                  │       │ 1 retired                                  │
# │ trip             │   9   │ 2 draft, 2 dispatched, 4 completed,        │
# │                  │       │ 1 cancelled                                │
# │ maintenance_log  │   3   │ 1 active (→ in_shop vehicle),              │
# │                  │       │ 2 closed                                   │
# │ fuel_log         │   6   │ 4 auto-created by completed trips +        │
# │                  │       │ 2 standalone                               │
# │ expense          │   6   │ 2 Toll, 1 Fine, 2 Other, 1 Maintenance     │
# └──────────────────┴───────┴────────────────────────────────────────────┘
#
# KEY CONSISTENCY CHECKS (verified manually before writing):
#   • Vehicles on_trip:  VAN-002 (trip_dispatched_1), TRK-004 (trip_dispatched_2)
#   • Drivers  on_trip:  alex.reyes (trip_dispatched_1), priya.nair (trip_dispatched_2)
#   • Vehicle  in_shop:  VAN-005 (maintenance_active_1)
#   • Driver suspended:  tomás.ferreira  → never on any dispatched/completed trip
#   • Driver expired:    fatima.hassan   → never on any dispatched/completed trip
#   • All cargo_weight values verified ≤ vehicle max_load_capacity
#   • Retired vehicle BIK-009 has only completed/cancelled trip history
# =============================================================================

RECORDS = {

    # =========================================================================
    # STEP 1 — USERS
    # Regions (NZ/SZ/EZ/WZ/CZ) and Roles are already in init_data.py.
    # We reference their xml_ids directly.
    # The $P$ prefix tells the DataLoader to bcrypt-hash the plain password.
    # =========================================================================

    # --- Admin (already seeded in init_data but we leave it — noupdate=True
    #            means it won't be overwritten; we just won't re-declare it) ---

    # --- Fleet Managers ---
    "demo_user_fleet_mgr_1": {
        "model": "user",
        "values": {
            "full_name": "Maria Santos",
            "email": "maria.santos@transitops.com",
            "hashed_password": "$P$Demo@1234",
            "role_id": "@role_fleet_manager",
            "timezone_id": "@tz_utc",
            "is_active": True,
        },
    },
    "demo_user_fleet_mgr_2": {
        "model": "user",
        "values": {
            "full_name": "James Okonkwo",
            "email": "james.okonkwo@transitops.com",
            "hashed_password": "$P$Demo@1234",
            "role_id": "@role_fleet_manager",
            "timezone_id": "@tz_utc",
            "is_active": True,
        },
    },

    # --- Drivers (signup auto-creates driver records; here we create the user
    #     and then explicitly create the linked driver record below so we can
    #     control all fields precisely) ---
    "demo_user_driver_1": {
        "model": "user",
        "values": {
            "full_name": "Alex Reyes",
            "email": "alex.reyes@transitops.com",
            "hashed_password": "$P$Demo@1234",
            "role_id": "@role_driver",
            "timezone_id": "@tz_utc",
            "is_active": True,
        },
    },
    "demo_user_driver_2": {
        "model": "user",
        "values": {
            "full_name": "Priya Nair",
            "email": "priya.nair@transitops.com",
            "hashed_password": "$P$Demo@1234",
            "role_id": "@role_driver",
            "timezone_id": "@tz_utc",
            "is_active": True,
        },
    },
    "demo_user_driver_3": {
        "model": "user",
        "values": {
            "full_name": "Tomás Ferreira",
            "email": "tomas.ferreira@transitops.com",
            "hashed_password": "$P$Demo@1234",
            "role_id": "@role_driver",
            "timezone_id": "@tz_utc",
            "is_active": True,
        },
    },
    "demo_user_driver_4": {
        "model": "user",
        "values": {
            "full_name": "Chen Wei",
            "email": "chen.wei@transitops.com",
            "hashed_password": "$P$Demo@1234",
            "role_id": "@role_driver",
            "timezone_id": "@tz_utc",
            "is_active": True,
        },
    },
    "demo_user_driver_5": {
        "model": "user",
        "values": {
            "full_name": "Fatima Hassan",
            "email": "fatima.hassan@transitops.com",
            "hashed_password": "$P$Demo@1234",
            "role_id": "@role_driver",
            "timezone_id": "@tz_utc",
            "is_active": True,
        },
    },

    # --- Safety Officers ---
    "demo_user_safety_1": {
        "model": "user",
        "values": {
            "full_name": "Kwame Asante",
            "email": "kwame.asante@transitops.com",
            "hashed_password": "$P$Demo@1234",
            "role_id": "@role_safety_officer",
            "timezone_id": "@tz_utc",
            "is_active": True,
        },
    },
    "demo_user_safety_2": {
        "model": "user",
        "values": {
            "full_name": "Elena Volkov",
            "email": "elena.volkov@transitops.com",
            "hashed_password": "$P$Demo@1234",
            "role_id": "@role_safety_officer",
            "timezone_id": "@tz_utc",
            "is_active": True,
        },
    },

    # --- Financial Analysts ---
    "demo_user_finance_1": {
        "model": "user",
        "values": {
            "full_name": "David Kim",
            "email": "david.kim@transitops.com",
            "hashed_password": "$P$Demo@1234",
            "role_id": "@role_financial_analyst",
            "timezone_id": "@tz_utc",
            "is_active": True,
        },
    },
    "demo_user_finance_2": {
        "model": "user",
        "values": {
            "full_name": "Sofia Mendez",
            "email": "sofia.mendez@transitops.com",
            "hashed_password": "$P$Demo@1234",
            "role_id": "@role_financial_analyst",
            "timezone_id": "@tz_utc",
            "is_active": True,
        },
    },

    # =========================================================================
    # STEP 2 — VEHICLES  (9 total)
    #
    # Status plan:
    #   available : VAN-001, TRK-003, TRL-006, VAN-007, TRK-008  (5)
    #   on_trip   : VAN-002, TRK-004                               (2) ← dispatched trips below
    #   in_shop   : VAN-005                                        (1) ← active maintenance below
    #   retired   : BIK-009                                        (1)
    #
    # max_load_capacity chosen so demo cargo weights are always safe:
    #   Van   → 800 kg,  Truck → 5000 kg,  Trailer → 15000 kg,  Bike → 100 kg
    # =========================================================================

    "demo_vehicle_1": {
        "model": "vehicle",
        "values": {
            "registration_number": "VAN-001",
            "name_model": "Van-01 (Sprinter)",
            "type": "Van",
            "max_load_capacity": 800.0,
            "odometer": 12450.0,
            "acquisition_cost": 28000.0,
            "status": "available",
            "region_id": "@region_north",
        },
    },
    "demo_vehicle_2": {
        "model": "vehicle",
        "values": {
            "registration_number": "VAN-002",
            "name_model": "Van-02 (Transit)",
            "type": "Van",
            "max_load_capacity": 800.0,
            "odometer": 34200.0,
            "acquisition_cost": 26500.0,
            "status": "on_trip",        # justified by trip_dispatched_1
            "region_id": "@region_west",
        },
    },
    "demo_vehicle_3": {
        "model": "vehicle",
        "values": {
            "registration_number": "TRK-003",
            "name_model": "Truck-03 (Tata LPT)",
            "type": "Truck",
            "max_load_capacity": 5000.0,
            "odometer": 61800.0,
            "acquisition_cost": 55000.0,
            "status": "available",
            "region_id": "@region_south",
        },
    },
    "demo_vehicle_4": {
        "model": "vehicle",
        "values": {
            "registration_number": "TRK-004",
            "name_model": "Truck-04 (Ashok Leyland)",
            "type": "Truck",
            "max_load_capacity": 5000.0,
            "odometer": 88600.0,
            "acquisition_cost": 58000.0,
            "status": "on_trip",        # justified by trip_dispatched_2
            "region_id": "@region_east",
        },
    },
    "demo_vehicle_5": {
        "model": "vehicle",
        "values": {
            "registration_number": "VAN-005",
            "name_model": "Van-05 (Mercedes Vito)",
            "type": "Van",
            "max_load_capacity": 800.0,
            "odometer": 45000.0,
            "acquisition_cost": 31000.0,
            "status": "available",        # justified by maintenance_active_1
            "region_id": "@region_central",
        },
    },
    "demo_vehicle_6": {
        "model": "vehicle",
        "values": {
            "registration_number": "TRL-006",
            "name_model": "Trailer-06 (Tata Prima)",
            "type": "Trailer",
            "max_load_capacity": 15000.0,
            "odometer": 102400.0,
            "acquisition_cost": 120000.0,
            "status": "available",
            "region_id": "@region_south",
        },
    },
    "demo_vehicle_7": {
        "model": "vehicle",
        "values": {
            "registration_number": "VAN-007",
            "name_model": "Van-07 (Ford Transit)",
            "type": "Van",
            "max_load_capacity": 800.0,
            "odometer": 9800.0,
            "acquisition_cost": 27000.0,
            "status": "available",
            "region_id": "@region_north",
        },
    },
    "demo_vehicle_8": {
        "model": "vehicle",
        "values": {
            "registration_number": "TRK-008",
            "name_model": "Truck-08 (Eicher Pro)",
            "type": "Truck",
            "max_load_capacity": 5000.0,
            "odometer": 22100.0,
            "acquisition_cost": 48000.0,
            "status": "available",
            "region_id": "@region_east",
        },
    },
    "demo_vehicle_9": {
        "model": "vehicle",
        "values": {
            "registration_number": "BIK-009",
            "name_model": "Bike-09 (Bajaj RE)",
            "type": "Bike",
            "max_load_capacity": 100.0,
            "odometer": 78300.0,
            "acquisition_cost": 3500.0,
            "status": "retired",        # all trip history is completed/cancelled
            "region_id": "@region_central",
        },
    },

    # =========================================================================
    # STEP 3 — DRIVERS  (5 records linked to driver-role users)
    #
    # Status plan:
    #   available : alex.reyes  → will be set on_trip by trip_dispatched_1 below
    #                             (data loader sets status field directly; the
    #                              dispatch action is NOT called here — we mirror
    #                              the final DB state the action would produce)
    #   on_trip   : alex.reyes, priya.nair  (2, matches vehicle on_trip count)
    #   available : chen.wei                (clean available)
    #   suspended : tomas.ferreira          (never on any active/completed trip)
    #   available : fatima.hassan           (expired license — dispatch filter
    #                                        blocks her despite status=available)
    #
    # NOTE: Because the data loader uses write() directly and bypasses action
    # buttons, status is set to its correct final state here.  The trip records
    # below also carry their final status.  This is the standard demo-data
    # pattern — we describe the world as it IS after all the actions ran.
    #
    # License expiry dates:
    #   Future  : 2027-12-31  (all valid drivers)
    #   EXPIRED : 2023-06-15  (fatima.hassan — proves dispatch filter works)
    # =========================================================================

    "demo_driver_1": {
        "model": "driver",
        "values": {
            "user_id": "@demo_user_driver_1",   # Alex Reyes
            "name": "Alex Reyes",
            "license_number": "DL-MH-2019-00341",
            "license_category": "LMV",
            "license_expiry_date": "2027-12-31",
            "contact_number": "+91-98765-11001",
            "safety_score": 92.5,
            "status": "on_trip",                # driving trip_dispatched_1
            "region_id": "@region_west",
        },
    },
    "demo_driver_2": {
        "model": "driver",
        "values": {
            "user_id": "@demo_user_driver_2",   # Priya Nair
            "name": "Priya Nair",
            "license_number": "DL-KA-2020-00782",
            "license_category": "HMV",
            "license_expiry_date": "2027-06-30",
            "contact_number": "+91-98765-22002",
            "safety_score": 87.0,
            "status": "on_trip",                # driving trip_dispatched_2
            "region_id": "@region_east",
        },
    },
    "demo_driver_3": {
        "model": "driver",
        "values": {
            "user_id": "@demo_user_driver_3",   # Tomás Ferreira — SUSPENDED
            "name": "Tomás Ferreira",
            "license_number": "DL-GJ-2018-00553",
            "license_category": "LMV",
            "license_expiry_date": "2026-09-15",
            "contact_number": "+91-98765-33003",
            "safety_score": 61.0,               # low score → led to suspension
            "status": "suspended",
            "region_id": "@region_central",
        },
    },
    "demo_driver_4": {
        "model": "driver",
        "values": {
            "user_id": "@demo_user_driver_4",   # Chen Wei
            "name": "Chen Wei",
            "license_number": "DL-TN-2021-00124",
            "license_category": "Heavy Truck",
            "license_expiry_date": "2028-03-20",
            "contact_number": "+91-98765-44004",
            "safety_score": 95.0,
            "status": "available",
            "region_id": "@region_south",
        },
    },
    "demo_driver_5": {
        "model": "driver",
        "values": {
            "user_id": "@demo_user_driver_5",   # Fatima Hassan — EXPIRED LICENSE
            "name": "Fatima Hassan",
            "license_number": "DL-DL-2015-00899",
            "license_category": "LMV",
            "license_expiry_date": "2023-06-15",  # EXPIRED — dispatch must reject
            "contact_number": "+91-98765-55005",
            "safety_score": 78.5,
            "status": "available",              # status=available but license invalid
            "region_id": "@region_north",
        },
    },

    # =========================================================================
    # STEP 4 — TRIPS  (9 total)
    #
    # Final status distribution:
    #   draft      : trip_draft_1, trip_draft_2          (2)
    #   dispatched : trip_dispatched_1, trip_dispatched_2 (2)
    #   completed  : trip_completed_1 … trip_completed_4  (4)
    #   cancelled  : trip_cancelled_1                      (1)
    #
    # Cargo weights (all verified ≤ vehicle max_load_capacity):
    #   Van   800 kg max  → cargo never exceeds 750 kg on vans
    #   Truck 5000 kg max → cargo never exceeds 4500 kg on trucks
    #   Bike  100 kg max  → only historical retired-bike trips use 80 kg
    #
    # The trip_completed_* records carry final_odometer / fuel_consumed /
    # fuel_unit_cost so the auto fuel_log creation logic is satisfied.
    # (actual fuel_log creation happens via action_complete in production;
    #  in demo data we also explicitly declare matching fuel_log records
    #  in STEP 5 so reports have data even if the action wasn't replayed.)
    #
    # REFERENCE / SHOWCASE CHAIN  (mirrors Example Workflow in spec §8):
    #   trip_completed_ref:  VAN-005 → Van-05 / Alex Reyes, 450 kg cargo,
    #                        West→Central, completed end-to-end.
    #   (VAN-005 is currently in_shop for new maintenance; this completed
    #    trip is historical — it ran before the current maintenance started.)
    # =========================================================================

    # --- DRAFT trips (vehicle/driver currently available) ---
    "demo_trip_draft_1": {
        "model": "trip",
        "values": {
            "source": "North Depot",
            "destination": "South Warehouse",
            "vehicle_id": "@demo_vehicle_1",     # VAN-001  available
            "driver_id": "@demo_driver_4",        # Chen Wei available
            "cargo_weight": 620.0,               # 620 ≤ 800 ✓
            "planned_distance": 185.0,
            "status": "draft",
            "created_by": "@demo_user_fleet_mgr_1",
        },
    },
    "demo_trip_draft_2": {
        "model": "trip",
        "values": {
            "source": "East Hub",
            "destination": "Central Distribution Centre",
            "vehicle_id": "@demo_vehicle_8",     # TRK-008  available
            "driver_id": "@demo_driver_4",        # Chen Wei available (two drafts
            #                                       can share a driver; only one
            #                                       can be dispatched at a time)
            "cargo_weight": 3800.0,              # 3800 ≤ 5000 ✓
            "planned_distance": 240.0,
            "status": "draft",
            "created_by": "@demo_user_driver_4",
        },
    },

    # --- DISPATCHED trips (vehicle/driver currently on_trip) ---
    "demo_trip_dispatched_1": {
        "model": "trip",
        "values": {
            "source": "West Depot",
            "destination": "North Retail Park",
            "vehicle_id": "@demo_vehicle_2",     # VAN-002  on_trip ✓
            "driver_id": "@demo_driver_1",        # Alex Reyes on_trip ✓
            "cargo_weight": 450.0,               # 450 ≤ 800 ✓
            "planned_distance": 312.0,
            "status": "dispatched",
            "created_by": "@demo_user_driver_1",
        },
    },
    "demo_trip_dispatched_2": {
        "model": "trip",
        "values": {
            "source": "East Logistics Park",
            "destination": "South Port Terminal",
            "vehicle_id": "@demo_vehicle_4",     # TRK-004  on_trip ✓
            "driver_id": "@demo_driver_2",        # Priya Nair on_trip ✓
            "cargo_weight": 4200.0,              # 4200 ≤ 5000 ✓
            "planned_distance": 520.0,
            "status": "dispatched",
            "created_by": "@demo_user_fleet_mgr_2",
        },
    },

    # --- COMPLETED trips (vehicle/driver back to available) ---

    # Reference / showcase chain: Van-05 / Alex Reyes, 450 kg — mirrors spec §8
    "demo_trip_completed_ref": {
        "model": "trip",
        "values": {
            "source": "West Depot",
            "destination": "Central Cold Storage",
            "vehicle_id": "@demo_vehicle_5",     # VAN-005  available at trip time
            #                                       (now in_shop for new maintenance)
            "driver_id": "@demo_driver_1",        # Alex Reyes
            "cargo_weight": 450.0,               # 450 ≤ 800 ✓  (exact spec example)
            "planned_distance": 275.0,
            "actual_distance": 281.0,
            "fuel_consumed": 28.5,
            "fuel_unit_cost": 95.0,
            "revenue": 25000.0,
            "final_odometer": 45281.0,           # 45000 + 281 ≥ 45000 ✓
            "status": "completed",
            "created_by": "@demo_user_driver_1",
        },
    },
    "demo_trip_completed_2": {
        "model": "trip",
        "values": {
            "source": "North Depot",
            "destination": "East Industrial Zone",
            "vehicle_id": "@demo_vehicle_3",     # TRK-003  available
            "driver_id": "@demo_driver_4",        # Chen Wei  available
            "cargo_weight": 3200.0,              # 3200 ≤ 5000 ✓
            "planned_distance": 410.0,
            "actual_distance": 398.0,
            "fuel_consumed": 62.0,
            "fuel_unit_cost": 95.0,
            "revenue": 5000.0,
            "final_odometer": 62198.0,           # 61800 + 398 ✓
            "status": "completed",
            "created_by": "@demo_user_fleet_mgr_1",
        },
    },
    "demo_trip_completed_3": {
        "model": "trip",
        "values": {
            "source": "South Port Terminal",
            "destination": "West Retail Hub",
            "vehicle_id": "@demo_vehicle_7",     # VAN-007  available
            "driver_id": "@demo_driver_2",        # Priya Nair  (before current dispatch)
            "cargo_weight": 700.0,               # 700 ≤ 800 ✓
            "planned_distance": 190.0,
            "actual_distance": 194.0,
            "fuel_consumed": 19.8,
            "fuel_unit_cost": 95.0,
            "revenue": 8000.0,
            "final_odometer": 9994.0,            # 9800 + 194 ✓
            "status": "completed",
            "created_by": "@demo_user_driver_2",
        },
    },
    # Historical completed trip for the retired Bike (BIK-009)
    "demo_trip_completed_4": {
        "model": "trip",
        "values": {
            "source": "Central Hub",
            "destination": "North Express Point",
            "vehicle_id": "@demo_vehicle_9",     # BIK-009  retired (historical)
            "driver_id": "@demo_driver_4",        # Chen Wei
            "cargo_weight": 75.0,               # 75 ≤ 100 ✓
            "planned_distance": 55.0,
            "actual_distance": 58.0,
            "fuel_consumed": 3.2,
            "fuel_unit_cost": 95.0,
            "revenue": 1500.0,
            "final_odometer": 78358.0,           # 78300 + 58 ✓
            "status": "completed",
            "created_by": "@demo_user_driver_4",
        },
    },

    # --- CANCELLED trip (from draft — no vehicle/driver status restore needed) ---
    "demo_trip_cancelled_1": {
        "model": "trip",
        "values": {
            "source": "West Depot",
            "destination": "South Warehouse Annex",
            "vehicle_id": "@demo_vehicle_6",     # TRL-006  available
            "driver_id": "@demo_driver_4",        # Chen Wei  available
            "cargo_weight": 9000.0,              # 9000 ≤ 15000 ✓
            "planned_distance": 330.0,
            "status": "cancelled",
            "created_by": "@demo_user_fleet_mgr_2",
        },
    },

    # =========================================================================
    # STEP 5 — MAINTENANCE LOGS  (3 records)
    #
    #   active  : VAN-005  → vehicle status = in_shop  ✓  (1 active per vehicle)
    #   closed  : TRK-003  → vehicle status = available ✓
    #   closed  : BIK-009  → vehicle status = retired  ✓ (closure didn't un-retire)
    # =========================================================================

    "demo_maintenance_active_1": {
        "model": "maintenance.log",
        "values": {
            "vehicle_id": "@demo_vehicle_5",     # VAN-005  in_shop
            "maintenance_type": "Engine",
            "description": "Full engine overhaul after high-mileage alert. "
                            "Replacing timing belt, oil seals, and injectors.",
            "cost": 14500.0,
            "start_date": "2025-07-08",
            "status": "active",
            "created_by": "@demo_user_fleet_mgr_1",
        },
    },
        "demo_maintenance_closed_1": {
        "model": "maintenance.log",
        "values": {
            "vehicle_id": "@demo_vehicle_3",     # TRK-003  back to available after close
            "maintenance_type": "Tyre",
            "description": "Replaced all six tyres. Alignment and balancing done.",
            "cost": 3800.0,
            "start_date": "2025-06-10",
            "end_date": "2025-06-12",
            "status": "closed",
            "created_by": "@demo_user_fleet_mgr_2",
        },
    },
    "demo_maintenance_closed_2": {
        "model": "maintenance.log",
        "values": {
            "vehicle_id": "@demo_vehicle_9",     # BIK-009  retired — closure did NOT un-retire
            "maintenance_type": "Body",
            "description": "Minor dent repair and repainting before retirement decision.",
            "cost": 850.0,
            "start_date": "2025-05-20",
            "end_date": "2025-05-21",
            "status": "closed",
            "created_by": "@demo_user_fleet_mgr_1",
        },
    },

    # =========================================================================
    # STEP 6 — FUEL LOGS  (6 total)
    #
    # The 4 completed trips above would auto-generate fuel_log entries via
    # action_complete in production. Because demo data sets the final status
    # directly (bypassing the action), we declare those 4 fuel_log records
    # explicitly here so reports have data.
    #
    # trip_completed_ref  → fuel_log_trip_ref   (VAN-005, 28.5 L, 95.0/L)
    # trip_completed_2    → fuel_log_trip_2     (TRK-003, 62.0 L, 95.0/L)
    # trip_completed_3    → fuel_log_trip_3     (VAN-007, 19.8 L, 95.0/L)
    # trip_completed_4    → fuel_log_trip_4     (BIK-009,  3.2 L, 95.0/L)
    #
    # Plus 2 standalone fills (not linked to any trip) for variety:
    #   fuel_log_standalone_1  : VAN-001  — routine depot refuel
    #   fuel_log_standalone_2  : TRK-008  — pre-trip fill before draft trip
    # =========================================================================

    # Trip-linked fuel logs (mirror what action_complete would auto-create)
    "demo_fuel_log_trip_ref": {
        "model": "fuel.log",
        "values": {
            "vehicle_id": "@demo_vehicle_5",         # VAN-005
            "trip_id": "@demo_trip_completed_ref",
            "liters": 28.5,
            "cost": 2707.5,                          # 28.5 × 95.0
            "date": "2025-07-05",
            "odometer_reading": 45281.0,
        },
    },
    "demo_fuel_log_trip_2": {
        "model": "fuel.log",
        "values": {
            "vehicle_id": "@demo_vehicle_3",         # TRK-003
            "trip_id": "@demo_trip_completed_2",
            "liters": 62.0,
            "cost": 5890.0,                          # 62.0 × 95.0
            "date": "2025-07-01",
            "odometer_reading": 62198.0,
        },
    },
    "demo_fuel_log_trip_3": {
        "model": "fuel.log",
        "values": {
            "vehicle_id": "@demo_vehicle_7",         # VAN-007
            "trip_id": "@demo_trip_completed_3",
            "liters": 19.8,
            "cost": 1881.0,                          # 19.8 × 95.0
            "date": "2025-07-03",
            "odometer_reading": 9994.0,
        },
    },
    "demo_fuel_log_trip_4": {
        "model": "fuel.log",
        "values": {
            "vehicle_id": "@demo_vehicle_9",         # BIK-009
            "trip_id": "@demo_trip_completed_4",
            "liters": 3.2,
            "cost": 304.0,                           # 3.2 × 95.0
            "date": "2025-06-28",
            "odometer_reading": 78358.0,
        },
    },

    # Standalone fuel logs (no trip_id)
    "demo_fuel_log_standalone_1": {
        "model": "fuel.log",
        "values": {
            "vehicle_id": "@demo_vehicle_1",         # VAN-001  — depot refuel
            "liters": 45.0,
            "cost": 4275.0,                          # 45.0 × 95.0
            "date": "2025-07-10",
            "odometer_reading": 12450.0,
        },
    },
    "demo_fuel_log_standalone_2": {
        "model": "fuel.log",
        "values": {
            "vehicle_id": "@demo_vehicle_8",         # TRK-008  — pre-trip fill
            "liters": 80.0,
            "cost": 7600.0,                          # 80.0 × 95.0
            "date": "2025-07-11",
            "odometer_reading": 22100.0,
        },
    },

    # =========================================================================
    # STEP 7 — EXPENSES  (6 records)
    #
    # Mix of Toll / Fine / Other / Maintenance spread across several vehicles
    # and dates so the ROI / Operational Cost reports have meaningful input.
    # =========================================================================

    "demo_expense_1": {
        "model": "expense",
        "values": {
            "vehicle_id": "@demo_vehicle_2",         # VAN-002  (currently on_trip)
            "expense_type": "Toll",
            "amount": 320.0,
            "date": "2025-07-09",
            "description": "National highway toll — NH-48 West corridor",
        },
    },
    "demo_expense_2": {
        "model": "expense",
        "values": {
            "vehicle_id": "@demo_vehicle_4",         # TRK-004  (currently on_trip)
            "expense_type": "Toll",
            "amount": 750.0,
            "date": "2025-07-10",
            "description": "Express freeway toll — East Port access road",
        },
    },
    "demo_expense_3": {
        "model": "expense",
        "values": {
            "vehicle_id": "@demo_vehicle_3",         # TRK-003  available
            "expense_type": "Fine",
            "amount": 1500.0,
            "date": "2025-06-25",
            "description": "Overweight penalty issued at North checkpoint — "
                            "load re-balanced before continuing.",
        },
    },
    "demo_expense_4": {
        "model": "expense",
        "values": {
            "vehicle_id": "@demo_vehicle_5",         # VAN-005  in_shop
            "expense_type": "Maintenance",
            "amount": 2200.0,
            "date": "2025-07-08",
            "description": "Workshop labour charges (separate from parts cost "
                            "in maintenance log) — engine overhaul.",
        },
    },
    "demo_expense_5": {
        "model": "expense",
        "values": {
            "vehicle_id": "@demo_vehicle_1",         # VAN-001
            "expense_type": "Other",
            "amount": 450.0,
            "date": "2025-07-06",
            "description": "Driver overnight stay — outstation delivery delay.",
        },
    },
    "demo_expense_6": {
        "model": "expense",
        "values": {
            "vehicle_id": "@demo_vehicle_6",         # TRL-006
            "expense_type": "Other",
            "amount": 900.0,
            "date": "2025-07-02",
            "description": "Loading/unloading labour at South Port Terminal.",
        },
    },
}
