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

    # Initialize test data
    test_data = {
        "coworking_spaces": {
            "1": {
                "name": "Test Space",
                "location": "Test Location",
                "capacity": 50,
                "current_occupancy": 25,
                "equipment": [
                    {"name": "Projector", "quantity": 2},
                    {"name": "Whiteboard", "quantity": 5},
                ],
            }
        },
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


def test_registration_form_page(authenticated_client):
    """Test that the registration form page loads correctly"""
    rv = authenticated_client.get("/registration_form")
    assert b"Registration Form" in rv.data
    assert b"User Registration Form" in rv.data


def test_submit_registration_success(authenticated_client):
    """Test submitting a registration form successfully"""
    # First add a space to register for
    rv = authenticated_client.post(
        "/add_space",
        data=dict(
            name="Registration Test Space",
            location="Registration Test Location",
            capacity=20,
        ),
        follow_redirects=True,
    )

    assert b"Space added successfully" in rv.data

    # Get the ID of the newly added space by parsing the registration form page
    rv = authenticated_client.get("/registration_form")

    import re

    match = re.search(
        r'<option value="(\d+)">Registration Test Space \(Coworking Space - Registration Test Location\)</option>',
        rv.data.decode("utf-8"),
    )
    assert match, "Could not find space ID in registration form page"
    space_id = match.group(1)

    # Submit a registration
    rv = authenticated_client.post(
        "/submit_registration",
        data=dict(
            firstName="John",
            lastName="Doe",
            email="john.doe@example.com",
            phone="123-456-7890",
            company="Test Company",
            space=space_id,
            membershipType="monthly",
            startDate="2025-10-01",
            additionalInfo="Testing registration",
        ),
        follow_redirects=True,
    )

    assert b"Registration submitted successfully" in rv.data

    # Check that the registration appears in the submissions list
    rv = authenticated_client.get("/registrations")
    assert b"John Doe" in rv.data
    assert b"john.doe@example.com" in rv.data
    assert b"Registration Test Space" in rv.data
    assert b"Monthly Membership" in rv.data


def test_submit_registration_invalid_space(authenticated_client):
    """Test submitting a registration with invalid space"""
    # Submit a registration with invalid space
    rv = authenticated_client.post(
        "/submit_registration",
        data=dict(
            firstName="John",
            lastName="Doe",
            email="john.doe@example.com",
            phone="123-456-7890",
            company="Test Company",
            space="999",
            membershipType="monthly",
            startDate="2025-10-01",
            additionalInfo="Testing registration",
        ),
        follow_redirects=True,
    )

    assert b"Invalid space selected" in rv.data


def test_registrations_page_empty(authenticated_client):
    """Test that the registrations page loads correctly"""
    rv = authenticated_client.get("/registrations")
    assert b"Registration Submissions" in rv.data


def test_registrations_page_with_data(authenticated_client):
    """Test that the registrations page shows data when present"""
    # First add a space to register for
    rv = authenticated_client.post(
        "/add_space",
        data=dict(
            name="Registration Test Space 2",
            location="Registration Test Location 2",
            capacity=25,
        ),
        follow_redirects=True,
    )

    assert b"Space added successfully" in rv.data

    # Get the ID of the newly added space by parsing the registration form page
    rv = authenticated_client.get("/registration_form")
    import re

    match = re.search(
        r'<option value="(\d+)">Registration Test Space 2 \(Coworking Space - Registration Test Location 2\)</option>',
        rv.data.decode("utf-8"),
    )
    assert match, "Could not find space ID in registration form page"
    space_id = match.group(1)

    # Submit a registration first
    rv = authenticated_client.post(
        "/submit_registration",
        data=dict(
            firstName="Jane",
            lastName="Smith",
            email="jane.smith@example.com",
            phone="098-765-4321",
            company="Another Company",
            space=space_id,
            membershipType="annual",
            startDate="2025-11-01",
            additionalInfo="Another test",
        ),
        follow_redirects=True,
    )

    # Check that the registration appears in the submissions list
    rv = authenticated_client.get("/registrations")
    assert b"Registration Submissions" in rv.data
    assert b"Jane Smith" in rv.data
    assert b"jane.smith@example.com" in rv.data
    assert b"Registration Test Space 2" in rv.data
    assert b"Annual Membership" in rv.data
