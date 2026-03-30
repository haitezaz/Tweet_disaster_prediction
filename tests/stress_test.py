import time
import requests

URL = "http://127.0.0.1:8000/predict"

payload = {
    "text": "Earthquake hits city causing building collapse"
}

num_requests = 100

print("Starting stress test...")

start_time = time.time()

for i in range(num_requests):
    response = requests.post(URL, json=payload)

    if response.status_code != 200:
        print(f"Error at request {i}: {response.text}")

end_time = time.time()

total_time = end_time - start_time
avg_latency = total_time / num_requests

print("\n===== Stress Test Results =====")
print(f"Total Requests   : {num_requests}")
print(f"Total Time       : {total_time:.4f} seconds")
print(f"Average Latency  : {avg_latency:.4f} seconds")
print(f"Throughput       : {num_requests / total_time:.2f} req/sec")