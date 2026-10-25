"""
Database seed script providing demo fleets, drivers, geofences, and coordinates.
"""
from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.user import Organization, User
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.gps_device import GPSDevice
from app.models.gps_telemetry import GPSTelemetry
from app.models.geofence import Geofence
from app.models.alert import Alert

def seed_database():
    """Populate database with sample fleet data if empty."""
    if User.query.first():
        print("[*] Database already contains data. Skipping seed.")
        return

    print("[*] Seeding initial Transport GPS Tracking fleet data...")

    # 1. Create Organization
    org = Organization(
        name="Swift Transport Logistics",
        contact_email="support@swifttransport.com",
        contact_phone="+91-98765-43210"
    )
    db.session.add(org)
    db.session.flush()

    # 2. Create Default Admin User
    admin = User(
        organization_id=org.id,
        email="admin@swifttransport.com",
        first_name="Rohan",
        last_name="FleetManager",
        role="admin"
    )
    admin.set_password("Admin@12345")
    db.session.add(admin)

    # 3. Create Drivers
    driver1 = Driver(
        organization_id=org.id,
        first_name="Rajesh",
        last_name="Kumar",
        license_number="DL-0420110023451",
        phone_number="+91-98200-11223",
        safety_score=94.5,
        status="available"
    )
    driver2 = Driver(
        organization_id=org.id,
        first_name="Amit",
        last_name="Sharma",
        license_number="MH-1220150098761",
        phone_number="+91-98200-44556",
        safety_score=88.0,
        status="available"
    )
    db.session.add_all([driver1, driver2])
    db.session.flush()

    # 4. Create Vehicles
    veh1 = Vehicle(
        organization_id=org.id,
        assigned_driver_id=driver1.id,
        registration_number="MH-12-RN-4501",
        vin="MAT428123XYZ999",
        make="Tata",
        model="Prima 4028.S",
        year=2023,
        fuel_type="diesel",
        fuel_capacity_litres=400,
        status="active",
        current_odometer_km=48200.5
    )
    veh2 = Vehicle(
        organization_id=org.id,
        assigned_driver_id=driver2.id,
        registration_number="MH-04-AX-8912",
        vin="BBNZ2823R2024001",
        make="BharatBenz",
        model="2823R",
        year=2024,
        fuel_type="diesel",
        fuel_capacity_litres=380,
        status="active",
        current_odometer_km=18450.0
    )
    db.session.add_all([veh1, veh2])
    db.session.flush()

    dev1 = GPSDevice(vehicle_id=veh1.id, imei="864201048821931", model="Teltonika FMB920")
    dev2 = GPSDevice(vehicle_id=veh2.id, imei="864201048899881", model="Concox AT4")
    db.session.add_all([dev1, dev2])

    # 5. Create Geofences
    fence1 = Geofence(
        organization_id=org.id,
        name="Bhiwandi Logistics Hub",
        fence_type="circle",
        center_latitude=19.2965,
        center_longitude=73.0631,
        radius_meters=1500,
        alert_on_entry=True,
        alert_on_exit=True,
        color_hex="#3B82F6"
    )
    db.session.add(fence1)

    # 6. Create Historical Telemetry Points (Mumbai - Pune Highway track)
    now = datetime.now(timezone.utc)
    coords = [
        (19.0760, 72.8777, 55.0, 140),
        (19.0820, 72.8850, 62.4, 138),
        (19.0910, 72.8940, 84.2, 135), # Overspeed
        (19.1000, 72.9050, 72.0, 130),
    ]
    for idx, (lat, lng, spd, hdg) in enumerate(coords):
        t_time = now - timedelta(minutes=(len(coords) - idx) * 5)
        pt = GPSTelemetry(
            vehicle_id=veh1.id,
            latitude=lat,
            longitude=lng,
            altitude=15.0,
            speed_kmh=spd,
            heading=hdg,
            satellites=10,
            ignition=True,
            battery_pct=95.0,
            odometer_km=48200.5 + (idx * 1.5),
            recorded_at=t_time
        )
        db.session.add(pt)

    # 7. Add Alert for overspeed
    alert = Alert(
        vehicle_id=veh1.id,
        alert_type="overspeed",
        severity="warning",
        message="Vehicle exceeded 80 km/h limit (recorded 84.2 km/h)",
        latitude=19.0910,
        longitude=72.8940,
        speed_kmh=84.2,
        is_acknowledged=False,
        created_at=now - timedelta(minutes=10)
    )
    db.session.add(alert)

    # 8. Add Sample Client Company & Location
    from app.models.company import Company, CompanyLocation
    comp1 = Company(
        organization_id=org.id,
        name="Reliance Retail Logistics",
        contact_person="Arun Verma",
        contact_email="arun.verma@relianceretail.com",
        contact_phone="+91-22-2789-0123",
        gst_number="27AAACR1234F1Z5",
        notes="Primary distribution client for West zone",
    )
    db.session.add(comp1)
    db.session.flush()

    loc1 = CompanyLocation(
        company_id=comp1.id,
        name="Bhiwandi Central Fulfillment Depot",
        address="Plot 42, Logistics Park",
        city="Thane",
        state="Maharashtra",
        latitude=19.2965,
        longitude=73.0631,
        location_type="warehouse",
    )
    db.session.add(loc1)

    # 9. Add Sample Completed Trip with Stops
    from app.models.trip import Trip, Stop
    trip1 = Trip(
        organization_id=org.id,
        vehicle_id=veh1.id,
        driver_id=driver1.id,
        status="completed",
        load_status="loaded",
        start_time=now - timedelta(hours=3),
        end_time=now - timedelta(minutes=30),
        start_latitude=19.0760,
        start_longitude=72.8777,
        end_latitude=19.2965,
        end_longitude=73.0631,
        distance_km=32.4,
        duration_minutes=150.0,
        idle_minutes=25.0,
        max_speed_kmh=84.2,
        avg_speed_kmh=42.0,
        notes="Delivery manifest #RT-88231 completed",
    )
    db.session.add(trip1)
    db.session.flush()

    stop1 = Stop(
        trip_id=trip1.id,
        vehicle_id=trip1.vehicle_id,
        latitude=19.1500,
        longitude=72.9500,
        address="Navi Mumbai Checkpost",
        arrived_at=now - timedelta(hours=2),
        departed_at=now - timedelta(hours=1, minutes=35),
        duration_minutes=25.0,
    )
    db.session.add(stop1)

    db.session.commit()
    print("[+] Initial seed data populated successfully.")

