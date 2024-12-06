from flask import Flask, request, jsonify
import pandas as pd
import datetime
import hashlib
import pytz
import argparse

utc = pytz.UTC

parser = argparse.ArgumentParser(description='Run carbon intensity API server.')
parser.add_argument('--carbon-trace', type=str, default='us-east-1.csv', help='Data file for carbon intensity')
args = parser.parse_args()

# Load the carbon intensity data
data_file_path = args.carbon_trace  # Replace with the correct path to your CSV file
try:
    carbon_data = pd.read_csv(data_file_path)
except FileNotFoundError:
    print(f"Carbon intensity data file not found: {data_file_path}")
    exit(1)
carbon_data['datetime'] = pd.to_datetime(carbon_data['datetime'])  # Ensure timestamps are datetime objects
# make the datetime column the index
carbon_data.set_index('datetime', inplace=True)

# Flask app setup
app = Flask(__name__)

# In-memory store for registered users
user_registry = {}

def generate_user_id():
    """Generates a unique user hash ID based on the current time and a random component."""
    return hashlib.sha256(str(datetime.datetime.now()).encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register():
    initial_timestamp = request.json.get('timestamp')
    user_id = generate_user_id()
    try:
        # Store initial timestamp for this user
        initial_datetime = datetime.datetime.fromisoformat(initial_timestamp)

        # check if the datetime is in the data that we have access to
        if initial_datetime.isoformat() not in carbon_data.index:
            return jsonify({"error": "Requested time not available in local carbon intensity data."}), 400

        actual_datetime = datetime.datetime.now()
        user_registry[user_id] = initial_datetime, actual_datetime
        return jsonify({"user_id": user_id}), 201
    except ValueError:
        return jsonify({"error": "Invalid timestamp format. Use ISO format."}), 400

@app.route('/get_carbon_intensity', methods=['GET'])
def get_carbon_intensity():
    global user_registry

    user_id = request.args.get('user_id')
    if user_id not in user_registry:
        return jsonify({"error": "User ID not found. Register first."}), 404

    # Calculate the time delta
    initial_datetime, actual_datetime = user_registry[user_id]
    current_datetime = datetime.datetime.now()
    time_delta = current_datetime - actual_datetime

    # actual real time
    # elapsed_hours = int(time_delta.total_seconds() // 3600)

    # sped up by a factor of 60 (1 minute in real time = 1 hour in simulation time)
    elapsed_hours = int(time_delta.total_seconds() // 60)

    # Determine the corresponding row in the carbon intensity data
    carbon_time = (initial_datetime + datetime.timedelta(hours=elapsed_hours)).replace(tzinfo=utc)
    # if the carbon time is beyond the last time in the data, reset the ACTUAL_DATETIME (so that we loop back to the beginning of the data)
    if carbon_time > carbon_data.index[-1]:
        actual_datetime = current_datetime
        initial_datetime = carbon_data.index[0]
        user_registry[user_id] = initial_datetime, actual_datetime
        carbon_time = initial_datetime
        elapsed_hours = 0
    rounded_time = carbon_time.replace(minute=0, second=0, microsecond=0)  # Round down to the nearest hour
    future_time = rounded_time + datetime.timedelta(hours=48)
    # convert to iso format
    rounded_time = rounded_time.isoformat()
    future_time = future_time.isoformat()

    # Retrieve the intensity value
    # note that rounded_time is a datetime object so we can index the carbon_data DataFrame with it
    try:
        row = carbon_data.loc[rounded_time]
    except KeyError:
        print(f"Carbon intensity data not available for the requested time: {rounded_time}")
        return jsonify({"error": "Carbon intensity data not available for the requested time."}), 404
    carbon_intensity = row['carbon_intensity_avg']
    
    # Also retrieve the upper and lower bounds on future carbon intensities for up to 48 hours after the current (rounded) time
    future_carbon_intensity = carbon_data.loc[rounded_time:future_time]
    lower_bound = future_carbon_intensity['carbon_intensity_avg'].min()
    upper_bound = future_carbon_intensity['carbon_intensity_avg'].max()

    return jsonify({"timestamp": rounded_time, "carbon_intensity": carbon_intensity, "upper_bound": upper_bound, "lower_bound": lower_bound}), 200

if __name__ == "__main__":
    # run the server on port 6066
    app.run(port=6066, debug=True)