from flask import Flask, jsonify
import json
import os
import requests
import threading
import time
import schedule

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


# API Endpoint
API_URL = "https://apis.mytel.com.mm/network-test/v3/submit"

# Mapping of operators to their request IDs
OPERATORS = {
    "ATOM": "12be4567-e89b-12d3-a456-426655444212",
    "MYTEL": "123e4567-e89b-12d3-a456-426655440000",
    "OOREDOO": "a21e4567-e89b-12d3-a456-a14132143535",
    "MPT": "12312567-e89b-12d3-a456-124324125ab1"
}

# Function to send request for each record and operator
def send_request(record, operator, request_id):
    try:
        headers = {
            "Authorization": f"Bearer {record['token']}"
        }
        body = {
            "cellId": "30816289",
            "deviceModel": "M2007J22C",
            "downloadSpeed": 40.2,
            "enb": "120376",
            "latency": 90.375,
            "latitude": "16.9264438",
            "location": "Mon, Myanmar",
            "longitude": "97.3599738",
            "msisdn": f"+95{record['phNo']}",
            "networkType": "_4G",
            "operator": operator,
            "requestId": request_id,
            "requestTime": "2025-01-20 07:40:24",
            "rsrp": "-111",
            "township": "Mon",
            "uploadSpeed": 62.0
        }
        
        print(f"Sending request for {record['phNo']} with operator: {operator}")
        print(f"Headers: {headers}")
        print(f"Body: {json.dumps(body, indent=4)}")

        response = requests.post(API_URL, headers=headers, json=body)
        response_data = response.json()

        print("Status Code:", response.status_code)
        print("Response Body:", json.dumps(response_data, indent=4))

        if response_data.get("message") == "SUCCESS":
            print(f"SUCCESS for {record['phNo']} on {operator}")
        else:
            print(f"Failed for {record['phNo']} on {operator}: {response_data}")

    except Exception as e:
        print(f"Error sending request for {record['phNo']} on {operator}: {e}")

# Auto send function
def auto_send():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as file:
                raw_data = file.read().strip()

            if raw_data:
                records = json.loads(f"[{raw_data}]")
                for record in records:
                    for operator, request_id in OPERATORS.items():
                        send_request(record, operator, request_id)
                        time.sleep(5)  # Delay between requests
            else:
                print("No data to send.")
        else:
            print(f"Data file {DATA_FILE} not found.")
    except Exception as e:
        print(f"Error in auto_send: {e}")

# Schedule the job for every day at 11 PM Myanmar Time
def schedule_daily_job():
    schedule.every().day.at("01:45").do(auto_send)
    print("Daily job scheduled for 11:33 PM Myanmar Time.")
    while True:
        schedule.run_pending()
        time.sleep(1)

# Flask route to confirm the schedule
@app.route('/start_schedule', methods=['POST'])
def start_schedule():
    try:
        return jsonify({"message": "Schedule is already running."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    threading.Thread(target=schedule_daily_job, daemon=True).start()
    print("Auto-schedule started.")
    app.run()
    

