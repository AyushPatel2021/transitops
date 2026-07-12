# TransitOps

TransitOps is a smart transport operations workspace built with FastAPI, Vue 3, TypeScript, PostgreSQL, and a metadata-driven Python model layer. It is designed for fleet teams that need role-aware workflows for vehicles, drivers, regions, trips, maintenance, fuel, expenses, users, and operational reporting.

The application follows an Odoo-style module design: Python models define fields, form/list metadata, access rules, menus, constraints, and lifecycle actions, while the frontend renders CRUD screens from that metadata.

## Current Status

Implemented:

- TransitOps branding, favicon, landing page, dashboard shell, sidebar, dark mode support, and role-aware menus.
- Authentication with email/password, Google OAuth signup/login path, JWT sessions, profile page, and login lockout.
- Signup role selection for operational roles only: Fleet Manager, Driver, Safety Officer, Financial Analyst.
- Admin role seeded manually and not self-selectable.
- Role display names so users see friendly names instead of technical role codes.
- Region, Vehicle, Driver, Trip, Maintenance Log, Fuel Log, and Expense model files split by model type.
- Region seed data and base operational role seed data.
- Phase 2 master data models with CRUD metadata, selections, uniqueness constraints, and tests.

Planned by the module spec:

- Trip dispatch engine with server-side dispatch, complete, cancel, capacity, double-booking, driver eligibility, and vehicle eligibility rules.
- Maintenance workflow that moves vehicles into and out of shop status.
- Fuel and expense cost rollups.
- Dashboard KPIs and filters.
- Fuel Efficiency, Fleet Utilization, Operational Cost, and ROI reports with CSV export.
- Demo data for a full workflow.

## Features

### Roles

TransitOps uses role-based access throughout the API and UI.

| Role | Code | Purpose |
| --- | --- | --- |
| Admin | `admin` | Full system setup, users, roles, unlocks, and override access |
| Fleet Manager | `fleet_manager` | Vehicles, regions, maintenance, trips, and fleet operations |
| Driver | `driver` | Own trips and assigned trips |
| Safety Officer | `safety_officer` | Driver compliance, license validity, and safety scoring |
| Financial Analyst | `financial_analyst` | Fuel logs, expenses, and financial reports |

Only operational roles are selectable during signup. Admin is created through seed data or manual setup.

### Authentication

- Email/password login.
- Google OAuth login and signup.
- Signup role selection.
- Password confirmation and password strength checks.
- Failed login tracking with account lockout after repeated failures.
- Admin unlock support.
- JWT access and refresh token flow.
- User profile and preference UI.

### Fleet Master Data

- Regions: seeded operating zones such as North, South, East, West, and Central.
- Vehicles: registration number, model, type, load capacity, odometer, acquisition cost, status, and region.
- Drivers: linked user, license data, contact number, safety score, status, and region.

### Trips

The spec defines a trip lifecycle:

```text
draft -> dispatched -> completed
draft -> dispatched -> cancelled
draft -> cancelled
```

The planned trip engine validates capacity, driver availability, license validity, vehicle availability, double-booking, status transitions, odometer updates, and automatic fuel-log creation on completion.

### Maintenance And Finance

The spec includes:

- Maintenance logs with active/closed status and vehicle shop-state automation.
- Fuel logs linked to vehicles and optionally trips.
- Expenses by vehicle and expense type.
- Cost rollups for operational reports.

### Reports

Planned reports:

- Fuel Efficiency: distance divided by fuel liters per vehicle.
- Fleet Utilization: active/on-trip vehicle utilization.
- Operational Cost: fuel plus maintenance costs per vehicle.
- ROI: revenue minus operating cost divided by acquisition cost.

### Framework Capabilities

- Metadata-driven CRUD APIs.
- Metadata-driven list and form views.
- Role-aware menu rendering.
- Access-control middleware.
- Field definitions inspired by Odoo-style model metadata.
- PostgreSQL migrations through Alembic.
- WebSocket notification infrastructure.
- Dark and light UI support.

## Tech Stack

Backend:

- Python
- FastAPI
- PostgreSQL
- Alembic
- JWT authentication
- Custom metadata ORM/model framework

Frontend:

- Vue 3
- TypeScript
- Vite
- Pinia
- Vue Router
- Lucide icons

## Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- PostgreSQL 12 or newer
- npm

## Environment Setup

Create the environment file from the example:

```bash
cp .env.example .env
```

Default database settings in `.env.example`:

```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
POSTGRES_DB=enterprise_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://admin:password@localhost:5432/enterprise_db
```

Create the local database if it does not exist:

```bash
createdb -U admin enterprise_db
```

Optional Google OAuth settings:

```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

## Install

Install Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
npm --prefix frontend install
```

## Start Development

Start the backend on port `8000`:

```bash
python run.py
```

`run.py` handles migrations, initial seed data, and starts the FastAPI server.

Start the frontend in another terminal:

```bash
npm --prefix frontend run dev
```

Default URLs:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Fresh Database Setup

To rebuild the local database from scratch:

```bash
python setup_fresh.py
```

To rebuild and load demo data:

```bash
python setup_fresh.py --demo
```

Use this only when it is acceptable to drop local data.

## Default Access

Seeded admin account:

```text
Email: admin@example.com
Password: admin123
```

Operational users should normally be created through signup or by an admin.

## Useful Commands

Backend syntax check:

```bash
python -m py_compile backend/data/menus.py
```

Backend tests:

```bash
pytest backend/tests
```

Frontend build:

```bash
npm --prefix frontend run build
```

Frontend development server:

```bash
npm --prefix frontend run dev
```

## Project Structure

```text
transitops/
├── backend/
│   ├── api/                 # FastAPI endpoints
│   ├── core/                # Model framework, fields, database, ACL, policies
│   ├── data/                # Menus and seed data
│   ├── demo/                # Demo data helpers
│   ├── migrations/          # Alembic migrations
│   ├── models/              # One model type per file
│   ├── services/            # Auth and integration services
│   └── tests/               # Backend tests
├── frontend/
│   ├── src/
│   │   ├── assets/          # TransitOps logo and static assets
│   │   ├── components/      # Shared Vue components
│   │   ├── core/            # API and auth helpers
│   │   ├── stores/          # Pinia stores
│   │   └── views/           # Page views
│   └── package.json
├── TransitOps_Module_Spec.md
├── run.py
├── setup_fresh.py
├── requirements.txt
└── README.md
```

## Model Files

TransitOps keeps each business model in its own file:

- `backend/models/region.py`
- `backend/models/driver.py`
- `backend/models/vehicle.py`
- `backend/models/trip.py`
- `backend/models/maintenance_log.py`
- `backend/models/fuel_log.py`
- `backend/models/expense.py`
- `backend/models/role.py`
- `backend/models/user.py`

Shared TransitOps constants and helpers live in `backend/models/transitops_common.py`.

## Menu Map

| Section | Menu | Roles |
| --- | --- | --- |
| Main | Dashboard | All roles |
| Fleet | Vehicles | All roles, access scoped by policy |
| Fleet | Regions | Admin, Fleet Manager |
| Drivers | Driver Directory | Admin, Fleet Manager, Safety Officer |
| Trips | Trip Board | Admin, Fleet Manager |
| Trips | My Trips | Driver |
| Maintenance | Maintenance Log | Admin, Fleet Manager |
| Finance | Fuel Logs | Admin, Fleet Manager, Financial Analyst |
| Finance | Expenses | Admin, Fleet Manager, Financial Analyst |
| Reports | Fuel Efficiency, Fleet Utilization, Operational Cost, ROI | Admin, Fleet Manager, Financial Analyst |
| Settings | Users | Admin |

## Development Notes

- Keep one model type per file.
- Use the framework model and field APIs instead of direct database/session logic inside models.
- Enforce business rules on the backend, not only through frontend domains or disabled controls.
- Keep role display names user-facing; keep technical role codes internal.
- Update `TransitOps_Module_Spec.md` phase status only when the phase scope is fully implemented and tested.

## Production Checklist

- Set a strong `SECRET_KEY`.
- Set `ENVIRONMENT=production`.
- Disable debug mode.
- Use production PostgreSQL credentials.
- Configure CORS for the production frontend domain.
- Configure HTTPS at the proxy/load balancer.
- Run migrations before serving traffic.
- Build and serve `frontend/dist`.
- Set up database backups.
- Review seeded admin credentials.

## License

Internal project unless a license is added.
