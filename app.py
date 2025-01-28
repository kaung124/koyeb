from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# File to store the data
DATA_FILE = "datas.txt"

@app.route('/send_data', methods=['POST'])
def send_data():
    try:
        # Get JSON body from the request
        data = request.get_json()

        # Validate required fields
        required_fields = ['phNo', 'token', 'accId']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Extract data
        phNo = data['phNo']
        token = data['token']
        accId = data['accId']

        # Format data with quotes
        formatted_data = json.dumps({"phNo": phNo, "token": token, "accId": accId})

        # Check if the file exists
        if os.path.exists(DATA_FILE):
            # Read the existing data from the file
            with open(DATA_FILE, 'r') as file:
                existing_data = file.read().strip()

            # If there is existing data, prepend new data with a comma
            if existing_data:
                formatted_data = formatted_data + "," + existing_data
        else:
            existing_data = ""

        # Write the new content back to the file
        with open(DATA_FILE, 'w') as file:
            file.write(formatted_data)

        return jsonify({"message": "Data saved successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_data', methods=['GET'])
def get_data():
    try:
        # Read data from file
        with open(DATA_FILE, 'r') as file:
            raw_data = file.read().strip()

        # Parse the raw data into a list of dictionaries
        if raw_data:
            # Wrap the raw data with a list to form a valid JSON array
            records = f"[{raw_data}]"
            data_list = json.loads(records)  # Safely parse the data using JSON
        else:
            data_list = []

        # Return the parsed data list as JSON
        return jsonify(data_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run()
    