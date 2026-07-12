# AGENTS.md — TransitOps

Instructions for any coding agent (Codex, etc.) working in this repository.

---

## 0. Read Before Touching Any Code

Every session, in this exact order, before writing or editing a single line:

1. **`/docs`** — the framework guide. This explains how *our* framework (TypeScript + Vue + Python) expects models, roles, menus, and access rules to be wired up. It is the source of truth for **how** to build things (patterns, folder structure, conventions). Do not guess framework conventions — if `/docs` shows a pattern, use it exactly, even if you'd normally do it differently.
2. **`TransitOps_Module_Spec.md`** — the source of truth for **what** to build: models, fields, business rules, roles, menus, access matrix, and the phase plan. This is the product spec, not a suggestion — do not invent fields, statuses, or rules that aren't in it, and do not skip validations listed under a model's "Business logic / automations" section.

If `/docs` and the spec ever conflict on *implementation detail* (e.g. how a model file is structured), `/docs` wins. If they conflict on *business logic* (e.g. what a status transition should do), the spec wins. If genuinely ambiguous, stop and flag it rather than guessing.

---

## 1. Phase Discipline

The spec's **§8 Build Phases** table is the execution order. Rules:

- Work phases **strictly in order** (Phase 0 → 1 → 2 → ...). Do not start Phase 3 work while Phase 2 has unfinished or untested items, even if it looks faster to jump ahead.
- Before starting work in a session, open the Phase table and find the **first phase not marked ✅ Done**. That is the only phase you work on this session unless told otherwise.
- A phase's bullets are the literal scope. Don't add unlisted features to a phase, and don't quietly defer a listed item to "later" without flagging it.
- Bonus features (spec §9) are **out of scope** until all of Phase 0–6 are ✅.

### Updating status
- Mark a phase 🟨 In Progress as soon as you start it.
- Mark a phase ✅ Done **only** when every bullet in its scope is implemented **and** manually verified against the spec's business rules (not just "code compiles"). Partial completion stays 🟨.
- Update the Status column directly in `TransitOps_Module_Spec.md` — this file is the single progress tracker, don't create a separate progress log.
- When you mark a phase ✅, add a one-line note in the row (or immediately below the table) stating what was actually built, so the next session/human can verify quickly without re-reading all the code.

---

## 2. Business Rule Enforcement

These are graded/critical and must be enforced **server-side**, never only in the Vue UI:

- Vehicle registration number uniqueness
- Retired / In Shop vehicles never appear in dispatch dropdowns
- Suspended drivers or expired licenses never appear in dispatch dropdowns
- A vehicle/driver already `on_trip` cannot be assigned to a second trip
- Cargo weight ≤ vehicle max load capacity
- Dispatch/Complete/Cancel status transitions exactly as defined in spec §3.4
- Maintenance create → vehicle `in_shop`; maintenance close → vehicle `available` (unless retired)
- Login lockout after 5 failed attempts (spec §2.2)

Do not treat disabling a dropdown option in the UI as satisfying a rule — always add the matching backend constraint/check.

---

## 3. Access Control

Implement per the Access Matrix (spec §4) and Menu table (spec §5) exactly. In particular:
- `trip` is the only model scoped to "own records" for the Driver role — everything else is all-or-nothing per role.
- A menu with zero visible items for the current role must not render.
- Never let a role bypass its matrix via a different route (e.g. Driver hitting the Fuel Log API directly must be blocked server-side even though there's no Fuel Log menu item for Driver).

---

## 4. General Rules

- Don't refactor unrelated code while doing a phase's work — stay scoped.
- Don't rename, restructure, or introduce new architectural patterns not shown in `/docs`.
- If a spec requirement seems to conflict with something already in the codebase, flag it in your output rather than silently picking one.
- Keep commits/changes scoped to one phase at a time so progress is easy to review against the Status column.
