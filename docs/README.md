# Znova 1 Module Development Guide

This folder explains how to build a new business module on top of `znova_1.0`.

The goal is simple: a module should usually be backend-only. You define models, fields, permissions, menus, views, actions, data, sequences, and cron jobs in Python metadata. The existing frontend reads that metadata and renders generic list/form/search/action screens.

Use these files in order:

1. [01_architecture.md](01_architecture.md) - framework mental model.
2. [02_module_anatomy.md](02_module_anatomy.md) - where module files go.
3. [03_models_and_fields.md](03_models_and_fields.md) - how to define models, fields, relations, and methods.
4. [04_security_roles_permissions.md](04_security_roles_permissions.md) - roles, CRUD permissions, and domains.
5. [05_ui_metadata.md](05_ui_metadata.md) - list/form/tabs/buttons/search config.
6. [06_data_menus_demo.md](06_data_menus_demo.md) - menus, init records, demo records.
7. [07_actions_services_routes.md](07_actions_services_routes.md) - object actions, services, custom routes.
8. [08_sequences_crons.md](08_sequences_crons.md) - automatic numbers and scheduled jobs.
9. [09_frontend_contract.md](09_frontend_contract.md) - what the frontend expects and what not to hardcode.
10. [10_testing_and_verification.md](10_testing_and_verification.md) - backend/frontend checks before shipping.
11. [11_kinetic_style_example.md](11_kinetic_style_example.md) - how a Kinetic PLM-style app maps onto this framework.

Before building a new module, read `01` through `05`. Before shipping it, run through `10`.
