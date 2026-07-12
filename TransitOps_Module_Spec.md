# TransitOps — Module Specification
**Smart Transport Operations Platform — Odoo-style spec adapted for custom TS/Vue/Python framework**
**Hackathon window: 5 hours**

---

## 0. How to Read This Spec

This is written the way an Odoo module spec would be written — model by model, field by field, with domains, constraints, computed fields, state machines, and button logic — but adapted to your framework's **Role** system instead of Odoo's **Groups**, and your **Menu + Access Rule** system instead of Odoo's `ir.ui.menu` / `ir.rule`.

For every model you get:
- **Fields table** (name, type, required, unique, default, notes)
- **States** (if the model has a lifecycle)
- **Business logic / automations** (what fires on create/update — like Odoo's `@api.constrains`, `@api.onchange`, server actions)
- **Buttons** (name, visibility condition, action, allowed roles)
- **Access matrix row** (who can Create/Read/Update/Delete, and whether it's scoped to "own records" or "all records")

---

## 1. Roles

| Role | Code | Purpose |
|---|---|---|
| Admin | `admin` | System setup, user/role management, unlocks accounts, full access override |
| Fleet Manager | `fleet_manager` | Owns Vehicles, Maintenance, Regions; oversees fleet efficiency |
| Driver | `driver` | Creates/dispatches trips, sees own trips only |
| Safety Officer | `safety_officer` | Owns Driver compliance, license validity, safety scores |
| Financial Analyst | `financial_analyst` | Owns Fuel Logs, Expenses, Reports/ROI |

> Only `fleet_manager`, `driver`, `safety_officer`, `financial_analyst` are selectable at **Sign Up**. `admin` is seeded/created manually — never self-assignable.

---

## 2. Authentication & Signup

### 2.1 Sign Up
Fields on sign-up form:

| Field | Type | Required | Notes |
|---|---|---|---|
| Full Name | Char | Yes | |
| Email | Char (unique) | Yes | Used as login |
| Password | Char (hashed) | Yes | Min 8 chars, 1 number, 1 special char |
| Confirm Password | Char | Yes | Must match Password |
| Role | Selection (many2one to `role`) | Yes | Dropdown: Fleet Manager / Driver / Safety Officer / Financial Analyst |
| Contact Number | Char | Optional | Pre-fills Driver profile if role = Driver |

**Logic:**
- On submit → create `res.users` record with `role_id` set, `is_active = true`, `failed_login_attempts = 0`.
- If `Role = Driver` → auto-create a linked `driver` record (status = `available`) so the user immediately appears in the driver pool. `driver.user_id` = new user.
- Email must be unique across `res.users` — server-side constraint, not just UI validation.

### 2.2 Sign In
Fields: Email, Password (**no role selector on sign-in** — role is already attached to the account; a role picker at login, as shown in the Excalidraw mock, is not used here since it would let a user impersonate a role they don't have).

**Lockout logic (mandatory rule):**
- `res.users` gets two new fields: `failed_login_attempts` (Integer, default 0), `locked_until` (Datetime, nullable).
- On failed password match → `failed_login_attempts += 1`.
- On success → reset `failed_login_attempts = 0`, `locked_until = null`.
- When `failed_login_attempts >= 5` → set `locked_until = now() + 15 minutes`, block login with message: *"Account locked due to multiple failed attempts. Try again after 15 minutes."*
- If `locked_until` is set and in the future → block login regardless of password correctness, show remaining lockout time.
- If `locked_until` has passed → allow login attempt again, counter resets on next successful login.
- **Admin override:** Admin can manually unlock any account via an **"Unlock Account"** button on the User record (sets `failed_login_attempts = 0`, `locked_until = null`).

---

## 3. Models

### 3.1 `region`
Seed data on app start (like a timezone seed list) — e.g. North Zone, South Zone, East Zone, West Zone, Central.

| Field | Type | Required | Unique | Default | Notes |
|---|---|---|---|---|---|
| name | Char | Yes | Yes | — | e.g. "West Zone" |
| code | Char | Yes | Yes | — | e.g. "WZ" |
| active | Boolean | Yes | — | true | soft-disable without deleting |

**Access:** Read-only for all roles except Admin/Fleet Manager (Create/Update). Used as a `many2one` dropdown on `vehicle`.

---

### 3.2 `driver` (extends/links to `res.users`)

| Field | Type | Required | Unique | Default | Notes |
|---|---|---|---|---|---|
| user_id | Many2one → res.users | No | Yes | — | null if driver has no login (manually added by Fleet Manager) |
| name | Char | Yes | — | — | |
| license_number | Char | Yes | Yes | — | |
| license_category | Selection [LMV, HMV, Heavy Truck, Trailer] | Yes | — | — | |
| license_expiry_date | Date | Yes | — | — | |
| contact_number | Char | Yes | — | — | |
| safety_score | Float (0–100) | No | — | 100 | updated by Safety Officer |
| status | Selection [available, on_trip, off_duty, suspended] | Yes | — | available | |
| region_id | Many2one → region | No | — | — | home base |

**Computed:**
- `license_valid` (Boolean, computed) = `license_expiry_date >= today`. Not stored, used in domain filters.

**Business logic / constraints:**
- **Dispatch eligibility rule:** a driver can be selected for a trip only if `status = available` AND `license_valid = true`. Enforced as a **domain filter** on the trip's driver field AND a **server-side constraint** on trip dispatch (never trust client filtering alone).
- A `suspended` driver can never appear in the dispatch dropdown, full stop — even if license is valid.
- Cannot delete a driver who has trip history — only allow status change to `off_duty`/`suspended`.

**Buttons:**
| Button | Visible when | Action | Roles |
|---|---|---|---|
| Suspend | status ≠ suspended | status → suspended | Safety Officer, Admin |
| Reinstate | status = suspended | status → available | Safety Officer, Admin |
| Adjust Safety Score | always | opens inline edit for safety_score | Safety Officer, Admin |

---

### 3.3 `vehicle`

| Field | Type | Required | Unique | Default | Notes |
|---|---|---|---|---|---|
| registration_number | Char | Yes | **Yes** | — | primary business key |
| name_model | Char | Yes | — | — | e.g. "Van-05" |
| type | Selection [Van, Truck, Trailer, Bike] | Yes | — | — | |
| max_load_capacity | Float (kg) | Yes | — | — | |
| odometer | Float (km) | Yes | — | 0 | auto-updated on trip completion |
| acquisition_cost | Float (currency) | Yes | — | — | used in ROI calc |
| status | Selection [available, on_trip, in_shop, retired] | Yes | — | available | |
| region_id | Many2one → region | No | — | — | |

**Computed (not stored, calculated on read / report):**
- `total_operational_cost` = SUM(fuel_log.cost) + SUM(maintenance_log.cost) for this vehicle.
- `fuel_efficiency` = SUM(trip.actual_distance) / SUM(fuel_log.liters).
- `roi` = (Revenue − (Maintenance + Fuel)) / Acquisition Cost.

**Business logic / constraints:**
- `registration_number` uniqueness enforced at DB level (unique index), not just UI.
- **Dispatch pool rule:** vehicles with `status IN (in_shop, retired)` must NEVER appear in the trip's vehicle dropdown — enforced as domain filter + server constraint on dispatch.
- Cannot hard-delete a vehicle with trip/maintenance/fuel history — only allow `retired`.

**Buttons:**
| Button | Visible when | Action | Roles |
|---|---|---|---|
| Retire Vehicle | status ≠ retired, no active trip | status → retired | Fleet Manager, Admin |
| Reactivate | status = retired | status → available | Fleet Manager, Admin |

---

### 3.4 `trip`

| Field | Type | Required | Notes |
|---|---|---|---|
| source | Char | Yes | |
| destination | Char | Yes | |
| vehicle_id | Many2one → vehicle | Yes (before dispatch) | domain: `status = available` |
| driver_id | Many2one → driver | Yes (before dispatch) | domain: `status = available AND license_valid = true` |
| cargo_weight | Float (kg) | Yes | must be ≤ `vehicle_id.max_load_capacity` |
| planned_distance | Float (km) | Yes | |
| actual_distance | Float (km) | No | filled on completion |
| fuel_consumed | Float (L) | No | filled on completion |
| final_odometer | Float | No | filled on completion; must be ≥ vehicle's current odometer |
| status | Selection [draft, dispatched, completed, cancelled] | Yes, default `draft` | |
| created_by | Many2one → res.users | Yes, auto | for "own records" access rule |
| dispatched_at | Datetime | No | auto-stamped |
| completed_at | Datetime | No | auto-stamped |

**State machine:**
```
draft → dispatched → completed
draft → dispatched → cancelled
draft → cancelled
```
(No transition out of `completed` or `cancelled` — terminal states.)

**Business logic / automations (this is the core rule engine of the module):**
1. **On Create (draft):** vehicle/driver dropdowns are filtered to `available` + valid-license, non-suspended, non-retired/in_shop only.
2. **Constraint — cargo vs capacity:** `cargo_weight ≤ vehicle_id.max_load_capacity`, else block save with error.
3. **Constraint — no double-booking:** server re-checks at dispatch time (not just at draft creation) that `vehicle_id.status = available` and `driver_id.status = available`. Two drafts could reference the same vehicle; only the first to dispatch wins — reject the second with "Vehicle no longer available."
4. **On Dispatch button:** status → `dispatched`; `vehicle_id.status → on_trip`; `driver_id.status → on_trip`; stamp `dispatched_at = now()`.
5. **On Complete button:** requires `final_odometer` and `fuel_consumed` input; status → `completed`; `vehicle_id.status → available`; `driver_id.status → available`; `vehicle_id.odometer = final_odometer`; auto-create a linked `fuel_log` entry from `fuel_consumed`; stamp `completed_at = now()`.
6. **On Cancel button:** allowed from `draft` or `dispatched`. If cancelling from `dispatched` → restore `vehicle_id.status → available`, `driver_id.status → available`. If cancelling from `draft` → no status restore needed (nothing was locked yet).

**Buttons:**
| Button | Visible when | Action | Roles |
|---|---|---|---|
| Dispatch | status = draft | runs automation #4 | Driver (own), Fleet Manager, Admin |
| Complete Trip | status = dispatched | opens final_odometer/fuel_consumed form → automation #5 | Driver (own), Fleet Manager, Admin |
| Cancel | status in (draft, dispatched) | automation #6 | Driver (own), Fleet Manager, Admin |

---

### 3.5 `maintenance_log`

| Field | Type | Required | Notes |
|---|---|---|---|
| vehicle_id | Many2one → vehicle | Yes | |
| maintenance_type | Selection [Oil Change, Tyre, Brake, Engine, Body, Other] | Yes | |
| description | Text | No | |
| cost | Float | Yes | rolls into total_operational_cost |
| start_date | Date | Yes | |
| end_date | Date | No | required to close |
| status | Selection [active, closed] | Yes, default `active` | |
| created_by | Many2one → res.users | Yes, auto | |

**Business logic / automations:**
- **On Create (status = active):** `vehicle_id.status → in_shop` immediately, which removes it from the trip dispatch pool (enforced via the domain filter in 3.4).
- **On Close button:** requires `end_date`; status → `closed`; `vehicle_id.status → available` **unless** the vehicle's status was independently set to `retired` — never un-retire a vehicle via maintenance closure.
- A vehicle can only have **one active maintenance log at a time** — constraint blocks creating a second `active` record for a vehicle that already has one.

**Buttons:**
| Button | Visible when | Action | Roles |
|---|---|---|---|
| Close Maintenance | status = active | automation above | Fleet Manager, Admin |

---

### 3.6 `fuel_log`

| Field | Type | Required | Notes |
|---|---|---|---|
| vehicle_id | Many2one → vehicle | Yes | |
| trip_id | Many2one → trip | No | auto-linked if generated from trip completion |
| liters | Float | Yes | |
| cost | Float | Yes | |
| date | Date | Yes, default today | |
| odometer_reading | Float | No | |

**Access:** Financial Analyst (Create/Read/Update all), Fleet Manager (Read all, Create), Admin (all). Driver/Safety Officer: no access.

---

### 3.7 `expense`

| Field | Type | Required | Notes |
|---|---|---|---|
| vehicle_id | Many2one → vehicle | Yes | |
| expense_type | Selection [Toll, Maintenance, Fine, Other] | Yes | |
| amount | Float | Yes | |
| date | Date | Yes, default today | |
| description | Text | No | |

**Access:** Financial Analyst (full), Fleet Manager (Read all, Create), Admin (all). Driver/Safety Officer: no access.

---

## 4. Access Matrix (Model × Role × CRUD × Record Scope)

`A` = All records, `O` = Own records only, `–` = no access, letters = C/R/U/D

| Model | Admin | Fleet Manager | Driver | Safety Officer | Financial Analyst |
|---|---|---|---|---|---|
| region | CRUD·A | CRUD·A | R·A | R·A | R·A |
| driver | CRUD·A | CRU·A (no delete) | R·A (read pool only) | CRUD·A | R·A |
| vehicle | CRUD·A | CRUD·A | R·A (read pool only) | R·A | R·A |
| trip | CRUD·A | CRUD·A | **CRUD·O** (own created/assigned trips only) | R·A (monitor only) | R·A (for cost reports) |
| maintenance_log | CRUD·A | CRUD·A | – | – | R·A |
| fuel_log | CRUD·A | CRU·A | – | – | CRUD·A |
| expense | CRUD·A | CRU·A | – | – | CRUD·A |
| res.users | CRUD·A | R·O (self) | R·O (self) | R·O (self) | R·O (self) |

**Driver record rule detail:** `trip` visibility for role `driver` = `created_by = current_user OR driver_id.user_id = current_user`. This covers both "trips I created" and "trips assigned to me by a Fleet Manager."

---

## 5. Menus

| Menu | Sub-menu | Visible to roles |
|---|---|---|
| Dashboard | — | All roles (content varies by role — see §6) |
| Fleet | Vehicles | Admin, Fleet Manager, Safety Officer (RO), Financial Analyst (RO), Driver (RO) |
| Fleet | Regions | Admin, Fleet Manager |
| Drivers | Driver Directory | Admin, Fleet Manager (RO), Safety Officer (full) |
| Trips | Trip Board (all) | Admin, Fleet Manager |
| Trips | My Trips | Driver |
| Maintenance | Maintenance Log | Admin, Fleet Manager |
| Finance | Fuel Logs | Admin, Fleet Manager, Financial Analyst |
| Finance | Expenses | Admin, Fleet Manager, Financial Analyst |
| Reports | Fuel Efficiency, Fleet Utilization, Operational Cost, ROI | Admin, Fleet Manager, Financial Analyst |
| Settings | Users & Roles | Admin only |

A menu with zero visible sub-items for the current role should not render at all.

---

## 6. Dashboard KPIs

| KPI | Formula | Visible to |
|---|---|---|
| Active Vehicles | count(vehicle, status != retired) | All |
| Available Vehicles | count(vehicle, status = available) | All |
| Vehicles in Maintenance | count(vehicle, status = in_shop) | Fleet Manager, Admin |
| Active Trips | count(trip, status = dispatched) | All |
| Pending Trips | count(trip, status = draft) | Fleet Manager, Admin, Driver (own only) |
| Drivers On Duty | count(driver, status = on_trip) | Fleet Manager, Safety Officer, Admin |
| Fleet Utilization % | count(vehicle, status=on_trip) / count(vehicle, active) × 100 | All |

Filters: vehicle type, status, region — apply across dashboard widgets.

---

## 7. Reports & Analytics

| Report | Formula | Export |
|---|---|---|
| Fuel Efficiency | Σ actual_distance / Σ fuel liters (per vehicle) | CSV |
| Fleet Utilization | as above | CSV |
| Operational Cost | Σ fuel_log.cost + Σ maintenance_log.cost (per vehicle) | CSV |
| Vehicle ROI | (Revenue − (Maintenance + Fuel)) / Acquisition Cost | CSV |

PDF export = bonus, not in core phases.

---

## 8. Build Phases (5-Hour Hackathon Plan)

| Phase | Time | Scope | Status |
|---|---|---|---|
| **Phase 0 — Setup** | 0:00–0:20 (20m) | Scaffold project, DB schema/migrations for all 8 models, seed `region` + Admin user | ✅ Done — built TransitOps model schema for user/region/driver/vehicle/trip/maintenance/fuel/expense and seeded roles, regions, timezone data path, and Admin user |
| **Phase 1 — Auth & RBAC** | 0:20–1:10 (50m) | • **Sign Up** screen (name, email, password, confirm password, role select) with auto driver-record creation<br>• **Sign In** screen (email, password, no role picker) with 5-attempt lockout<br>• Role-based menu rendering, access-matrix middleware<br>• **Rebrand:** rename framework/app branding from `znova` → **TransitOps** everywhere — app name, page titles, logo/nav text, favicon reference, README, package name | ✅ Done — signup role selection now limits self-signup to operational roles, creates linked driver records for driver signup, sign-in lockout, role menus, access middleware, and rebrand are built |
| **Phase 2 — Master Data** | 1:10–2:00 (50m) | Vehicle CRUD, Driver CRUD, Region CRUD, uniqueness constraints, status enums | ✅ Done — Region, Vehicle, and Driver are split into dedicated model files with CRUD metadata, status enums, framework-level uniqueness, and Phase 2 CRUD/uniqueness tests |
| **Phase 3 — Trip Engine** | 2:00–3:10 (70m) | Trip create/dispatch/complete/cancel, all validation rules (§3.4), domain filters on dropdowns | ⬜ Not Started |
| **Phase 4 — Maintenance + Finance** | 3:10–4:00 (50m) | Maintenance log + auto in_shop/available toggling, Fuel logs, Expenses, cost roll-up computation | ⬜ Not Started |
| **Phase 5 — Dashboard & Reports** | 4:00–4:40 (40m) | KPI widgets, filters, report calculations, CSV export | ⬜ Not Started |
| **Phase 6 — Polish & Demo Prep** | 4:40–5:00 (20m) | Bug pass on business rules, seed demo data matching the Example Workflow (§5 of PS), rehearse demo | ⬜ Not Started |

**Status legend:** ⬜ Not Started · 🟨 In Progress · ✅ Done

> **Agent rule:** update this Status column the moment a phase's scope is fully implemented and working — not before. Never mark a phase ✅ if any bullet in its scope is incomplete or untested.

If time overruns, cut in this order: CSV export → dashboard filters → ROI report → ratings polish. Never cut Phase 1/3 (auth + trip validation) — these are the graded core rules.

---

## 9. Bonus / Extra Features (build only after Phase 6, in this order)

1. Search, filters, sorting on list views
2. Charts on Dashboard/Reports (visual, not just numbers)
3. Email reminders for expiring driver licenses
4. Vehicle document management (upload/attach docs)
5. Dark mode
6. PDF export for reports

---

## 10. Open Implementation Notes

- All server-side business rules in §3 must be enforced **on the backend**, not just disabled dropdowns in Vue — a judge or malicious client could bypass client-side filters.
- Treat `driver.license_valid` and dispatch-pool filtering as **query-time computed**, not stored, so it's always accurate without a cron job.
- `created_by` should be set automatically on every model that needs "own records" scoping (currently only `trip` needs it for the Driver role).
