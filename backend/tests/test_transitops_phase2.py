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


def test_phase2_region_vehicle_driver_crud_and_uniqueness(db):
    env = Environment(db)

    region = env["region"].create({
        "name": "West Zone",
        "code": "WZ",
        "active": True,
    })._records[0]
    assert env["region"].search([("code", "=", "WZ")]).name == "West Zone"

    with pytest.raises(UserError):
        env["region"].create({
            "name": "West Duplicate",
            "code": "WZ",
            "active": True,
        })

    vehicle = env["vehicle"].create({
        "registration_number": "TR-100",
        "name_model": "Van-100",
        "type": "Van",
        "max_load_capacity": 1200.0,
        "odometer": 10.0,
        "acquisition_cost": 50000.0,
        "status": "available",
        "region_id": region.id,
    })._records[0]
    assert vehicle.status == "available"
    assert vehicle.region.name == "West Zone"

    vehicle.write({"status": "retired"})
    assert env["vehicle"].browse(vehicle.id).status == "retired"

    with pytest.raises(UserError):
        env["vehicle"].create({
            "registration_number": "TR-100",
            "name_model": "Van-101",
            "type": "Van",
            "max_load_capacity": 900.0,
            "odometer": 0.0,
            "acquisition_cost": 45000.0,
            "status": "available",
        })

    driver = env["driver"].create({
        "name": "Riya Driver",
        "license_number": "LIC-100",
        "license_category": "HMV",
        "license_expiry_date": date(2030, 1, 1),
        "contact_number": "9999999999",
        "safety_score": 96.0,
        "status": "available",
        "region_id": region.id,
    })._records[0]
    driver_metadata = type(driver).get_ui_metadata()
    assert driver_metadata["fields"]["license_valid"]["type"] == "boolean"
    assert driver_metadata["fields"]["license_valid"]["compute"] == "_compute_license_valid"
    assert driver.license_valid is True
    assert driver.status == "available"

    driver.write({"status": "suspended"})
    assert env["driver"].browse(driver.id).status == "suspended"

    with pytest.raises(UserError):
        env["driver"].create({
            "name": "Duplicate Driver",
            "license_number": "LIC-100",
            "license_category": "HMV",
            "license_expiry_date": date(2030, 1, 1),
            "contact_number": "8888888888",
            "status": "available",
        })
