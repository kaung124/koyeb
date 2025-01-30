from flask import Flask, request, jsonify
import json
import os
import requests
import threading
import time

app = Flask(__name__)

# Files for data storage
DATA_FILE = "datas.txt"
STATUS_FILE = "status.txt"

API_URL = "https://apis.mytel.com.mm/network-test/v3/submit"

OPERATORS = {
    "ATOM": "12be4567-e89b-12d3-a456-426655444212",
    "MYTEL": "123e4567-e89b-12d3-a456-426655440000",
    "OOREDOO": "a21e4567-e89b-12d3-a456-a14132143535",
    "MPT": "12312567-e89b-12d3-a456-124324125ab1"
}

def update_status(total, success, fail):
    status_data = {"total": total, "success": success, "fail": fail}
    with open(STATUS_FILE, "w") as file:
        json.dump(status_data, file)

@app.route('/get_status', methods=['GET'])
def get_status():
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as file:
                status_data = json.load(file)
            return jsonify(status_data), 200
        else:
            return jsonify({"total": 0, "success": 0, "fail": 0}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send_data', methods=['POST'])
def send_data():
    try:
        data = request.get_json()
        required_fields = ['phNo', 'token', 'accId']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        phNo = data['phNo']
        token = data['token']
        accId = data['accId']

        formatted_data = json.dumps({"phNo": phNo, "token": token, "accId": accId})

        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as file:
                existing_data = file.read().strip()
            if existing_data:
                formatted_data = formatted_data + "," + existing_data
        else:
            existing_data = ""

        with open(DATA_FILE, 'w') as file:
            file.write(formatted_data)

        return jsonify({"message": "Data saved successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_data', methods=['GET'])
def get_data():
    try:
        with open(DATA_FILE, 'r') as file:
            raw_data = file.read().strip()

        if raw_data:
            records = f"[{raw_data}]"
            data_list = json.loads(records)
        else:
            data_list = []

        return jsonify(data_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def send_request(record, operator, request_id, status_counts):
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
        response = requests.post(API_URL, headers=headers, json=body)
        response_data = response.json()

        print("Status Code:", response.status_code)
        print("Response:", json.dumps(response_data, indent=4))

        status_counts["total"] += 1

        if response_data.get("message") == "SUCCESS":
            status_counts["success"] += 1
            print(f"SUCCESS for {record['phNo']} on {operator}")
        else:
            status_counts["fail"] += 1
            print(f"Failed for {record['phNo']} on {operator}: {response_data}")

    except Exception as e:
        status_counts["fail"] += 1
        print(f"Error sending request for {record['phNo']} on {operator}: {e}")

def auto_send():
    status_counts = {"total": 0, "success": 0, "fail": 0}

    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as file:
                raw_data = file.read().strip()

            if raw_data:
                records = json.loads(f"[{raw_data}]")
                for record in records:
                    for operator, request_id in OPERATORS.items():
                        send_request(record, operator, request_id, status_counts)
                        time.sleep(5)  # Delay between requests

                # Update status file after sending all requests
                update_status(status_counts["total"], status_counts["success"], status_counts["fail"])

            else:
                print("No data to send.")
        else:
            print(f"Data file {DATA_FILE} not found.")

    except Exception as e:
        print(f"Error in auto_send: {e}")

@app.route('/start_send', methods=['POST'])
def start_send():
    try:
        threading.Thread(target=auto_send, daemon=True).start()
        return jsonify({"message": "Auto-send started!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Server started.")
    app.run()
    
