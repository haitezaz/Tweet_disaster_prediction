from __future__ import annotations

import os
import json
import httpx
import google.auth
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleAuthRequest
from src.config import FIREBASE_PROJECT_ID, FIREBASE_LOCATION, DATA_CONNECT_SERVICE_ID, DATA_CONNECT_CONNECTOR_ID

class FirebaseDataConnectClient:
    def __init__(self):
        self.project_id = FIREBASE_PROJECT_ID
        self.location = FIREBASE_LOCATION
        self.service_id = DATA_CONNECT_SERVICE_ID
        self.connector_id = DATA_CONNECT_CONNECTOR_ID
        self.base_url = f"https://firebasedataconnect.googleapis.com/v1beta/projects/{self.project_id}/locations/{self.location}/services/{self.service_id}/connectors/{self.connector_id}"
        
        # Configure a larger connection pool and longer timeout for concurrency
        limits = httpx.Limits(max_keepalive_connections=500, max_connections=1000)
        timeout = httpx.Timeout(
            timeout=30.0,  # default timeout for all operations
            connect=10.0,  # connection establishment timeout
            read=20.0,     # reading response timeout
            write=10.0,    # writing request timeout
            pool=5.0       # acquiring connection from pool timeout
        )
        self.client = httpx.AsyncClient(limits=limits, timeout=timeout)
        
        self._credentials = None
        self._token = None
        self._token_expiry = 0

    async def get_auth_token(self) -> str:
        import time
        if self._token and time.time() < self._token_expiry:
            return self._token
            
        try:
            if not self._credentials:
                credentials_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
                if credentials_json:
                    info = json.loads(credentials_json)
                    self._credentials = service_account.Credentials.from_service_account_info(
                        info, scopes=["https://www.googleapis.com/auth/cloud-platform"]
                    )
                else:
                    self._credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            
            # Refresh is synchronous but now only called once every ~50 mins
            self._credentials.refresh(GoogleAuthRequest())
            self._token = self._credentials.token
            self._token_expiry = time.time() + 3000
            return self._token
        except Exception as e:
            print(f"Auth error: {e}. Returning empty token.")
            return ""

    async def execute_mutation(self, mutation_name: str, variables: dict) -> dict:
        url = f"{self.base_url}:executeMutation"
        token = await self.get_auth_token()
        headers = {
            "Content-Type": "application/json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        payload = {
            "operationName": mutation_name,
            "variables": variables
        }

        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        response_json = response.json()
        if "errors" in response_json:
            print(f"GraphQL Errors in {mutation_name}:", json.dumps(response_json["errors"], indent=2))
            
        return response_json

    async def execute_query(self, query_name: str, variables: dict) -> dict:
        url = f"{self.base_url}:executeQuery"
        token = await self.get_auth_token()
        headers = {
            "Content-Type": "application/json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        payload = {
            "operationName": query_name,
            "variables": variables
        }

        response = await self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        response_json = response.json()
        if "errors" in response_json:
            print(f"GraphQL Errors in {query_name}:", json.dumps(response_json["errors"], indent=2))
            
        return response_json

    async def close(self):
        await self.client.aclose()


# Global client instance
firebase_client = FirebaseDataConnectClient()

async def get_db() -> FirebaseDataConnectClient:
    return firebase_client

def init_db() -> None:
    pass