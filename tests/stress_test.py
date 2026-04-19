import asyncio
import time
import httpx

URL = "http://127.0.0.1:8000/predict"

payload = {
    "text": "Earthquake hits city causing building collapse"
}

num_requests = 100
concurrency_limit = 20

async def fetch(client, i):
    try:
        response = await client.post(URL, json=payload)
        if response.status_code != 200:
            print(f"Request {i} failed: Status {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Request {i} failed: {repr(e)}")
        return False

async def main():
    print("Sending warmup request to initialize server models...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            await client.post(URL, json=payload)
            print("Warmup successful!")
        except Exception as e:
            print(f"Warmup failed: {repr(e)}")

    print(f"Starting async stress test with {num_requests} requests (Concurrency: {concurrency_limit})...")
    
    limits = httpx.Limits(max_connections=concurrency_limit)
    async with httpx.AsyncClient(limits=limits, timeout=60.0) as client:
        start_time = time.time()
        
        # Create tasks
        tasks = [fetch(client, i) for i in range(num_requests)]
        
        # Run concurrently
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        
        successful = sum(results)
        failed = num_requests - successful
        
        total_time = end_time - start_time
        avg_latency = total_time / num_requests if num_requests > 0 else 0
        throughput = successful / total_time if total_time > 0 else 0
        
        print("\n===== Async Stress Test Results =====")
        print(f"Total Requests   : {num_requests}")
        print(f"Successful       : {successful}")
        print(f"Failed           : {failed}")
        print(f"Total Time       : {total_time:.4f} seconds")
        print(f"Average Latency  : {avg_latency:.4f} seconds")
        print(f"Throughput       : {throughput:.2f} req/sec")

if __name__ == "__main__":
    asyncio.run(main())