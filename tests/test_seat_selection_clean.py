import json
import os
import tempfile

import pytest


@pytest.fixture
def clean_client():
    # Create a temporary file for testing
    db_fd, temp_data_file = tempfile.mkstemp()

    # Set the DATA_FILE environment variable
    os.environ["DATA_FILE"] = temp_data_file

    # Import app after setting environment variable
    from app import app

    # Initialize test data with no existing spaces
    test_data = {
        "coworking_spaces": {},
        "meeting_rooms": {},
        "admins": {"admin": "password"},
        "registrations": [],
    }

    # Write test data to temp file
    with open(temp_data_file, "w") as f:
        json.dump(test_data, f)

    with app.test_client() as client:
        with app.app_context():
            yield client

    # Cleanup
    os.close(db_fd)
    os.unlink(temp_data_file)
    if "DATA_FILE" in os.environ:
        del os.environ["DATA_FILE"]


@pytest.fixture
def clean_authenticated_client(clean_client):
    # Login as admin
    rv = clean_client.post(
        "/login",
        data=dict(username="admin", password="password"),
        follow_redirects=True,
    )

    return clean_client


def test_add_space_with_seat_layout(clean_authenticated_client):
    """Test adding a new space with seat layout configuration"""
    rv = clean_authenticated_client.post(
        "/add_space",
        data=dict(
            name="New Space with Seats",
            location="New Location",
            capacity=6,
            rows=2,
            cols=3
        ),
        follow_redirects=True,
    )

    assert b"Space added successfully" in rv.data

    # Check that the new space (ID 1) has the correct seat layout
    rv = clean_authenticated_client.get("/space/1")
    assert b"New Space with Seats" in rv.data
    assert b"Seat Map" in rv.data


def test_submit_registration_with_seat_selection(clean_authenticated_client):
    """Test submitting a registration with seat selection"""
    # First add a new space with seats
    rv = clean_authenticated_client.post(
        "/add_space",
        data=dict(
            name="Test Space for Registration",
            location="Test Location",
            capacity=4,
            rows=2,
            cols=2
        ),
        follow_redirects=True,
    )
    assert b"Space added successfully" in rv.data

    # Submit a registration with seat selection for the new space (ID 1)
    rv = clean_authenticated_client.post(
        "/submit_registration",
        data=dict(
            firstName="John",
            lastName="Doe",
            email="john.doe@example.com",
            phone="123-456-7890",
            company="Test Company",
            space="1",  # Using the newly created space
            membershipType="monthly",
            startDate="2025-10-01",
            additionalInfo="Testing seat selection",
            selectedSeat="1-1"  # Select seat 1-1
        ),
        follow_redirects=True,
    )

    assert b"Registration submitted successfully" in rv.data

    # Check that the registration appears with seat information
    rv = clean_authenticated_client.get("/registrations")
    assert b"John Doe" in rv.data
    assert b"1-1" in rv.data  # Should show the selected seat


def test_submit_registration_with_occupied_seat(clean_authenticated_client):
    """Test submitting a registration with an already occupied seat"""
    # First add a new space with seats
    rv = clean_authenticated_client.post(
        "/add_space",
        data=dict(
            name="Test Space for Occupied Seat",
            location="Test Location",
            capacity=4,
            rows=2,
            cols=2
        ),
        follow_redirects=True,
    )
    assert b"Space added successfully" in rv.data

    # First, create a registration that occupies seat 1-1
    rv = clean_authenticated_client.post(
        "/submit_registration",
        data=dict(
            firstName="Alice",
            lastName="Smith",
            email="alice@example.com",
            phone="111-222-3333",
            company="Company A",
            space="1",  # Using the newly created space (ID 1)
            membershipType="monthly",
            startDate="2025-10-01",
            additionalInfo="First registration",
            selectedSeat="1-1"
        ),
        follow_redirects=True,
    )
    assert b"Registration submitted successfully" in rv.data

    # Now try to register the same seat again
    rv = clean_authenticated_client.post(
        "/submit_registration",
        data=dict(
            firstName="Bob",
            lastName="Johnson",
            email="bob@example.com",
            phone="444-555-6666",
            company="Company B",
            space="1",  # Same space
            membershipType="monthly",
            startDate="2025-10-01",
            additionalInfo="Second registration attempt",
            selectedSeat="1-1"  # Same seat
        ),
        follow_redirects=True,
    )

    # Should show error message
    assert b"Selected seat is not available" in rv.data


def test_seat_reservation_persistence(clean_authenticated_client):
    """Test that seat reservations are persisted and displayed correctly"""
    # First add a new space with seats
    rv = clean_authenticated_client.post(
        "/add_space",
        data=dict(
            name="Test Space for Persistence",
            location="Test Location",
            capacity=4,
            rows=2,
            cols=2
        ),
        follow_redirects=True,
    )
    assert b"Space added successfully" in rv.data

    # Submit a registration with seat selection
    rv = clean_authenticated_client.post(
        "/submit_registration",
        data=dict(
            firstName="Test",
            lastName="User",
            email="test@example.com",
            phone="123-456-7890",
            company="Test Company",
            space="1",  # Using the newly created space (ID 1)
            membershipType="monthly",
            startDate="2025-10-01",
            additionalInfo="Testing persistence",
            selectedSeat="2-2"
        ),
        follow_redirects=True,
    )
    assert b"Registration submitted successfully" in rv.data

    # Check space detail page to see if seat is now marked as occupied
    rv = clean_authenticated_client.get("/space/1")
    assert b"2-2" in rv.data  # Seat should still be displayed

    # Check API to see if seat is marked as unavailable
    rv = clean_authenticated_client.get("/api/seats/1")
    response_data = json.loads(rv.data.decode("utf-8"))
    assert response_data["seats"]["2-2"]["available"] is False
    assert response_data["seats"]["2-2"]["reserved_by"] == "Test User"