import asyncio
from api.database import FirebaseDataConnectClient

async def test_db() -> None:
    print("Testing Firebase Data Connect Client initialization...")
    client = FirebaseDataConnectClient()
    
    print(f"Project ID: {client.project_id}")
    print(f"Location: {client.location}")
    print(f"Service ID: {client.service_id}")
    print(f"Base URL: {client.base_url}")
    
    print("Attempting to generate auth token...")
    token = await client.get_auth_token()
    if token:
        print("Auth token generated successfully (length: {})".format(len(token)))
    else:
        print("No auth token generated. This is expected if GOOGLE_APPLICATION_CREDENTIALS is not set.")
    
    await client.close()
    print("Test finished.")

if __name__ == "__main__":
    asyncio.run(test_db())