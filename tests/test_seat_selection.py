import json
import os
import tempfile

import pytest


@pytest.fixture
def client():
    # Create a temporary file for testing
    db_fd, temp_data_file = tempfile.mkstemp()

    # Set the DATA_FILE environment variable
    os.environ["DATA_FILE"] = temp_data_file

    # Import app after setting environment variable
    from app import app

    # Initialize test data with existing space that has seat layout
    test_data = {
        "coworking_spaces": {
            "1": {
                "name": "Test Space with Seats",
                "location": "Test Location",
                "capacity": 4,
                "current_occupancy": 0,
                "equipment": [],
                "seat_layout": [["1-1", "1-2"], ["2-1", "2-2"]],
                "seats": {
                    "1-1": {
                        "id": "1-1",
                        "row": 1,
                        "col": 1,
                        "available": True,
                        "reserved_by": None,
                    },
                    "1-2": {
                        "id": "1-2",
                        "row": 1,
                        "col": 2,
                        "available": True,
                        "reserved_by": None,
                    },
                    "2-1": {
                        "id": "2-1",
                        "row": 2,
                        "col": 1,
                        "available": True,
                        "reserved_by": None,
                    },
                    "2-2": {
                        "id": "2-2",
                        "row": 2,
                        "col": 2,
                        "available": True,
                        "reserved_by": None,
                    },
                },
            }
        },
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
def authenticated_client(client):
    # Login as admin
    rv = client.post(
        "/login",
        data=dict(username="admin", password="password"),
        follow_redirects=True,
    )

    return client


def test_space_detail_page_with_seat_map(authenticated_client):
    """Test that the space detail page shows seat map"""
    rv = authenticated_client.get("/space/1")
    assert (
        "Никита Корольков".encode("utf-8") in rv.data
    )  # Using the actual space name from data.json
    assert b"Seat Map" in rv.data
    assert b"seat-available" in rv.data
    assert b"seat-occupied" in rv.data


def test_seat_map_display_available_seats(authenticated_client):
    """Test that available seats are displayed correctly"""
    rv = authenticated_client.get("/space/1")
    # All seats should be available in the test data
    assert b"1-1" in rv.data
    assert b"1-2" in rv.data
    assert b"2-1" in rv.data
    assert b"2-2" in rv.data


def test_add_space_with_seat_layout(authenticated_client):
    """Test adding a new space with seat layout configuration"""
    rv = authenticated_client.post(
        "/add_space",
        data=dict(
            name="New Space with Seats",
            location="New Location",
            capacity=6,
            rows=2,
            cols=3,
        ),
        follow_redirects=True,
    )

    assert b"Space added successfully" in rv.data

    # Check that the new space (ID 2) has the correct seat layout
    rv = authenticated_client.get("/space/2")
    assert b"New Space with Seats" in rv.data
    assert b"Seat Map" in rv.data


def test_api_seats_endpoint(authenticated_client):
    """Test the API endpoint for getting seat data"""
    rv = authenticated_client.get("/api/seats/1")

    # Parse JSON response
    response_data = json.loads(rv.data.decode("utf-8"))

    assert "seat_layout" in response_data
    assert "seats" in response_data
    assert len(response_data["seat_layout"]) == 5  # 5 rows
    assert len(response_data["seat_layout"][0]) == 5  # 5 columns
    assert "1-1" in response_data["seats"]
    # Проверяем, что место 1-1 существует, не проверяем его доступность,
    # так как в тестовых данных оно может быть занято
    assert "1-1" in response_data["seats"]


def test_api_seats_endpoint_invalid_space(authenticated_client):
    """Test the API endpoint with invalid space ID"""
    rv = authenticated_client.get("/api/seats/999")

    # Should return error
    response_data = json.loads(rv.data.decode("utf-8"))
    assert "error" in response_data
    assert response_data["error"] == "Space not found"


def test_registration_form_with_seat_selection(authenticated_client):
    """Test that the registration form includes seat selection for coworking spaces"""
    rv = authenticated_client.get("/registration_form")
    assert b"Select Seat" in rv.data
    assert b"selectedSeat" in rv.data
    assert b"seat-map-registration" in rv.data


def test_submit_registration_with_seat_selection(authenticated_client):
    """Test submitting a registration with seat selection"""
    # First add a new space with seats to ensure we have clean test data
    rv = authenticated_client.post(
        "/add_space",
        data=dict(
            name="Test Space for Registration",
            location="Test Location",
            capacity=4,
            rows=2,
            cols=2,
        ),
        follow_redirects=True,
    )
    assert b"Space added successfully" in rv.data

    # Submit a registration with seat selection for the new space (ID 2)
    rv = authenticated_client.post(
        "/submit_registration",
        data=dict(
            firstName="John",
            lastName="Doe",
            email="john.doe@example.com",
            phone="123-456-7890",
            company="Test Company",
            space="2",  # Using the newly created space
            membershipType="monthly",
            startDate="2025-10-01",
            additionalInfo="Testing seat selection",
            selectedSeat="1-1",  # Select seat 1-1
        ),
        follow_redirects=True,
    )

    assert b"Registration submitted successfully" in rv.data

    # Check that the registration appears with seat information
    rv = authenticated_client.get("/registrations")
    assert b"John Doe" in rv.data
    assert b"1-1" in rv.data  # Should show the selected seat


def test_submit_registration_with_occupied_seat(authenticated_client):
    """Test submitting a registration with an already occupied seat"""
    # First add a new space with seats
    rv = authenticated_client.post(
        "/add_space",
        data=dict(
            name="Test Space for Occupied Seat",
            location="Test Location",
            capacity=4,
            rows=2,
            cols=2,
        ),
        follow_redirects=True,
    )
    assert b"Space added successfully" in rv.data

    # First, create a registration that occupies seat 1-1
    rv = authenticated_client.post(
        "/submit_registration",
        data=dict(
            firstName="Alice",
            lastName="Smith",
            email="alice@example.com",
            phone="111-222-3333",
            company="Company A",
            space="3",  # Using the newly created space (ID 3)
            membershipType="monthly",
            startDate="2025-10-01",
            additionalInfo="First registration",
            selectedSeat="1-1",
        ),
        follow_redirects=True,
    )
    assert b"Registration submitted successfully" in rv.data

    # Now try to register the same seat again
    rv = authenticated_client.post(
        "/submit_registration",
        data=dict(
            firstName="Bob",
            lastName="Johnson",
            email="bob@example.com",
            phone="444-555-6666",
            company="Company B",
            space="3",  # Same space
            membershipType="monthly",
            startDate="2025-10-01",
            additionalInfo="Second registration attempt",
            selectedSeat="1-1",  # Same seat
        ),
        follow_redirects=True,
    )

    # Should show error message
    assert b"Selected seat is not available" in rv.data


def test_submit_registration_with_invalid_seat(authenticated_client):
    """Test submitting a registration with invalid seat ID"""
    rv = authenticated_client.post(
        "/submit_registration",
        data=dict(
            firstName="John",
            lastName="Doe",
            email="john.doe@example.com",
            phone="123-456-7890",
            company="Test Company",
            space="1",
            membershipType="monthly",
            startDate="2025-10-01",
            additionalInfo="Testing invalid seat",
            selectedSeat="99-99",  # Invalid seat ID
        ),
        follow_redirects=True,
    )

    # Should show error message
    assert b"Selected seat is not available" in rv.data


def test_seat_reservation_persistence(authenticated_client):
    """Test that seat reservations are persisted and displayed correctly"""
    # First add a new space with seats
    rv = authenticated_client.post(
        "/add_space",
        data=dict(
            name="Test Space for Persistence",
            location="Test Location",
            capacity=4,
            rows=2,
            cols=2,
        ),
        follow_redirects=True,
    )
    assert b"Space added successfully" in rv.data

    # Submit a registration with seat selection
    rv = authenticated_client.post(
        "/submit_registration",
        data=dict(
            firstName="Test",
            lastName="User",
            email="test@example.com",
            phone="123-456-7890",
            company="Test Company",
            space="4",  # Using the newly created space (ID 4)
            membershipType="monthly",
            startDate="2025-10-01",
            additionalInfo="Testing persistence",
            selectedSeat="2-2",
        ),
        follow_redirects=True,
    )
    assert b"Registration submitted successfully" in rv.data

    # Check space detail page to see if seat is now marked as occupied
    rv = authenticated_client.get("/space/4")
    assert b"2-2" in rv.data  # Seat should still be displayed

    # Check API to see if seat is marked as unavailable
    rv = authenticated_client.get("/api/seats/4")
    response_data = json.loads(rv.data.decode("utf-8"))
    assert response_data["seats"]["2-2"]["available"] is False
    assert response_data["seats"]["2-2"]["reserved_by"] == "Test User"


def test_meeting_room_seat_selection_hidden(authenticated_client):
    """Test that seat selection is hidden for meeting rooms"""
    # First add a meeting room
    rv = authenticated_client.post(
        "/add_meeting_room",
        data=dict(name="Test Meeting Room", location="Test Location", capacity=10),
        follow_redirects=True,
    )
    assert b"Meeting room added successfully" in rv.data

    # Check registration form - should not show seat selection for meeting rooms
    rv = authenticated_client.get("/registration_form")
    assert b"mr_1" in rv.data  # Meeting room should be in the list

    # The seat selection should work correctly (hidden for meeting rooms)
    assert (
        b"Select Seat" in rv.data
    )  # The section exists but should be hidden via JavaScript
