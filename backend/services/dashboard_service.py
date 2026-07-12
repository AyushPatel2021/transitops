"""
Dashboard & Reports service for TransitOps.

All queries are scoped by the caller's role — the API endpoint passes
`current_user` and this service enforces access rules.

Date range helper accepts:
    period: "this_month" | "this_quarter" | "all_time" | "custom"
    date_from: ISO date string  (required for "custom")
    date_to:   ISO date string  (required for "custom")
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Date range helper
# ---------------------------------------------------------------------------

def _parse_date_range(period: str, date_from: Optional[str], date_to: Optional[str]):
    today = date.today()

    if period == "this_month":
        start = today.replace(day=1)
        end = today
    elif period == "this_quarter":
        q_start_month = ((today.month - 1) // 3) * 3 + 1
        start = today.replace(month=q_start_month, day=1)
        end = today
    elif period == "custom" and date_from and date_to:
        start = date.fromisoformat(date_from)
        end = date.fromisoformat(date_to)
    else:  # all_time
        start = date(2000, 1, 1)
        end = today

    return start, end


# ---------------------------------------------------------------------------
# DASHBOARD DATA
# ---------------------------------------------------------------------------

def get_dashboard_data(db: Session, user, period: str = "this_month",
                        date_from: Optional[str] = None, date_to: Optional[str] = None) -> dict:
    """Return role-specific dashboard KPIs and chart data."""
    from backend.core.base_model import Environment

    env = Environment(db)
    role = user.role.name if user.role else None
    start, end = _parse_date_range(period, date_from, date_to)

    if role in ("admin", "fleet_manager"):
        return _fleet_dashboard(env, start, end, user, role)
    elif role == "driver":
        return _driver_dashboard(env, start, end, user)
    elif role == "safety_officer":
        return _safety_dashboard(env, start, end)
    elif role == "financial_analyst":
        return _finance_dashboard(env, start, end)
    else:
        return {"kpis": [], "charts": []}


def _fleet_dashboard(env, start: date, end: date, user, role: str) -> dict:
    all_vehicles = env["vehicle"].search([])
    active_vehicles = [v for v in all_vehicles if v.status != "retired"]
    available = [v for v in all_vehicles if v.status == "available"]
    in_shop = [v for v in all_vehicles if v.status == "in_shop"]
    on_trip = [v for v in all_vehicles if v.status == "on_trip"]
    retired = [v for v in all_vehicles if v.status == "retired"]

    all_trips = env["trip"].search([])
    active_trips = [t for t in all_trips if t.status == "dispatched"]
    pending_trips = [t for t in all_trips if t.status == "draft"]
    all_drivers = env["driver"].search([])
    drivers_on_duty = [d for d in all_drivers if d.status == "on_trip"]

    utilization_pct = round(len(on_trip) / len(active_vehicles) * 100, 1) if active_vehicles else 0

    kpis = [
        {"key": "active_vehicles", "label": "Active Vehicles", "value": len(active_vehicles), "icon": "BusFront"},
        {"key": "available_vehicles", "label": "Available Vehicles", "value": len(available), "icon": "CheckCircle"},
        {"key": "in_maintenance", "label": "In Maintenance", "value": len(in_shop), "icon": "Wrench"},
        {"key": "active_trips", "label": "Active Trips", "value": len(active_trips), "icon": "Route"},
        {"key": "pending_trips", "label": "Pending Trips", "value": len(pending_trips), "icon": "Clock"},
        {"key": "drivers_on_duty", "label": "Drivers On Duty", "value": len(drivers_on_duty), "icon": "UserRoundCheck"},
        {"key": "utilization", "label": "Fleet Utilization %", "value": utilization_pct, "icon": "Activity", "suffix": "%"},
    ]

    # Vehicle status donut
    status_donut = {
        "type": "donut",
        "title": "Vehicle Status",
        "labels": ["Available", "On Trip", "In Shop", "Retired"],
        "data": [len(available), len(on_trip), len(in_shop), len(retired)],
        "colors": ["success", "warning", "danger", "muted"],
    }

    # Trip volume line (day by day in range)
    trip_line = _trip_volume_chart(env, start, end)

    # Utilization by region bar
    util_bar = _utilization_by_region_chart(env)

    return {"kpis": kpis, "charts": [status_donut, trip_line, util_bar]}


def _driver_dashboard(env, start: date, end: date, user) -> dict:
    driver_records = env["driver"].search([("user_id", "=", user.id)])
    driver_id = driver_records[0].id if driver_records else None

    base_domain = ["|", ("created_by", "=", user.id)]
    if driver_id:
        base_domain.append(("driver_id", "=", driver_id))

    my_trips = env["trip"].search(base_domain)
    active = [t for t in my_trips if t.status == "dispatched"]
    pending = [t for t in my_trips if t.status == "draft"]

    completed_in_period = [
        t for t in my_trips
        if t.status == "completed"
        and t.completed_at
        and start <= (t.completed_at.date() if isinstance(t.completed_at, datetime) else t.completed_at) <= end
    ]

    # Current vehicle
    current_vehicle_status = "—"
    if driver_records and driver_id:
        active_trip = next((t for t in my_trips if t.status == "dispatched"), None)
        if active_trip and active_trip.vehicle:
            current_vehicle_status = active_trip.vehicle.registration_number

    kpis = [
        {"key": "my_active_trips", "label": "My Active Trips", "value": len(active), "icon": "Route"},
        {"key": "my_pending_trips", "label": "My Pending Trips", "value": len(pending), "icon": "Clock"},
        {"key": "completed_period", "label": "Completed This Period", "value": len(completed_in_period), "icon": "CheckCircle"},
        {"key": "current_vehicle", "label": "Current Vehicle", "value": current_vehicle_status, "icon": "BusFront", "is_text": True},
    ]

    trip_line = _trip_volume_chart(env, start, end, driver_trips=my_trips)

    return {"kpis": kpis, "charts": [trip_line]}


def _safety_dashboard(env, start: date, end: date) -> dict:
    all_drivers = env["driver"].search([])
    on_duty = [d for d in all_drivers if d.status == "on_trip"]
    suspended = [d for d in all_drivers if d.status == "suspended"]

    today = date.today()
    in_30 = today + timedelta(days=30)
    expiring = [
        d for d in all_drivers
        if d.license_expiry_date and today <= d.license_expiry_date <= in_30
    ]
    expiring_sorted = sorted(expiring, key=lambda d: d.license_expiry_date)

    avg_score = round(
        sum(d.safety_score or 0 for d in all_drivers) / len(all_drivers), 1
    ) if all_drivers else 0

    kpis = [
        {"key": "drivers_on_duty", "label": "Drivers On Duty", "value": len(on_duty), "icon": "UserRoundCheck"},
        {"key": "suspended", "label": "Suspended Drivers", "value": len(suspended), "icon": "ShieldAlert"},
        {"key": "expiring_licenses", "label": "Licenses Expiring (30d)", "value": len(expiring), "icon": "CalendarAlert"},
        {"key": "avg_safety_score", "label": "Avg Safety Score", "value": avg_score, "icon": "Shield", "suffix": "/100"},
    ]

    # Safety score bar (buckets)
    buckets = {"90-100": 0, "70-89": 0, "Below 70": 0}
    for d in all_drivers:
        s = d.safety_score or 0
        if s >= 90:
            buckets["90-100"] += 1
        elif s >= 70:
            buckets["70-89"] += 1
        else:
            buckets["Below 70"] += 1

    score_bar = {
        "type": "bar",
        "title": "Safety Score Distribution",
        "labels": list(buckets.keys()),
        "data": list(buckets.values()),
        "colors": ["success", "warning", "danger"],
    }

    expiring_table = {
        "type": "table",
        "title": "Drivers with License Expiring Soon",
        "columns": ["Driver", "License #", "Expiry Date", "Status"],
        "rows": [
            [d.name, d.license_number, str(d.license_expiry_date), d.status]
            for d in expiring_sorted
        ],
    }

    return {"kpis": kpis, "charts": [score_bar, expiring_table]}


def _finance_dashboard(env, start: date, end: date) -> dict:
    # Fuel logs in period
    fuel_logs = env["fuel.log"].search([])
    fuel_in_period = [
        f for f in fuel_logs
        if f.date and start <= (f.date if isinstance(f.date, date) else f.date.date()) <= end
    ]
    total_fuel_cost = sum(f.cost or 0 for f in fuel_in_period)

    # Maintenance in period
    maint_logs = env["maintenance.log"].search([])
    maint_in_period = [
        m for m in maint_logs
        if m.start_date and start <= (m.start_date if isinstance(m.start_date, date) else m.start_date.date()) <= end
    ]
    total_maint_cost = sum(m.cost or 0 for m in maint_in_period)

    # Other expenses in period
    expenses = env["expense"].search([])
    exp_in_period = [
        e for e in expenses
        if e.date and start <= (e.date if isinstance(e.date, date) else e.date.date()) <= end
    ]
    total_expenses = sum(e.amount or 0 for e in exp_in_period)
    total_op_cost = total_fuel_cost + total_maint_cost + total_expenses

    kpis = [
        {"key": "total_op_cost", "label": "Total Operational Cost", "value": round(total_op_cost, 2), "icon": "TrendingUp", "prefix": "₹"},
        {"key": "fuel_cost", "label": "Total Fuel Cost", "value": round(total_fuel_cost, 2), "icon": "Fuel", "prefix": "₹"},
        {"key": "maintenance_cost", "label": "Maintenance Cost", "value": round(total_maint_cost, 2), "icon": "Wrench", "prefix": "₹"},
        {"key": "other_expenses", "label": "Other Expenses", "value": round(total_expenses, 2), "icon": "ReceiptText", "prefix": "₹"},
    ]

    # Cost breakdown pie
    pie = {
        "type": "pie",
        "title": "Cost Breakdown",
        "labels": ["Fuel", "Maintenance", "Expenses"],
        "data": [round(total_fuel_cost, 2), round(total_maint_cost, 2), round(total_expenses, 2)],
        "colors": ["info", "warning", "danger"],
    }

    # Cost trend line (weekly buckets)
    cost_line = _cost_trend_chart(fuel_logs, maint_logs, expenses, start, end)

    # Top 5 vehicles by operational cost bar
    top5_bar = _top5_vehicles_cost_chart(env)

    return {"kpis": kpis, "charts": [pie, cost_line, top5_bar]}


# ---------------------------------------------------------------------------
# SHARED CHART HELPERS
# ---------------------------------------------------------------------------

def _trip_volume_chart(env, start: date, end: date, driver_trips=None) -> dict:
    """Line chart: trips per day/week bucketed by created_at (always populated)."""
    if driver_trips is None:
        all_trips = env["trip"].search([])
    else:
        all_trips = driver_trips

    def _trip_date(t):
        for attr in ("created_at", "completed_at", "dispatched_at"):
            val = getattr(t, attr, None)
            if val:
                return val.date() if isinstance(val, datetime) else val
        return None

    trip_dates = [_trip_date(t) for t in all_trips]
    
    if start == date(2000, 1, 1):
        valid_dates = [d for d in trip_dates if d]
        if valid_dates:
            start = min(valid_dates)
        else:
            start = end - timedelta(days=365)

    delta = (end - start).days + 1
    labels = []
    data = []

    if delta <= 31:
        # Daily
        cursor = start
        while cursor <= end:
            count = sum(1 for t in all_trips if _trip_date(t) == cursor)
            labels.append(cursor.strftime("%b %d"))
            data.append(count)
            cursor += timedelta(days=1)
    elif delta <= 92:
        # Weekly
        cursor = start
        while cursor <= end:
            bucket_end = min(cursor + timedelta(days=6), end)
            count = sum(1 for t in all_trips if (td := _trip_date(t)) and cursor <= td <= bucket_end)
            label = cursor.strftime("%b %d") if cursor.year == end.year else cursor.strftime("%b %d, %Y")
            labels.append(label)
            data.append(count)
            cursor += timedelta(days=7)
    else:
        # Monthly
        cursor = start.replace(day=1)
        while cursor <= end:
            if cursor.month == 12:
                next_cursor = cursor.replace(year=cursor.year + 1, month=1)
            else:
                next_cursor = cursor.replace(month=cursor.month + 1)
            bucket_end = min(next_cursor - timedelta(days=1), end)
            count = sum(1 for t in all_trips if (td := _trip_date(t)) and cursor <= td <= bucket_end)
            labels.append(cursor.strftime("%b %Y"))
            data.append(count)
            cursor = next_cursor

    return {
        "type": "bar",
        "title": "Trip Volume",
        "labels": labels,
        "data": data,
        "colors": ["primary"],
    }


def _utilization_by_region_chart(env) -> dict:
    regions = env["region"].search([])
    labels = []
    data = []
    for r in regions:
        vehicles = env["vehicle"].search([("region_id", "=", r.id)])
        active = [v for v in vehicles if v.status != "retired"]
        on_trip = [v for v in vehicles if v.status == "on_trip"]
        pct = round(len(on_trip) / len(active) * 100, 1) if active else 0
        labels.append(r.name)
        data.append(pct)

    return {
        "type": "bar",
        "title": "Fleet Utilization by Region (%)",
        "labels": labels,
        "data": data,
        "colors": ["primary"],
    }


def _cost_trend_chart(fuel_logs, maint_logs, expenses, start: date, end: date) -> dict:
    """Bar chart: total cost trend."""
    all_dates = []
    for f in fuel_logs:
        if f.date:
            all_dates.append(f.date if isinstance(f.date, date) else f.date.date())
    for m in maint_logs:
        if m.start_date:
            all_dates.append(m.start_date if isinstance(m.start_date, date) else m.start_date.date())
    for e in expenses:
        if e.date:
            all_dates.append(e.date if isinstance(e.date, date) else e.date.date())

    if start == date(2000, 1, 1):
        valid_dates = [d for d in all_dates if d]
        if valid_dates:
            start = min(valid_dates)
        else:
            start = end - timedelta(days=365)

    delta = (end - start).days + 1
    labels = []
    data = []

    if delta <= 31:
        # Daily
        cursor = start
        while cursor <= end:
            fuel = sum(f.cost or 0 for f in fuel_logs if f.date and (f.date if isinstance(f.date, date) else f.date.date()) == cursor)
            maint = sum(m.cost or 0 for m in maint_logs if m.start_date and (m.start_date if isinstance(m.start_date, date) else m.start_date.date()) == cursor)
            exp = sum(e.amount or 0 for e in expenses if e.date and (e.date if isinstance(e.date, date) else e.date.date()) == cursor)
            labels.append(cursor.strftime("%b %d"))
            data.append(round(fuel + maint + exp, 2))
            cursor += timedelta(days=1)
    elif delta <= 92:
        # Weekly
        cursor = start
        while cursor <= end:
            bucket_end = min(cursor + timedelta(days=6), end)
            fuel = sum(f.cost or 0 for f in fuel_logs if f.date and cursor <= (f.date if isinstance(f.date, date) else f.date.date()) <= bucket_end)
            maint = sum(m.cost or 0 for m in maint_logs if m.start_date and cursor <= (m.start_date if isinstance(m.start_date, date) else m.start_date.date()) <= bucket_end)
            exp = sum(e.amount or 0 for e in expenses if e.date and cursor <= (e.date if isinstance(e.date, date) else e.date.date()) <= bucket_end)
            label = cursor.strftime("%b %d") if cursor.year == end.year else cursor.strftime("%b %d, %Y")
            labels.append(label)
            data.append(round(fuel + maint + exp, 2))
            cursor += timedelta(days=7)
    else:
        # Monthly
        cursor = start.replace(day=1)
        while cursor <= end:
            if cursor.month == 12:
                next_cursor = cursor.replace(year=cursor.year + 1, month=1)
            else:
                next_cursor = cursor.replace(month=cursor.month + 1)
            bucket_end = min(next_cursor - timedelta(days=1), end)
            fuel = sum(f.cost or 0 for f in fuel_logs if f.date and cursor <= (f.date if isinstance(f.date, date) else f.date.date()) <= bucket_end)
            maint = sum(m.cost or 0 for m in maint_logs if m.start_date and cursor <= (m.start_date if isinstance(m.start_date, date) else m.start_date.date()) <= bucket_end)
            exp = sum(e.amount or 0 for e in expenses if e.date and cursor <= (e.date if isinstance(e.date, date) else e.date.date()) <= bucket_end)
            labels.append(cursor.strftime("%b %Y"))
            data.append(round(fuel + maint + exp, 2))
            cursor = next_cursor

    return {
        "type": "bar",
        "title": "Operational Cost Trend",
        "labels": labels,
        "data": data,
        "colors": ["danger"],
    }


def _top5_vehicles_cost_chart(env) -> dict:
    vehicles = env["vehicle"].search([])
    costs = []
    for v in vehicles:
        fuel = sum(f.cost or 0 for f in env["fuel.log"].search([("vehicle_id", "=", v.id)]))
        maint = sum(m.cost or 0 for m in env["maintenance.log"].search([("vehicle_id", "=", v.id)]))
        costs.append((v.registration_number, fuel + maint))

    costs.sort(key=lambda x: x[1], reverse=True)
    top5 = costs[:5]

    return {
        "type": "bar",
        "title": "Top 5 Vehicles by Operational Cost",
        "labels": [c[0] for c in top5],
        "data": [round(c[1], 2) for c in top5],
        "colors": ["danger"],
    }


# ---------------------------------------------------------------------------
# REPORT DATA
# ---------------------------------------------------------------------------

def get_fuel_efficiency_report(db: Session, user, period: str = "all_time",
                                date_from=None, date_to=None,
                                vehicle_type=None, region_id=None) -> dict:
    from backend.core.base_model import Environment
    env = Environment(db)
    start, end = _parse_date_range(period, date_from, date_to)

    vehicles = env["vehicle"].search([])
    if vehicle_type:
        vehicles = [v for v in vehicles if v.type == vehicle_type]
    if region_id:
        vehicles = [v for v in vehicles if v.region_id == int(region_id)]

    rows = []
    for v in vehicles:
        # Use fuel_log for fuel data (always populated in demo)
        fuel_logs = env["fuel.log"].search([("vehicle_id", "=", v.id)])
        fuel_in_period = [
            f for f in fuel_logs
            if f.date and start <= (f.date if isinstance(f.date, date) else f.date.date()) <= end
        ]
        total_fuel = sum(f.liters or 0 for f in fuel_in_period)

        # For distance: prefer actual_distance from completed trips, fall back to planned_distance
        trips = env["trip"].search([
            ("vehicle_id", "=", v.id), ("status", "=", "completed")
        ])
        total_distance = sum(
            (t.actual_distance or t.planned_distance or 0) for t in trips
        )

        efficiency = round(total_distance / total_fuel, 2) if total_fuel else 0
        if not trips:
            efficiency = "No trip data"
        rows.append({
            "vehicle": v.registration_number,
            "type": v.type,
            "region": v.region.name if v.region else "—",
            "distance_km": round(total_distance, 1),
            "fuel_liters": round(total_fuel, 1),
            "efficiency_km_per_l": efficiency,
        })

    # Sort so that numeric efficiencies are ordered descending, and string values are at the bottom
    rows.sort(
        key=lambda r: (
            0 if isinstance(r["efficiency_km_per_l"], str) else 1,
            0 if isinstance(r["efficiency_km_per_l"], str) else r["efficiency_km_per_l"]
        ),
        reverse=True
    )
    # Only show vehicles with some data and numeric efficiency for the chart
    chart_rows = [r for r in rows if isinstance(r["efficiency_km_per_l"], (int, float)) and (r["fuel_liters"] > 0 or r["distance_km"] > 0)] or rows

    chart = {
        "type": "bar",
        "title": "Fuel Efficiency by Vehicle (km/L)",
        "labels": [r["vehicle"] for r in chart_rows],
        "data": [(r["efficiency_km_per_l"] if isinstance(r["efficiency_km_per_l"], (int, float)) else 0) for r in chart_rows],
        "colors": ["success"],
    }

    return {"rows": rows, "chart": chart, "columns": ["vehicle", "type", "region", "distance_km", "fuel_liters", "efficiency_km_per_l"]}


def get_fleet_utilization_report(db: Session, user, period: str = "all_time",
                                  date_from=None, date_to=None,
                                  vehicle_type=None, region_id=None) -> dict:
    from backend.core.base_model import Environment
    env = Environment(db)
    start, end = _parse_date_range(period, date_from, date_to)

    vehicles = env["vehicle"].search([])
    if vehicle_type:
        vehicles = [v for v in vehicles if v.type == vehicle_type]
    if region_id:
        vehicles = [v for v in vehicles if v.region_id == int(region_id)]

    active = [v for v in vehicles if v.status != "retired"]
    on_trip = [v for v in vehicles if v.status == "on_trip"]
    fleet_util = round(len(on_trip) / len(active) * 100, 1) if active else 0

    rows = []
    for v in vehicles:
        is_active = v.status != "retired"
        is_on_trip = v.status == "on_trip"
        rows.append({
            "vehicle": v.registration_number,
            "type": v.type,
            "region": v.region.name if v.region else "—",
            "status": v.status,
            "utilization_pct": 100.0 if is_on_trip else (0.0 if not is_active else 0.0),
        })

    # Utilization by region
    regions = env["region"].search([])
    region_rows = []
    region_labels = []
    region_data = []
    for r in regions:
        rvs = [v for v in vehicles if v.region and v.region.id == r.id]
        ra = [v for v in rvs if v.status != "retired"]
        rot = [v for v in rvs if v.status == "on_trip"]
        pct = round(len(rot) / len(ra) * 100, 1) if ra else 0
        region_labels.append(r.name)
        region_data.append(pct)

    trend = _trip_volume_chart(env, start, end)

    bar_chart = {
        "type": "bar",
        "title": "Fleet Utilization by Region (%)",
        "labels": region_labels,
        "data": region_data,
        "colors": ["primary"],
    }

    return {
        "rows": rows,
        "fleet_utilization_pct": fleet_util,
        "charts": [trend, bar_chart],
        "columns": ["vehicle", "type", "region", "status", "utilization_pct"],
    }


def get_operational_cost_report(db: Session, user, period: str = "all_time",
                                 date_from=None, date_to=None,
                                 vehicle_id=None, region_id=None) -> dict:
    from backend.core.base_model import Environment
    env = Environment(db)
    start, end = _parse_date_range(period, date_from, date_to)

    vehicles = env["vehicle"].search([])
    if vehicle_id:
        vehicles = [v for v in vehicles if v.id == int(vehicle_id)]
    if region_id:
        vehicles = [v for v in vehicles if v.region_id == int(region_id)]

    rows = []
    total_fuel_all = 0
    total_maint_all = 0
    for v in vehicles:
        fuel_logs = env["fuel.log"].search([("vehicle_id", "=", v.id)])
        fuel_in = [
            f for f in fuel_logs
            if f.date and start <= (f.date if isinstance(f.date, date) else f.date.date()) <= end
        ]
        maint_logs = env["maintenance.log"].search([("vehicle_id", "=", v.id)])
        maint_in = [
            m for m in maint_logs
            if m.start_date and start <= (m.start_date if isinstance(m.start_date, date) else m.start_date.date()) <= end
        ]
        fuel_cost = sum(f.cost or 0 for f in fuel_in)
        maint_cost = sum(m.cost or 0 for m in maint_in)
        total_fuel_all += fuel_cost
        total_maint_all += maint_cost
        rows.append({
            "vehicle": v.registration_number,
            "type": v.type,
            "region": v.region.name if v.region else "—",
            "fuel_cost": round(fuel_cost, 2),
            "maintenance_cost": round(maint_cost, 2),
            "total_cost": round(fuel_cost + maint_cost, 2),
        })

    rows.sort(key=lambda r: r["total_cost"], reverse=True)

    stacked_bar = {
        "type": "stacked_bar",
        "title": "Operational Cost per Vehicle",
        "labels": [r["vehicle"] for r in rows],
        "datasets": [
            {"label": "Fuel", "data": [r["fuel_cost"] for r in rows], "color": "info"},
            {"label": "Maintenance", "data": [r["maintenance_cost"] for r in rows], "color": "warning"},
        ],
    }
    pie = {
        "type": "pie",
        "title": "Total Cost Split",
        "labels": ["Fuel", "Maintenance"],
        "data": [round(total_fuel_all, 2), round(total_maint_all, 2)],
        "colors": ["info", "warning"],
    }

    return {"rows": rows, "charts": [stacked_bar, pie], "columns": ["vehicle", "type", "region", "fuel_cost", "maintenance_cost", "total_cost"]}


def get_roi_report(db: Session, user, period: str = "all_time",
                   date_from=None, date_to=None,
                   vehicle_id=None, region_id=None) -> dict:
    """
    ROI = (Revenue - (Fuel + Maintenance)) / Acquisition Cost
    Revenue is assumed 0 (trip.revenue field doesn't exist yet in the model).
    This placeholder returns 0 revenue per vehicle but the formula/table are
    fully wired so adding a revenue field to trip later will light it up.
    """
    from backend.core.base_model import Environment
    env = Environment(db)
    start, end = _parse_date_range(period, date_from, date_to)

    vehicles = env["vehicle"].search([])
    if vehicle_id:
        vehicles = [v for v in vehicles if v.id == int(vehicle_id)]
    if region_id:
        vehicles = [v for v in vehicles if v.region_id == int(region_id)]

    rows = []
    for v in vehicles:
        fuel_logs = env["fuel.log"].search([("vehicle_id", "=", v.id)])
        fuel_cost = sum(
            f.cost or 0 for f in fuel_logs
            if f.date and start <= (f.date if isinstance(f.date, date) else f.date.date()) <= end
        )
        maint_logs = env["maintenance.log"].search([("vehicle_id", "=", v.id)])
        maint_cost = sum(
            m.cost or 0 for m in maint_logs
            if m.start_date and start <= (m.start_date if isinstance(m.start_date, date) else m.start_date.date()) <= end
        )
        # Revenue: use getattr so adding trip.revenue later works automatically
        trips = env["trip"].search([("vehicle_id", "=", v.id), ("status", "=", "completed")])
        revenue = sum(getattr(t, "revenue", 0) or 0 for t in trips)

        acq = v.acquisition_cost or 1  # avoid div-by-zero
        total_cost = fuel_cost + maint_cost
        roi_pct = round((revenue - total_cost) / acq * 100, 2) if acq else 0

        rows.append({
            "vehicle": v.registration_number,
            "type": v.type,
            "region": v.region.name if v.region else "—",
            "revenue": round(revenue, 2),
            "fuel_cost": round(fuel_cost, 2),
            "maintenance_cost": round(maint_cost, 2),
            "acquisition_cost": round(acq, 2),
            "roi_pct": roi_pct,
        })

    rows.sort(key=lambda r: r["roi_pct"], reverse=True)

    roi_bar = {
        "type": "bar",
        "title": "ROI by Vehicle (%)",
        "labels": [r["vehicle"] for r in rows],
        "data": [r["roi_pct"] for r in rows],
        "colors": ["dynamic_roi"],  # frontend maps this to green/red per bar
    }

    return {"rows": rows, "chart": roi_bar, "columns": ["vehicle", "type", "region", "revenue", "fuel_cost", "maintenance_cost", "acquisition_cost", "roi_pct"]}


# ---------------------------------------------------------------------------
# CSV EXPORT
# ---------------------------------------------------------------------------

def rows_to_csv(rows: list, columns: list) -> str:
    """Convert report rows dict-list to a CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({col: row.get(col, "") for col in columns})
    return output.getvalue()
