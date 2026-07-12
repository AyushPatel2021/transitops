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
        "email": "fleet-phase4@example.com",
        "hashed_password": "ValidPass1!",
        "role_id": role.id,
        "timezone_id": timezone.id,
    })._records[0]


def _seed_vehicle(env):
    region = env["region"].create({
        "name": "Phase Four Zone",
        "code": "P4",
        "active": True,
    })._records[0]
    return env["vehicle"].create({
        "registration_number": "TR-400",
        "name_model": "Truck-400",
        "type": "Truck",
        "max_load_capacity": 1400.0,
        "odometer": 400.0,
        "acquisition_cost": 90000.0,
        "status": "available",
        "region_id": region.id,
    })._records[0]


def test_phase4_maintenance_start_close_and_cost_rollup(db):
    env = Environment(db)
    user = _seed_user(env)
    vehicle = _seed_vehicle(env)
    user_env = Environment(db, user_id=user.id)

    maintenance = user_env["maintenance.log"].create({
        "vehicle_id": vehicle.id,
        "maintenance_type": "Engine",
        "description": "Phase 4 maintenance",
        "cost": 250.0,
        "start_date": date(2026, 7, 12),
    })._records[0]

    assert maintenance.created_by.id == user.id
    assert maintenance.status == "active"
    assert maintenance.vehicle.status == "in_shop"

    with pytest.raises(UserError, match="one active maintenance"):
        user_env["maintenance.log"].create({
            "vehicle_id": vehicle.id,
            "maintenance_type": "Brake",
            "cost": 80.0,
            "start_date": date(2026, 7, 13),
        })

    with pytest.raises(UserError, match="only be changed through Close Maintenance"):
        maintenance.write({"status": "closed"})

    with pytest.raises(UserError, match="End date is required"):
        maintenance.action_close()

    maintenance.write({"end_date": date(2026, 7, 14)})
    maintenance.action_close()

    assert maintenance.status == "closed"
    assert maintenance.vehicle.status == "available"

    env["fuel.log"].create({
        "vehicle_id": vehicle.id,
        "liters": 20.0,
        "cost": 75.0,
        "date": date(2026, 7, 15),
        "odometer_reading": 420.0,
    })
    env["expense"].create({
        "vehicle_id": vehicle.id,
        "expense_type": "Toll",
        "amount": 35.0,
        "date": date(2026, 7, 15),
    })

    assert vehicle.total_operational_cost == 325.0
    vehicle_dict = vehicle.to_dict(fields=["total_operational_cost"])
    assert vehicle_dict["total_operational_cost"] == 325.0


def test_phase4_maintenance_close_does_not_unretire_vehicle(db):
    env = Environment(db)
    user = _seed_user(env)
    vehicle = _seed_vehicle(env)
    user_env = Environment(db, user_id=user.id)

    maintenance = user_env["maintenance.log"].create({
        "vehicle_id": vehicle.id,
        "maintenance_type": "Body",
        "cost": 120.0,
        "start_date": date(2026, 7, 12),
    })._records[0]

    vehicle.write({"status": "retired"})
    maintenance.write({"end_date": date(2026, 7, 14)})
    maintenance.action_close()

    assert maintenance.status == "closed"
    assert maintenance.vehicle.status == "retired"


def test_phase4_finance_values_cannot_be_negative(db):
    env = Environment(db)
    vehicle = _seed_vehicle(env)

    with pytest.raises(UserError, match="Fuel liters cannot be negative"):
        env["fuel.log"].create({
            "vehicle_id": vehicle.id,
            "liters": -1.0,
            "cost": 10.0,
            "date": date(2026, 7, 15),
        })

    with pytest.raises(UserError, match="Fuel cost cannot be negative"):
        env["fuel.log"].create({
            "vehicle_id": vehicle.id,
            "liters": 10.0,
            "cost": -5.0,
            "date": date(2026, 7, 15),
        })

    with pytest.raises(UserError, match="Expense amount cannot be negative"):
        env["expense"].create({
            "vehicle_id": vehicle.id,
            "expense_type": "Fine",
            "amount": -25.0,
            "date": date(2026, 7, 15),
        })
