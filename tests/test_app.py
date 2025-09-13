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
        "coworking_spaces": {},
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


def test_index_page(client):
    """Test that the index page loads correctly"""
    rv = client.get("/", follow_redirects=True)
    # Should redirect to login page
    assert b"Admin Login" in rv.data


def test_login_page_get(client):
    """Test that the login page loads correctly"""
    rv = client.get("/login")
    assert b"Admin Login" in rv.data
    assert b"Username" in rv.data
    assert b"Password" in rv.data


def test_login_success(client):
    """Test successful login"""
    rv = client.post(
        "/login",
        data=dict(username="admin", password="password"),
        follow_redirects=True,
    )

    assert b"Dashboard" in rv.data
    assert b"Welcome to the Coworking Space Administration Panel" in rv.data


def test_login_failure(client):
    """Test failed login"""
    rv = client.post(
        "/login", data=dict(username="wrong", password="wrong"), follow_redirects=True
    )

    assert b"Invalid credentials" in rv.data


def test_authenticated_access(authenticated_client):
    """Test that authenticated users can access protected pages"""
    rv = authenticated_client.get("/")
    assert b"Dashboard" in rv.data


def test_spaces_page(authenticated_client):
    """Test that the spaces page loads correctly"""
    rv = authenticated_client.get("/spaces")
    assert b"Coworking Spaces" in rv.data


def test_add_space_page(authenticated_client):
    """Test that the add space page loads correctly"""
    rv = authenticated_client.get("/add_space")
    assert b"Add New Coworking Space" in rv.data


def test_registration_form_page(authenticated_client):
    """Test that the registration form page loads correctly"""
    rv = authenticated_client.get("/registration_form")
    assert b"Registration Form" in rv.data
    assert b"User Registration Form" in rv.data


def test_logout(authenticated_client):
    """Test logout functionality"""
    rv = authenticated_client.get("/logout", follow_redirects=True)
    assert b"Admin Login" in rv.data


def test_space_operations(authenticated_client):
    """Test adding, viewing, editing, and deleting a space"""
    # Add a space
    rv = authenticated_client.post(
        "/add_space",
        data=dict(name="Test Space", location="Test Location", capacity=50),
        follow_redirects=True,
    )

    assert b"Space added successfully" in rv.data

    # Check that the space was added (it should have ID 1)
    rv = authenticated_client.get("/space/1")
    assert b"Test Space" in rv.data
    assert b"Test Location" in rv.data

    # Test updating occupancy
    rv = authenticated_client.post(
        "/update_occupancy/1", data=dict(occupancy=30), follow_redirects=True
    )

    assert b"Occupancy updated successfully" in rv.data

    # Check that the occupancy was updated
    rv = authenticated_client.get("/space/1")
    assert b"30" in rv.data

    # Test adding equipment
    rv = authenticated_client.post(
        "/add_equipment/1",
        data=dict(equipment_name="Projector", quantity=2),
        follow_redirects=True,
    )

    assert b"Equipment added successfully" in rv.data

    # Check that the equipment was added
    rv = authenticated_client.get("/space/1")
    assert b"Projector" in rv.data

    # Test editing the space
    rv = authenticated_client.post(
        "/edit_space/1",
        data=dict(
            name="Updated Test Space", location="Updated Test Location", capacity=75
        ),
        follow_redirects=True,
    )

    assert b"Space updated successfully" in rv.data

    # Check that the space was updated
    rv = authenticated_client.get("/space/1")
    assert b"Updated Test Space" in rv.data
    assert b"Updated Test Location" in rv.data

    # Test deleting the space
    rv = authenticated_client.get("/delete_space/1", follow_redirects=True)
    assert b"Space deleted successfully" in rv.data


def test_space_detail_not_found(authenticated_client):
    """Test that accessing a non-existent space shows an error"""
    rv = authenticated_client.get("/space/999", follow_redirects=True)
    assert b"Space not found" in rv.data


def test_add_space(authenticated_client):
    """Test adding a new space"""
    rv = authenticated_client.post(
        "/add_space",
        data=dict(name="New Space", location="New Location", capacity=100),
        follow_redirects=True,
    )

    assert b"Space added successfully" in rv.data

    # Check that the space was actually added
    rv = authenticated_client.get("/spaces")
    assert b"New Space" in rv.data


def test_delete_space(authenticated_client):
    """Test deleting a space"""
    # First add a space to delete
    rv = authenticated_client.post(
        "/add_space",
        data=dict(name="Space to Delete", location="Delete Location", capacity=50),
        follow_redirects=True,
    )

    # Verify space was added (should be ID 2 since we already added one in the previous test)
    assert b"Space added successfully" in rv.data

    # Now delete the space
    rv = authenticated_client.get("/delete_space/2", follow_redirects=True)
    assert b"Space deleted successfully" in rv.data


def test_registration_submission(authenticated_client):
    """Test submitting a registration form"""
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


def test_registrations_page(authenticated_client):
    """Test that the registrations page loads correctly"""
    rv = authenticated_client.get("/registrations")
    assert b"Registration Submissions" in rv.data
