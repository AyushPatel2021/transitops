"""
Dashboard & Reports API endpoints for TransitOps.

All endpoints require authentication. Role-based data scoping is applied
inside the service layer, not in the route handlers.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.api.v1.endpoints.model_api import get_current_user
from backend.core.database import get_db
from backend.services.auth_service import get_current_user_from_jwt, validate_jwt_token
from backend.core.base_model import Environment
from backend.services.dashboard_service import (
    get_dashboard_data,
    get_fuel_efficiency_report,
    get_fleet_utilization_report,
    get_operational_cost_report,
    get_roi_report,
    rows_to_csv,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_user_from_token_param(token: Optional[str], db: Session):
    """Resolve a user from a ?token= query param (used for browser CSV downloads)."""
    if not token:
        return None
    try:
        claims = validate_jwt_token(token)
        env = Environment(db)
        user = env["user"].search([("email", "=", claims.get("email"))], limit=1)
        return user if user else None
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard/data")
def dashboard_data(
    period: str = Query("this_month", description="this_month | this_quarter | all_time | custom"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return role-specific KPIs and chart data for the dashboard."""
    try:
        data = get_dashboard_data(db, current_user, period, date_from, date_to)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Dashboard data error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "data": {"kpis": [], "charts": []}}


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@router.get("/reports/fuel-efficiency")
def fuel_efficiency_report(
    period: str = Query("all_time"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        data = get_fuel_efficiency_report(db, current_user, period, date_from, date_to, vehicle_type, region_id)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Fuel efficiency report error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "data": {"rows": [], "chart": None}}


@router.get("/reports/fuel-efficiency/csv")
def fuel_efficiency_csv(
    period: str = Query("all_time"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    user = _get_user_from_token_param(token, db)
    if not user:
        return Response(content="Unauthorized", status_code=401)
    data = get_fuel_efficiency_report(db, user, period, date_from, date_to, vehicle_type, region_id)
    csv_str = rows_to_csv(data["rows"], data["columns"])
    return Response(content=csv_str, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=fuel_efficiency.csv"})


@router.get("/reports/fleet-utilization")
def fleet_utilization_report(
    period: str = Query("all_time"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        data = get_fleet_utilization_report(db, current_user, period, date_from, date_to, vehicle_type, region_id)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Fleet utilization report error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "data": {"rows": [], "charts": []}}


@router.get("/reports/fleet-utilization/csv")
def fleet_utilization_csv(
    period: str = Query("all_time"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    user = _get_user_from_token_param(token, db)
    if not user:
        return Response(content="Unauthorized", status_code=401)
    data = get_fleet_utilization_report(db, user, period, date_from, date_to, vehicle_type, region_id)
    csv_str = rows_to_csv(data["rows"], data["columns"])
    return Response(content=csv_str, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=fleet_utilization.csv"})


@router.get("/reports/operational-cost")
def operational_cost_report(
    period: str = Query("all_time"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    vehicle_id: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        data = get_operational_cost_report(db, current_user, period, date_from, date_to, vehicle_id, region_id)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Operational cost report error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "data": {"rows": [], "charts": []}}


@router.get("/reports/operational-cost/csv")
def operational_cost_csv(
    period: str = Query("all_time"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    vehicle_id: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    user = _get_user_from_token_param(token, db)
    if not user:
        return Response(content="Unauthorized", status_code=401)
    data = get_operational_cost_report(db, user, period, date_from, date_to, vehicle_id, region_id)
    csv_str = rows_to_csv(data["rows"], data["columns"])
    return Response(content=csv_str, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=operational_cost.csv"})


@router.get("/reports/roi")
def roi_report(
    period: str = Query("all_time"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    vehicle_id: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        data = get_roi_report(db, current_user, period, date_from, date_to, vehicle_id, region_id)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"ROI report error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "data": {"rows": [], "chart": None}}


@router.get("/reports/roi/csv")
def roi_csv(
    period: str = Query("all_time"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    vehicle_id: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    user = _get_user_from_token_param(token, db)
    if not user:
        return Response(content="Unauthorized", status_code=401)
    data = get_roi_report(db, user, period, date_from, date_to, vehicle_id, region_id)
    csv_str = rows_to_csv(data["rows"], data["columns"])
    return Response(content=csv_str, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=roi_report.csv"})
