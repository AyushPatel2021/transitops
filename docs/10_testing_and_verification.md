# Testing And Verification

Every module should prove that it works at three levels:

1. backend model/ORM tests
2. frontend metadata contract tests when frontend behavior is affected
3. startup/build checks

## Backend Tests

Create tests under `backend/tests`.

Minimum coverage for each new model:

- create
- read/search
- write
- unlink/delete
- required fields
- relations
- role permissions
- object button methods
- sequence generation if used
- cron method if used

Run:

```bash
cd /home/erp/znova/znova_1.0
source ~/python3_venv/bin/activate && pytest -q backend/tests
```

## Frontend Tests

Frontend tests live next to the feature or composable:

```text
frontend/src/composables/useForm.framework.test.ts
frontend/src/components/form/BaseForm.framework.test.ts
```

Run:

```bash
cd /home/erp/znova/znova_1.0/frontend
npm test
```

Add frontend tests when:

- metadata rendering changes
- generic action handling changes
- breadcrumbs change
- relation fields change
- search/list behavior changes

Do not add frontend tests for backend-only business rules unless those rules affect frontend metadata rendering.

## Build

Run:

```bash
cd /home/erp/znova/znova_1.0/frontend
npm run build
```

This runs:

- `vue-tsc`
- `vite build`

Build warnings about chunk size are not automatically failures. Type errors are failures.

## Startup Smoke

A useful backend startup smoke test is:

```bash
cd /home/erp/znova/znova_1.0
source ~/python3_venv/bin/activate && python -m py_compile backend/main.py
```

For deeper startup verification, use FastAPI `TestClient` with a temporary database like the existing backend framework tests.

## Manual Checks

For a new module, manually verify:

- menu appears for the right role
- list page opens
- create form opens
- defaults are correct
- required fields show correctly
- record saves
- record opens after save
- search works
- filters work
- group-by works
- relation dropdowns load
- smart buttons hide/show correctly
- object buttons call backend methods
- delete works
- unauthorized role cannot modify records

## Before Marking A Module Done

Run all:

```bash
cd /home/erp/znova/znova_1.0
source ~/python3_venv/bin/activate && pytest -q backend/tests

cd /home/erp/znova/znova_1.0/frontend
npm test
npm run build
```

If a module needs a custom page, also open it in the browser and verify responsive layout.
