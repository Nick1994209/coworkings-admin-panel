# Coworking Space Admin Panel

A Flask-based administration panel for managing multiple coworking spaces. This application provides administrators with tools to monitor occupancy, manage equipment, and handle registration requests.

## Features

- Admin-only access with login authentication
- Manage multiple coworking spaces
- View occupancy statistics and utilization rates
- Track equipment inventory for each space
- Registration form for new members
- Responsive web interface using Bootstrap

## Requirements

- Python 3.13
- Flask 3.1.2

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd coworking-admin-panel
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to `http://localhost:5000`

3. Login with the default credentials:
   - Username: `admin`
   - Password: `password`

**Note:** For production use, change the secret key and admin credentials in `app.py`.

## Application Structure

- `app.py`: Main Flask application file
- `templates/`: HTML templates for the web interface
- `data.json`: Local storage for coworking space data (automatically created)
- `requirements.txt`: Python package dependencies
- `README.md`: This file
- `tests/`: Test suite for the application
- `run_tests.py`: Test runner script

## Functionality

### Dashboard
The main dashboard provides an overview of all coworking spaces and quick access to management features.

### Spaces Management
- View all coworking spaces with occupancy statistics
- Add new spaces with name, location, and capacity
- Edit existing space details
- Delete spaces
- Update current occupancy numbers

### Equipment Tracking
- View equipment inventory for each space
- Add new equipment items with quantities

### Registration Form
- Sample registration form for new members
- Shows available spaces and membership options

## Data Storage

Data is stored locally in a JSON file (`data.json`) which is automatically created when the application starts. This includes:
- Coworking space information (names, locations, capacities)
- Current occupancy levels
- Equipment inventories
- Admin credentials (for demo purposes)

## Security Notes

This is a demonstration application with simplified security:
- Default admin credentials are hardcoded (`admin`/`password`)
- Secret key is hardcoded in the application
- No encryption for stored data

For production use, implement:
- Proper user authentication and authorization
- Secure password storage (hashing)
- Environment-based configuration
- Database storage instead of JSON files

## Testing

### Running Tests

You can run the tests in multiple ways:

1. Using the test runner script:
   ```
   python run_tests.py
   ```

2. Directly with pytest:
   ```
   python -m pytest tests/
   ```

3. With verbose output:
   ```
   python -m pytest tests/ -v
   ```

### Test Coverage

The test suite includes:
- Authentication tests (login/logout)
- Page rendering tests
- CRUD operations for coworking spaces
- Equipment management tests
- Form submission tests

## License

This project is licensed under the MIT License.