import requests
import time
import json
from datetime import datetime

WORKER_NODES = {
    "69d27be66dfc8dac776fa9ce":"http://192.168.1.101:5000/sensors/fetch/latest",
    "69d27be66dfc8dac776fa9cf":"http://192.168.1.102:5000/sensors/fetch/latest",
    "69d27be66dfc8dac776fa9d0":"http://192.168.1.103:5000/sensors/fetch/latest",
}

CLOUD_URL = "https://your-cloud-api.com/ingest"
def run_fog_aggregator():
    print("Fog Processor started. Syncing every 60 seconds...")
    while True:
        master_payload = {
            "fog_dispatch_time": datetime.now().isoformat(),
            "sections": [] 
        }
        for section_id, url in WORKER_NODES.items():
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Inject the hardcoded Section ID into the record
                    data["section_id"] = section_id
                    data["remainingShelfLife"] = 5
                    data["gasStage"]= "ripe"
                    data["gasConfidence"] = 1
                    data["action"] = "TESTING"
                    
                    master_payload["sections"].append(data)
                    print(f"Successfully pulled {section_id}")
                else:
                    print(f"Warning: {section_id} returned status {response.status_code}")
            except Exception as e:
                print(f"Error reaching {section_id} ({url}): {e}")

        if master_payload["sections"]:
            try:
                res = requests.post(
                    CLOUD_URL, 
                    json=master_payload, 
                    timeout=30
                )
                print(f"Cloud Response: {res.status_code} - {res.text}")
            except Exception as e:
                print(f"Cloud connection failed: {e}")
        time.sleep(60)

if __name__ == "__main__":
    run_fog_aggregator()