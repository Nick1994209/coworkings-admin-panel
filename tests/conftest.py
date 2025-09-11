import pytest
import os
import tempfile
import json

@pytest.fixture
def client():
    # Create a temporary file for testing
    db_fd, temp_data_file = tempfile.mkstemp()
    
    # Set the DATA_FILE environment variable
    os.environ['DATA_FILE'] = temp_data_file
    
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
                    {"name": "Whiteboard", "quantity": 5}
                ]
            }
        },
        "admins": {
            "admin": "password"
        },
        "registrations": []  # Add registrations array
    }
    
    # Write test data to temp file
    with open(temp_data_file, 'w') as f:
        json.dump(test_data, f)
    
    with app.test_client() as client:
        with app.app_context():
            yield client
    
    # Cleanup
    os.close(db_fd)
    os.unlink(temp_data_file)
    if 'DATA_FILE' in os.environ:
        del os.environ['DATA_FILE']

@pytest.fixture
def authenticated_client(client):
    # Login as admin
    rv = client.post('/login', data=dict(
        username='admin',
        password='password'
    ), follow_redirects=True)
    
    return client