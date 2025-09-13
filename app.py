import json
import os
from datetime import datetime
from functools import wraps
import pathlib

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "your-secret-key-change-in-production"

# Local data storage
DATA_DIRECTORY = pathlib.Path(os.environ.get("DATA_DIRECTORY", "data"))
DATA_FILE = DATA_DIRECTORY / "data.json"
os.makedirs(DATA_DIRECTORY, exist_ok=True)


# Initialize data file if it doesn't exist
def init_data():
    if not os.path.exists(DATA_FILE):
        initial_data = {
            "coworking_spaces": {},
            "meeting_rooms": {},  # New entity for meeting rooms
            "admins": {"admin": "password"},  # Simple auth for demo purposes
            "registrations": [],  # Store registration forms
        }
        with open(DATA_FILE, "w") as f:
            json.dump(initial_data, f, indent=2)


# Load data from file
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # If file doesn't exist, create it with default data
        init_data()
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # Ensure meeting_rooms key exists for backward compatibility
            if "meeting_rooms" not in data:
                data["meeting_rooms"] = {}
            return data


# Save data to file
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# Admin login required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_logged_in" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
@admin_required
def index():
    data = load_data()
    return render_template("index.html", spaces=data["coworking_spaces"])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        data = load_data()
        if username in data["admins"] and data["admins"][username] == password:
            session["admin_logged_in"] = True
            session["username"] = username
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/spaces")
@admin_required
def spaces():
    data = load_data()
    return render_template("spaces.html", spaces=data["coworking_spaces"])
    
    
@app.route("/meeting_rooms")
@admin_required
def meeting_rooms():
    data = load_data()
    return render_template("meeting_rooms.html", meeting_rooms=data["meeting_rooms"])


@app.route("/space/<space_id>")
@admin_required
def space_detail(space_id):
    data = load_data()
    if space_id not in data["coworking_spaces"]:
        flash("Space not found")
        return redirect(url_for("spaces"))

    space = data["coworking_spaces"][space_id]
    
    # Get registrations for this space
    space_registrations = [reg for reg in data["registrations"] if reg["space_id"] == space_id]
    
    return render_template("space_detail.html", space=space, space_id=space_id, registrations=space_registrations)
    
    
@app.route("/meeting_room/<room_id>")
@admin_required
def meeting_room_detail(room_id):
    data = load_data()
    if room_id not in data["meeting_rooms"]:
        flash("Meeting room not found")
        return redirect(url_for("meeting_rooms"))
        
    room = data["meeting_rooms"][room_id]
    
    # Get registrations for this meeting room (we'll need to modify the registration model to support this)
    # For now, we'll just show the room details
    return render_template("meeting_room_detail.html", room=room, room_id=room_id)


@app.route("/add_space", methods=["GET", "POST"])
@admin_required
def add_space():
    if request.method == "POST":
        name = request.form["name"]
        location = request.form["location"]
        capacity = int(request.form["capacity"])

        data = load_data()
        new_id = str(len(data["coworking_spaces"]) + 1)

        data["coworking_spaces"][new_id] = {
            "name": name,
            "location": location,
            "capacity": capacity,
            "current_occupancy": 0,
            "equipment": [],
        }

        save_data(data)
        flash("Space added successfully")
        return redirect(url_for("spaces"))

    return render_template("add_space.html")
    
    
@app.route("/add_meeting_room", methods=["GET", "POST"])
@admin_required
def add_meeting_room():
    if request.method == "POST":
        name = request.form["name"]
        location = request.form["location"]
        capacity = int(request.form["capacity"])
        
        data = load_data()
        new_id = str(len(data["meeting_rooms"]) + 1)
        
        data["meeting_rooms"][new_id] = {
            "name": name,
            "location": location,
            "capacity": capacity,
            "current_occupancy": 0,
        }
        
        save_data(data)
        flash("Meeting room added successfully")
        return redirect(url_for("meeting_rooms"))
        
    return render_template("add_meeting_room.html")
    
    
@app.route("/edit_meeting_room/<room_id>", methods=["GET", "POST"])
@admin_required
def edit_meeting_room(room_id):
    data = load_data()
    if room_id not in data["meeting_rooms"]:
        flash("Meeting room not found")
        return redirect(url_for("meeting_rooms"))
        
    if request.method == "POST":
        data["meeting_rooms"][room_id]["name"] = request.form["name"]
        data["meeting_rooms"][room_id]["location"] = request.form["location"]
        data["meeting_rooms"][room_id]["capacity"] = int(request.form["capacity"])
        save_data(data)
        flash("Meeting room updated successfully")
        return redirect(url_for("meeting_room_detail", room_id=room_id))
        
    room = data["meeting_rooms"][room_id]
    return render_template("edit_meeting_room.html", room=room, room_id=room_id)


@app.route("/edit_space/<space_id>", methods=["GET", "POST"])
@admin_required
def edit_space(space_id):
    data = load_data()
    if space_id not in data["coworking_spaces"]:
        flash("Space not found")
        return redirect(url_for("spaces"))

    if request.method == "POST":
        data["coworking_spaces"][space_id]["name"] = request.form["name"]
        data["coworking_spaces"][space_id]["location"] = request.form["location"]
        data["coworking_spaces"][space_id]["capacity"] = int(request.form["capacity"])
        save_data(data)
        flash("Space updated successfully")
        return redirect(url_for("space_detail", space_id=space_id))

    space = data["coworking_spaces"][space_id]
    return render_template("edit_space.html", space=space, space_id=space_id)


@app.route("/delete_space/<space_id>")
@admin_required
def delete_space(space_id):
    data = load_data()
    if space_id in data["coworking_spaces"]:
        del data["coworking_spaces"][space_id]
        save_data(data)
        flash("Space deleted successfully")
    else:
        flash("Space not found")
    return redirect(url_for("spaces"))


@app.route("/update_occupancy/<space_id>", methods=["POST"])
@admin_required
def update_occupancy(space_id):
    occupancy = int(request.form["occupancy"])
    data = load_data()

    if space_id in data["coworking_spaces"]:
        if occupancy <= data["coworking_spaces"][space_id]["capacity"]:
            data["coworking_spaces"][space_id]["current_occupancy"] = occupancy
            save_data(data)
            flash("Occupancy updated successfully")
        else:
            flash("Occupancy cannot exceed capacity")
    else:
        flash("Space not found")

    return redirect(url_for("space_detail", space_id=space_id))


@app.route("/add_equipment/<space_id>", methods=["POST"])
@admin_required
def add_equipment(space_id):
    equipment_name = request.form["equipment_name"]
    quantity = int(request.form["quantity"])

    data = load_data()
    if space_id in data["coworking_spaces"]:
        data["coworking_spaces"][space_id]["equipment"].append(
            {"name": equipment_name, "quantity": quantity}
        )
        save_data(data)
        flash("Equipment added successfully")

    return redirect(url_for("space_detail", space_id=space_id))


@app.route("/registration_form")
@admin_required
def registration_form():
    data = load_data()
    # Combine coworking spaces and meeting rooms for the registration form
    all_spaces = {}
    # Add coworking spaces
    all_spaces.update(data["coworking_spaces"])
    # Add meeting rooms with a prefix to distinguish them
    for room_id, room in data["meeting_rooms"].items():
        all_spaces[f"mr_{room_id}"] = room
    return render_template("registration_form.html", spaces=all_spaces)


@app.route("/submit_registration", methods=["POST"])
@admin_required
def submit_registration():
    # Get form data
    first_name = request.form["firstName"]
    last_name = request.form["lastName"]
    email = request.form["email"]
    phone = request.form["phone"]
    company = request.form["company"]
    space_id = request.form["space"]
    membership_type = request.form["membershipType"]
    start_date = request.form["startDate"]
    additional_info = request.form["additionalInfo"]

    # Load data
    data = load_data()

    # Check if it's a coworking space or meeting room
    space_name = ""
    is_meeting_room = False
    
    if space_id.startswith("mr_"):
        # It's a meeting room (mr_ prefix)
        is_meeting_room = True
        room_id = space_id[3:]  # Remove "mr_" prefix
        if room_id not in data["meeting_rooms"]:
            flash("Invalid meeting room selected")
            return redirect(url_for("registration_form"))
        space_name = data["meeting_rooms"][room_id]["name"]
    else:
        # It's a coworking space
        if space_id not in data["coworking_spaces"]:
            flash("Invalid space selected")
            return redirect(url_for("registration_form"))
        space_name = data["coworking_spaces"][space_id]["name"]
    
    # Create registration record
    registration = {
        "id": len(data["registrations"]) + 1,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "company": company,
        "space_id": space_id,
        "space_name": space_name,
        "membership_type": membership_type,
        "start_date": start_date,
        "additional_info": additional_info,
        "submitted_at": datetime.now().isoformat(),
        "is_meeting_room": is_meeting_room
    }
    
    # Add to registrations
    data["registrations"].append(registration)
    
    # Update current occupancy for the space
    if is_meeting_room:
        room_id = space_id[3:]  # Remove "mr_" prefix
        data["meeting_rooms"][room_id]["current_occupancy"] += 1
    else:
        data["coworking_spaces"][space_id]["current_occupancy"] += 1
    
    # Save data
    save_data(data)

    flash("Registration submitted successfully")
    return redirect(url_for("registration_form"))


@app.route("/registrations")
@admin_required
def registrations():
    data = load_data()
    return render_template("registrations.html", registrations=data["registrations"])


@app.route("/api/meeting_rooms_count")
@admin_required
def api_meeting_rooms_count():
    data = load_data()
    return {"count": len(data["meeting_rooms"])}


if __name__ == "__main__":
    init_data()
    app.run(host="0.0.0.0", debug=True)
