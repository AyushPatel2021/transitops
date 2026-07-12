# Architecture

Znova 1 is a metadata-driven ERP framework.

The backend owns business behavior:

- models and database schema
- field definitions
- relations
- validation
- security
- menu structure
- list/form layout metadata
- object buttons and client actions
- default values
- cron jobs
- sequences
- custom services and routes when truly needed

The frontend is generic:

- `/models/:model` shows a backend-defined list view.
- `/models/:model/:id` shows a backend-defined form view.
- `/models/:model/new` creates records using backend metadata and defaults.
- Header buttons and smart buttons are rendered from backend `_ui_views`.
- Search filters and group-by options come from backend `_search_config`.
- Breadcrumbs are route/menu/metadata driven.

For most modules, you should not create frontend files. Add frontend only for a genuinely custom page, such as a specialized comparison screen or visual dashboard that cannot be expressed as generic list/form metadata.

## Runtime Flow

1. The backend imports models from `backend/models`.
2. Model classes register themselves using `_model_name_`.
3. Field declarations create SQLAlchemy columns and UI metadata.
4. Generic APIs in `backend/api/v1/endpoints/model_api.py` expose CRUD, metadata, defaults, permissions, object method calls, comparison, and PDF report hooks.
5. The frontend requests metadata and data using those generic APIs.
6. The frontend renders list/form/action UI without module-specific code.

## Framework Rule

If you need to touch `frontend/src` for a normal model, list, form, field, button, breadcrumb, filter, or relation, stop first. The better fix is usually backend metadata or a generic framework enhancement.

If you need to touch `backend/core`, also stop first. A module should normally live in:

- `backend/models`
- `backend/data`
- `backend/demo`
- `backend/services`
- `backend/api/v1/endpoints` only for custom routes
- `backend/tests`

Core changes are for framework behavior that every future module benefits from.
