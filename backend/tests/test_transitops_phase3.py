from datetime import date

import pytest

import backend.models
from backend.core.base_model import Environment
from backend.core.database import Base
from backend.core.database import SessionLocal
from backend.core.database import engine
from backend.core.exceptions import UserError


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _seed_user(env):
    role = env["role"].create({
        "display_name": "Fleet Manager",
        "name": "fleet_manager",
        "description": "Fleet operations",
    })._records[0]
    timezone = env["timezone"].create({
        "name": "UTC",
        "display_name": "UTC",
        "offset": "+00:00",
    })._records[0]
    return env["user"].create({
        "full_name": "Fleet Manager",
        "email": "fleet@example.com",
        "hashed_password": "ValidPass1!",
        "role_id": role.id,
        "timezone_id": timezone.id,
    })._records[0]


def _seed_assets(env):
    region = env["region"].create({
        "name": "West Zone",
        "code": "WZ",
        "active": True,
    })._records[0]
    vehicle = env["vehicle"].create({
        "registration_number": "TR-300",
        "name_model": "Truck-300",
        "type": "Truck",
        "max_load_capacity": 1000.0,
        "odometer": 100.0,
        "acquisition_cost": 75000.0,
        "status": "available",
        "region_id": region.id,
    })._records[0]
    driver = env["driver"].create({
        "name": "Phase Three Driver",
        "license_number": "LIC-300",
        "license_category": "HMV",
        "license_expiry_date": date(2035, 1, 1),
        "contact_number": "7777777777",
        "safety_score": 98.0,
        "status": "available",
        "region_id": region.id,
    })._records[0]
    return vehicle, driver


def test_phase3_trip_dispatch_complete_cancel_and_validation(db):
    env = Environment(db)
    user = _seed_user(env)
    vehicle, driver = _seed_assets(env)

    with pytest.raises(UserError, match="Cargo weight cannot exceed"):
        env["trip"].create({
            "source": "Depot",
            "destination": "Overweight Hub",
            "vehicle_id": vehicle.id,
            "driver_id": driver.id,
            "cargo_weight": 1500.0,
            "planned_distance": 50.0,
            "created_by": user.id,
        })

    trip = env["trip"].create({
        "source": "Depot",
        "destination": "Central Hub",
        "vehicle_id": vehicle.id,
        "driver_id": driver.id,
        "cargo_weight": 750.0,
        "planned_distance": 80.0,
        "created_by": user.id,
    })._records[0]

    second_trip = env["trip"].create({
        "source": "Depot",
        "destination": "Second Hub",
        "vehicle_id": vehicle.id,
        "driver_id": driver.id,
        "cargo_weight": 500.0,
        "planned_distance": 40.0,
        "created_by": user.id,
    })._records[0]

    with pytest.raises(UserError, match="Trip status can only be changed"):
        trip.write({"status": "dispatched"})

    trip.action_dispatch()
    assert trip.status == "dispatched"
    assert trip.vehicle.status == "on_trip"
    assert trip.driver.status == "on_trip"
    assert trip.dispatched_at is not None

    with pytest.raises(UserError, match="Vehicle no longer available"):
        second_trip.action_dispatch()

    trip.write({
        "actual_distance": 82.0,
        "fuel_consumed": 18.5,
        "fuel_unit_cost": 4.25,
        "final_odometer": 182.0,
        "status": "dispatched",
    })
    assert trip.total_fuel_cost == 78.625
    trip.action_complete()

    assert trip.status == "completed"
    assert trip.vehicle.status == "available"
    assert trip.driver.status == "available"
    assert trip.vehicle.odometer == 182.0
    assert trip.completed_at is not None

    fuel_log = env["fuel.log"].search([("trip_id", "=", trip.id)], limit=1)
    assert fuel_log
    assert fuel_log.vehicle.id == vehicle.id
    assert fuel_log.liters == 18.5
    assert fuel_log.cost == 78.625
    assert fuel_log.odometer_reading == 182.0

    with pytest.raises(UserError, match="terminal"):
        trip.action_cancel()


def test_phase3_trip_created_by_auto_sets_from_action_user(db):
    env = Environment(db)
    user = _seed_user(env)
    vehicle, driver = _seed_assets(env)
    user_env = Environment(db, user_id=user.id)

    trip = user_env["trip"].create({
        "source": "Depot",
        "destination": "Auto Creator Hub",
        "vehicle_id": vehicle.id,
        "driver_id": driver.id,
        "cargo_weight": 500.0,
        "planned_distance": 40.0,
    })._records[0]
    assert trip.created_by.id == user.id

    metadata = type(trip).get_ui_metadata()
    assert metadata["fields"]["created_by"]["required"] is False
    assert metadata["fields"]["created_by"]["readonly"] is True
    assert metadata["fields"]["total_fuel_cost"]["compute"] == "_compute_total_fuel_cost"
    assert metadata["fields"]["total_fuel_cost"]["readonly"] is True
    completion_tab = next(tab for tab in metadata["views"]["form"]["tabs"] if tab["title"] == "Completion")
    assert completion_tab["groups"][1]["fields"] == ["fuel_consumed", "fuel_unit_cost", "total_fuel_cost"]
    audit_tab = next(tab for tab in metadata["views"]["form"]["tabs"] if tab["title"] == "Audit")
    assert audit_tab["groups"][0]["fields"] == ["created_by", "dispatched_at", "completed_at"]


def test_phase3_trip_cancel_from_draft_and_dispatched_restores_assets(db):
    env = Environment(db)
    user = _seed_user(env)
    vehicle, driver = _seed_assets(env)

    draft_trip = env["trip"].create({
        "source": "Depot",
        "destination": "Draft Cancel Hub",
        "vehicle_id": vehicle.id,
        "driver_id": driver.id,
        "cargo_weight": 300.0,
        "planned_distance": 25.0,
        "created_by": user.id,
    })._records[0]
    draft_trip.action_cancel()
    assert draft_trip.status == "cancelled"
    assert draft_trip.vehicle.status == "available"
    assert draft_trip.driver.status == "available"

    dispatched_trip = env["trip"].create({
        "source": "Depot",
        "destination": "Dispatch Cancel Hub",
        "vehicle_id": vehicle.id,
        "driver_id": driver.id,
        "cargo_weight": 300.0,
        "planned_distance": 25.0,
        "created_by": user.id,
    })._records[0]
    dispatched_trip.action_dispatch()
    assert dispatched_trip.vehicle.status == "on_trip"
    assert dispatched_trip.driver.status == "on_trip"

    dispatched_trip.action_cancel()
    assert dispatched_trip.status == "cancelled"
    assert dispatched_trip.vehicle.status == "available"
    assert dispatched_trip.driver.status == "available"
